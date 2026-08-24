# -*- coding: utf-8 -*-
"""数据库连接配置：默认 MySQL（持久化到 data/db_config.json，重启后保持），连接失败时回退 SQLite"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_CONFIG_FILE = os.path.join(DATA_DIR, "db_config.json")

# 默认连接串（SQLite），无 MySQL 配置时使用
DEFAULT_DB_URL = os.environ.get("DEFAULT_DB_URL", f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}")


def load_db_config() -> dict:
    """读取持久化的数据库连接配置；无则返回 None。"""
    try:
        with open(DB_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else None
    except Exception:
        return None


def save_db_config(cfg: dict):
    with open(DB_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def effective_default_url() -> str:
    """启动时使用的默认连接串：优先读持久化的 MySQL 配置。"""
    cfg = load_db_config()
    if cfg and cfg.get("db_type") == "mysql":
        try:
            return _build_mysql_url(cfg)
        except Exception:
            pass
    return DEFAULT_DB_URL


def _build_mysql_url(cfg: dict) -> str:
    user = cfg.get("username", "root")
    pwd = cfg.get("password", "")
    host = cfg.get("host", "127.0.0.1")
    port = cfg.get("port", 3306)
    dbname = cfg.get("database", "bigscreen")
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{dbname}?charset=utf8mb4"
