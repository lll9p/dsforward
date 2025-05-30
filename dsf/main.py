"""
启动AI API代理服务器
"""

import argparse
import logging
import os
import sys

import uvicorn  # type: ignore

from .proxy import create_app

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI API转发代理服务器")
    parser.add_argument(
        "--target-url",
        type=str,
        default=None,
        help="目标API的基础URL (默认: 从环境变量TARGET_API_URL获取，或使用 https://api.deepseek.com/v1)",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用自动重载 (开发模式)")
    parser.add_argument(
        "--log-level", type=str, default="info", choices=["debug", "info", "warning", "error"], help="日志级别"
    )

    args = parser.parse_args()

    # 设置日志级别
    log_level = getattr(logging, args.log_level.upper())
    logging.getLogger().setLevel(log_level)

    # 设置目标URL
    target_url = args.target_url or os.getenv("TARGET_API_URL", "https://api.deepseek.com/v1")

    logger.info("启动AI API代理服务器...")
    logger.info(f"监听地址: {args.host}:{args.port}")
    logger.info(f"目标API: {target_url}")
    logger.info(f"代理地址: http://{args.host}:{args.port}")
    logger.info(f"健康检查: http://{args.host}:{args.port}/health")
    logger.info("-" * 50)

    # 设置环境变量供应用使用
    os.environ["TARGET_API_URL"] = target_url

    # 启动服务器
    try:
        if args.reload:
            # 开发模式：使用字符串导入，支持热重载
            logger.warning("开发模式启动，启用热重载")
            uvicorn.run(
                "dsf.proxy:create_app",
                factory=True,
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level=args.log_level,
            )
        else:
            # 生产模式：直接使用应用实例
            logger.info("生产模式启动")
            app = create_app(target_url)
            uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    except KeyboardInterrupt:
        logger.info("收到中断信号，服务器正在停止...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
