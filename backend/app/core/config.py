import os

APP_NAME = os.getenv("APP_NAME", "shop_system")
APP_ENV = os.getenv("APP_ENV", "dev")  # dev / prod

# 默认：在 backend/ 下生成 shop.db（请务必在 backend/ 目录运行 alembic 与 uvicorn）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shop.db")

# 开发环境默认允许 Vite
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
