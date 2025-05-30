"""
配置管理模块
"""

import os
from typing import Optional


class Config:
    """应用配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.target_api_url = os.getenv("TARGET_API_URL", "https://api.deepseek.com/v1")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "info").lower()
        self.timeout = float(os.getenv("TIMEOUT", "300.0"))
        self.max_connections = int(os.getenv("MAX_CONNECTIONS", "100"))
        self.max_keepalive_connections = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
        self.enable_http2 = os.getenv("ENABLE_HTTP2", "true").lower() == "true"
        self.verify_ssl = os.getenv("VERIFY_SSL", "false").lower() == "true"
    
    def update_from_args(self, args) -> None:
        """从命令行参数更新配置"""
        if args.target_url:
            self.target_api_url = args.target_url
        if args.host:
            self.host = args.host
        if args.port:
            self.port = args.port
        if args.log_level:
            self.log_level = args.log_level
    
    def validate(self) -> None:
        """验证配置"""
        if not self.target_api_url:
            raise ValueError("TARGET_API_URL 不能为空")
        
        if not (1 <= self.port <= 65535):
            raise ValueError(f"端口号必须在1-65535之间，当前值: {self.port}")
        
        if self.log_level not in ["debug", "info", "warning", "error"]:
            raise ValueError(f"无效的日志级别: {self.log_level}")
        
        if self.timeout <= 0:
            raise ValueError(f"超时时间必须大于0，当前值: {self.timeout}")


# 全局配置实例
config = Config()
