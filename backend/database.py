# -*- coding: utf-8 -*-
"""SQLAlchemy 引擎与会话管理，支持运行时切换 MySQL/SQLite"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import effective_default_url

Base = declarative_base()

_engine = None
_SessionLocal = None


def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def init_db(url: str = None):
    """初始化全局引擎。首次调用或传入不同 url 时重建。"""
    global _engine, _SessionLocal
    target = url or effective_default_url()
    if _engine is None or str(_engine.url) != target:
        _engine = _make_engine(target)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    import models  # noqa
    Base.metadata.create_all(_engine)


def get_db_url():
    return _engine.url if _engine else effective_default_url()


def get_db():
    if _SessionLocal is None:
        init_db()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
