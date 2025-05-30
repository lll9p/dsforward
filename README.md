# DSF - AI API转发代理

一个高性能的FastAPI转发工具，用于修复AI模型API缺少`<think>`标签的问题。

## 功能特点

- **透明代理**: 完全透传所有HTTP请求和响应
- **自动修复**: 在第一个返回内容前自动添加`<think>`标签（如果缺失）
- **流式支持**: 优化的流式和非流式响应处理
- **高性能**: HTTP/2支持，连接池优化，异步处理
- **生产就绪**: 健康检查，日志记录，错误处理
- **Docker支持**: 完整的容器化部署方案
- **简单配置**: 环境变量和命令行参数配置

## 快速开始

### 方式1: 直接安装

```bash
pip install -e .
dsf --target-url https://api.deepseek.com/v1
```

### 方式2: Docker运行

```bash
# 构建镜像
docker build -t dsf-proxy .

# 运行容器
docker run -p 8000:8000 -e TARGET_API_URL=https://api.deepseek.com/v1 dsf-proxy
```

### 方式3: Docker Compose

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件设置你的配置
# 启动服务
docker-compose up -d
```

## 使用方法

### 命令行启动

```bash
# 使用默认设置（代理到 https://api.deepseek.com/v1）
dsf

# 指定目标API
dsf --target-url https://your-api-endpoint.com/v1

# 自定义端口和地址
dsf --host 0.0.0.0 --port 8080

# 设置日志级别
dsf --log-level debug

# 开发模式（自动重载）
dsf --reload
```

### 环境变量配置

```bash
export TARGET_API_URL=https://your-api-endpoint.com/v1
export LOG_LEVEL=info
dsf
```

### 程序化使用

```python
from dsf import create_app
import uvicorn

# 创建应用
app = create_app("https://your-api-endpoint.com/v1")

# 启动服务器
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 工作原理

1. **请求转发**: 接收所有HTTP请求，完整转发到目标API
2. **响应处理**:
   - 对于流式响应：检查第一个内容块，如果不以`<think>`开头则自动添加
   - 对于非流式响应：检查JSON内容，修复缺失的`<think>`标签
3. **透明代理**: 除了添加`<think>`标签外，所有其他内容保持不变

## 示例

启动代理服务器：

```bash
dsf --target-url https://api.deepseek.com/v1 --port 8000
```

然后将你的应用指向代理地址：

```text
http://localhost:8000/chat/completions
```

代理会自动转发到：

```text
https://api.deepseek.com/v1/chat/completions
```

并在响应中添加缺失的`<think>`标签。

## 健康检查

访问健康检查端点：

```bash
curl http://localhost:8000/health
```

## 配置参数

### 命令行参数

- `--target-url`: 目标API的基础URL
- `--host`: 监听地址（默认: 0.0.0.0）
- `--port`: 监听端口（默认: 8000）
- `--log-level`: 日志级别（debug, info, warning, error）
- `--reload`: 启用自动重载（开发模式）

### 环境变量

- `TARGET_API_URL`: 目标API的基础URL
- `HOST`: 监听地址
- `PORT`: 监听端口
- `LOG_LEVEL`: 日志级别
- `TIMEOUT`: 请求超时时间（秒）
- `MAX_CONNECTIONS`: 最大连接数
- `MAX_KEEPALIVE_CONNECTIONS`: 最大保持连接数
- `ENABLE_HTTP2`: 是否启用HTTP/2
- `VERIFY_SSL`: 是否验证SSL证书

## Docker部署

### 构建和运行

```bash
# 构建镜像
docker build -t dsf-proxy .

# 运行容器
docker run -d \
  --name dsf-proxy \
  -p 8000:8000 \
  -e TARGET_API_URL=https://api.deepseek.com \
  -e LOG_LEVEL=info \
  dsf-proxy
```

### 使用Docker Compose

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
vim .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 性能优化

- **HTTP/2支持**: 自动启用HTTP/2以提高性能
- **连接池**: 优化的连接池配置
- **异步处理**: 全异步架构，支持高并发
- **流式优化**: 使用`httpx.stream()`优化流式响应处理

## 故障排除

### 常见问题

1. **连接超时**: 检查目标API是否可访问，调整`TIMEOUT`设置
2. **SSL错误**: 设置`VERIFY_SSL=false`跳过SSL验证
3. **端口占用**: 更改`PORT`环境变量或使用`--port`参数

### 日志调试

```bash
# 启用调试日志
dsf --log-level debug

# 或设置环境变量
export LOG_LEVEL=debug
dsf
```

## 项目结构

```text
dsforward/
├── dsf/                    # 主要代码目录
│   ├── __init__.py        # 包初始化
│   ├── main.py            # 主入口点
│   ├── proxy.py           # 核心代理逻辑
│   └── config.py          # 配置管理
├── Dockerfile             # Docker镜像构建
├── docker-compose.yml     # Docker编排配置
├── requirements.txt       # Python依赖
├── pyproject.toml         # 项目配置
├── Makefile              # 构建和部署脚本
├── .env.example          # 环境变量模板
├── .dockerignore         # Docker忽略文件
├── README.md             # 项目说明
├── DEPLOYMENT.md         # 部署指南
├── CHANGELOG.md          # 更新日志
├── test_proxy.py         # 功能测试
├── benchmark.py          # 性能测试
└── start_server.py       # 简单启动脚本
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如果你觉得这个项目有用，请给它一个 ⭐️！
