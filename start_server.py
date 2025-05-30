#!/usr/bin/env python3
"""
启动服务器的简单脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from dsf.main import main

if __name__ == "__main__":
    main()
