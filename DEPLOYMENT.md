# 部署指南

本文档介绍如何在不同环境中部署DSF AI API代理。

## 本地开发

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd dsforward

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

### 2. 启动开发服务器

```bash
# 使用默认配置
dsf

# 开发模式（自动重载）
dsf --reload --log-level debug

# 自定义配置
dsf --target-url https://api.deepseek.com/v1 --port 8080
```

## Docker部署

### 1. 构建镜像

```bash
docker build -t dsf-proxy .
```

### 2. 运行容器

```bash
# 基本运行
docker run -p 8000:8000 dsf-proxy

# 自定义配置
docker run -p 8000:8000 \
  -e TARGET_API_URL=https://api.deepseek.com/v1 \
  -e LOG_LEVEL=info \
  dsf-proxy

# 后台运行
docker run -d \
  --name dsf-proxy \
  --restart unless-stopped \
  -p 8000:8000 \
  -e TARGET_API_URL=https://api.deepseek.com/v1 \
  dsf-proxy
```

### 3. 查看日志

```bash
docker logs dsf-proxy
docker logs -f dsf-proxy  # 实时查看
```

## Docker Compose部署

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 2. 启动服务

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 生产环境部署

### 1. 使用反向代理

#### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式响应优化
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

#### Traefik配置示例

```yaml
version: '3.8'

services:
  dsf-proxy:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dsf.rule=Host(`your-domain.com`)"
      - "traefik.http.services.dsf.loadbalancer.server.port=8000"
    environment:
      - TARGET_API_URL=https://api.deepseek.com/v1
```

### 2. 环境变量配置

生产环境推荐的环境变量：

```bash
TARGET_API_URL=https://api.deepseek.com/v1
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
TIMEOUT=300.0
MAX_CONNECTIONS=100
MAX_KEEPALIVE_CONNECTIONS=20
ENABLE_HTTP2=true
VERIFY_SSL=true
```

### 3. 监控和健康检查

#### 健康检查端点

```bash
curl http://localhost:8000/health
```

#### 监控脚本示例

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

## 性能优化

### 1. 系统级优化

```bash
# 增加文件描述符限制
ulimit -n 65536

# 优化TCP设置
echo 'net.core.somaxconn = 65536' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65536' >> /etc/sysctl.conf
sysctl -p
```

### 2. 应用级优化

```bash
# 增加连接数
export MAX_CONNECTIONS=200
export MAX_KEEPALIVE_CONNECTIONS=50

# 启用HTTP/2
export ENABLE_HTTP2=true

# 调整超时时间
export TIMEOUT=600.0
```

### 3. 容器资源限制

```yaml
version: '3.8'

services:
  dsf-proxy:
    build: .
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

## 故障排除

### 1. 常见问题

#### 连接超时
- 检查目标API是否可访问
- 调整TIMEOUT设置
- 检查网络连接

#### 内存使用过高
- 减少MAX_CONNECTIONS
- 检查是否有内存泄漏
- 重启服务

#### SSL证书错误
- 设置VERIFY_SSL=false（仅测试环境）
- 更新证书
- 检查证书链

### 2. 日志分析

```bash
# 启用调试日志
export LOG_LEVEL=debug

# 查看详细日志
docker-compose logs -f dsf-proxy

# 过滤错误日志
docker-compose logs dsf-proxy | grep ERROR
```

### 3. 性能测试

```bash
# 运行性能测试
python benchmark.py

# 使用ab测试
ab -n 1000 -c 10 http://localhost:8000/health

# 使用wrk测试
wrk -t12 -c400 -d30s http://localhost:8000/health
```

## 安全建议

1. **网络安全**
   - 使用HTTPS
   - 配置防火墙
   - 限制访问IP

2. **容器安全**
   - 使用非root用户运行
   - 定期更新基础镜像
   - 扫描安全漏洞

3. **配置安全**
   - 不在代码中硬编码敏感信息
   - 使用环境变量或密钥管理
   - 定期轮换密钥

4. **监控和审计**
   - 启用访问日志
   - 监控异常请求
   - 设置告警机制
