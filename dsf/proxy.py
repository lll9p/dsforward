"""
AI API转发代理服务器
用于转发AI模型API请求和响应
"""

import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AIProxy:
    """AI API代理类，负责转发请求和响应"""

    def __init__(self, target_url: str):
        """
        初始化代理

        Args:
            target_url: 目标API的基础URL
        """
        self.target_url = target_url.rstrip("/")
        self.client = self._create_http_client()
        logger.info(f"AI代理初始化完成，目标URL: {self.target_url}")

    def _create_http_client(self) -> httpx.AsyncClient:
        """创建优化的HTTP客户端"""
        # 优化httpx客户端配置以提高流式性能
        try:
            # 尝试启用HTTP/2支持
            client = httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(300.0, connect=30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                http2=True,
            )
            logger.info("HTTP/2客户端创建成功")
            return client
        except ImportError:
            # 如果没有h2包，则使用HTTP/1.1
            client = httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(300.0, connect=30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
            logger.info("HTTP/1.1客户端创建成功")
            return client

    async def close(self) -> None:
        """关闭HTTP客户端"""
        await self.client.aclose()
        logger.info("HTTP客户端已关闭")

    async def forward_request(self, request: Request, path: str) -> Response:
        """
        转发请求到目标API

        Args:
            request: FastAPI请求对象
            path: 请求路径

        Returns:
            Response: 处理后的响应
        """
        # 构建目标URL
        target_url = f"{self.target_url}/{path.lstrip('/')}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        # 获取请求体
        body = await request.body()

        # 准备headers（排除host等）
        headers = self._prepare_headers(dict(request.headers))

        # 检查是否是流式请求
        is_stream_request = self._is_stream_request(body)

        logger.info(f"转发请求到: {target_url}, 流式: {is_stream_request}")

        try:
            # 根据是否是流式请求选择不同的处理方式
            if is_stream_request:
                return await self._handle_stream_request(target_url, request.method, headers, body)
            else:
                return await self._handle_non_stream_request(target_url, request.method, headers, body)
        except Exception as e:
            logger.error(f"请求转发失败: {e}")
            raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")

    def _prepare_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """准备转发的请求头"""
        # 移除可能导致问题的headers
        headers.pop("host", None)
        headers.pop("content-length", None)
        return headers

    def _is_stream_request(self, body: bytes) -> bool:
        """检查是否是流式请求"""
        try:
            if body:
                request_data = json.loads(body)
                stream_flag = request_data.get("stream", False)
                return stream_flag
        except json.JSONDecodeError:
            pass
        return False

    async def _handle_stream_request(
        self, target_url: str, method: str, headers: dict[str, str], body: bytes
    ) -> Response:
        """
        处理流式请求，使用client.stream()优化性能

        Args:
            target_url: 目标URL
            method: HTTP方法
            headers: 请求头
            body: 请求体

        Returns:
            StreamingResponse: 流式响应
        """

        async def stream_generator() -> AsyncGenerator[str]:
            try:
                async with self.client.stream(
                    method=method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    timeout=300,
                ) as response:
                    logger.info(f"收到流式响应，状态码: {response.status_code}")

                    # 错误处理
                    if response.status_code != 200:
                        error = await response.aread()
                        error_msg = error.decode() if error else "未知错误"
                        yield f"data: {json.dumps({'error': error_msg})}\n\n"
                        return

                    # 直接转发流式响应
                    async for line in response.aiter_lines():
                        # if not line.strip():
                        #     yield "\n"
                        #     continue

                        # 直接转发所有行
                        # if line.startswith("data: "):
                        #     yield f"{line}\n\n"
                        # else:
                        # 处理其他SSE字段（如event:, id:等）
                        # yield f"{line}\n"
                        yield line
            except Exception as e:
                logger.error(f"流式请求处理失败: {e}")
                yield f"data: {json.dumps({'error': f'流式请求失败: {str(e)}'})}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            },
        )

    async def _handle_non_stream_request(
        self, target_url: str, method: str, headers: dict[str, str], body: bytes
    ) -> Response:
        """
        处理非流式请求

        Args:
            target_url: 目标URL
            method: HTTP方法
            headers: 请求头
            body: 请求体

        Returns:
            Response: 处理后的响应
        """
        response = await self.client.request(
            method=method, url=target_url, headers=headers, content=body, follow_redirects=True
        )
        logger.info(f"收到非流式响应，状态码: {response.status_code}")
        return await self._handle_non_stream_response(response)

    async def _handle_non_stream_response(self, response: httpx.Response) -> Response:
        """处理非流式响应"""
        content = response.content
        headers = self._filter_response_headers(dict(response.headers))

        # 直接转发响应，不做任何修改
        return Response(content=content, status_code=response.status_code, headers=headers)

    def _filter_response_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """过滤响应头，避免与FastAPI自动添加的headers冲突，并保持原生API的header格式"""
        # 标准化header名称映射（保持与原生API一致的大小写）
        header_name_mapping = {
            "content-type": "Content-Type",
            "transfer-encoding": "Transfer-Encoding",
            "connection": "Connection",
            "cache-control": "Cache-Control",
            "x-oneapi-request-id": "X-Oneapi-Request-Id",
            "server": "Server",
            "date": "Date",
        }

        # 标准化所有headers，保持原生API的格式
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            # 使用标准化的header名称，如果没有映射则保持原样
            standard_key = header_name_mapping.get(key_lower, key)
            filtered[standard_key] = value

        return filtered


def create_app(target_url: str | None = None) -> FastAPI:
    """创建FastAPI应用"""
    if not target_url:
        target_url = os.getenv("TARGET_API_URL", "https://api.deepseek.com")

    # 创建代理实例
    proxy = AIProxy(target_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """应用生命周期管理"""
        # 启动
        logger.info("AI API代理服务启动")
        yield
        # 关闭
        await proxy.close()
        logger.info("AI API代理服务关闭")

    # 创建应用实例
    app = FastAPI(title="AI API Proxy", description="转发AI模型API请求和响应", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy"}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def proxy_request(request: Request, path: str):  # type: ignore
        """代理所有请求"""
        # 跳过健康检查路径
        if path == "health":
            return await health_check()
        return await proxy.forward_request(request, path)

    return app
