# backend/reset_alembic.py
from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    print("✅ 成功：alembic_version 表已被强制清理！")
except Exception as e:
    print(f"❌ 发生错误：{e}")