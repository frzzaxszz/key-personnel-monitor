# -*- coding: utf-8 -*-
"""FastAPI 入口"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database
from config import UPLOAD_DIR, load_db_config, save_db_config
from models import DBSettings
from routers import dashboard, persons, import_export, settings
from seed import seed_demo
from sync_service import simulate_realtime, build_mysql_url_from_dict, ensure_mysql_database

SEED_COUNT = 5000  # 生成的模拟重点人员数量


async def _realtime_loop():
    """自动更新后台任务：按配置间隔模拟实时动态"""
    while True:
        try:
            session_factory = database._SessionLocal
            if session_factory is not None:
                db = session_factory()
                try:
                    s = db.query(DBSettings).first()
                    interval = max((s.sync_interval if s and s.auto_sync else 0), 0)
                    if interval and s and s.auto_sync:
                        simulate_realtime(db, interval)
                finally:
                    db.close()
        except Exception:
            pass
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 若持久化配置指向 MySQL，则先确保数据库存在；否则回退 SQLite
    cfg = load_db_config()
    if cfg and cfg.get("db_type") == "mysql":
        tmp = DBSettings(**{k: cfg.get(k, "") for k in ("db_type", "host", "port", "database", "username", "password")})
        try:
            ensure_mysql_database(tmp)
            database.init_db(build_mysql_url_from_dict(cfg))
        except Exception as e:
            print("[启动] MySQL 连接失败，回退 SQLite：", e)
            database.init_db()
    else:
        database.init_db()

    db = next(database.get_db())
    try:
        seed_demo(db, count=SEED_COUNT)
    finally:
        db.close()
    task = asyncio.create_task(_realtime_loop())
    yield
    task.cancel()


app = FastAPI(title="重点人员综合管控平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(dashboard.router)
app.include_router(persons.router)
app.include_router(import_export.router)
app.include_router(settings.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
