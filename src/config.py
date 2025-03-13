"""
配置模块，负责加载和管理配置信息
"""
import os
from pathlib import Path
import torch
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 创建必要的目录
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "bank_service_agent")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# Google API配置
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# 代理配置
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

# 模型配置
MODEL_NAME = "BAAI/bge-small-en"

# 设备配置
DEVICE = "cpu"
MODEL_KWARGS = {"device": DEVICE}
ENCODE_KWARGS = {"normalize_embeddings": True}

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# 缓存配置
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

# 配置日志
logger.add(
    LOGS_DIR / "app.log",
    rotation="500 MB",
    retention="10 days",
    level=LOG_LEVEL
)

def validate_config():
    """验证必要的配置是否存在"""
    # 基础服务配置验证
    required_vars = [
        ("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY),
        ("LANGCHAIN_API_KEY", LANGCHAIN_API_KEY),
        ("SECRET_KEY", SECRET_KEY),
    ]
    
    # Google API 配置验证
    google_vars = [
        ("GOOGLE_API_KEY", GOOGLE_API_KEY),
        ("GOOGLE_CSE_ID", GOOGLE_CSE_ID),
    ]
    
    # 代理配置验证
    proxy_vars = [
        ("PROXY_HOST", PROXY_HOST),
        ("PROXY_PORT", PROXY_PORT),
    ]
    
    # 检查基础配置
    missing_vars = [var for var, value in required_vars if not value]
    if missing_vars:
        logger.warning(f"缺少基础配置: {', '.join(missing_vars)}")
    
    # 检查 Google API 配置
    missing_google = [var for var, value in google_vars if not value]
    if missing_google:
        logger.warning(f"Google API 配置不完整: {', '.join(missing_google)}")
    
    # 检查代理配置
    missing_proxy = [var for var, value in proxy_vars if not value]
    if missing_proxy:
        logger.warning(f"代理配置不完整: {', '.join(missing_proxy)}")
    elif PROXY_HOST and PROXY_PORT:
        try:
            port = int(PROXY_PORT)
            if port <= 0 or port > 65535:
                logger.warning(f"代理端口无效: {PROXY_PORT}，端口范围应为 1-65535")
        except ValueError:
            logger.warning(f"代理端口格式错误: {PROXY_PORT}")
    
    # 返回验证结果
    return {
        "base_config": len(missing_vars) == 0,
        "google_api": len(missing_google) == 0,
        "proxy": len(missing_proxy) == 0
    }

# 验证配置
config_status = validate_config()

# 输出配置状态
logger.info("配置验证结果:")
logger.info(f"基础配置: {'✓' if config_status['base_config'] else '✗'}")
logger.info(f"Google API: {'✓' if config_status['google_api'] else '✗'}")
logger.info(f"代理配置: {'✓' if config_status['proxy'] else '✗'}") 