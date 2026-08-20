# -*- coding: utf-8 -*-
"""数据库连接配置 + 自动更新设置"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database
from config import save_db_config
from database import get_db, init_db
from models import DBSettings, Person, VisitRecord, AlertRecord, ImportLog
from schemas import DBSettingsOut, DBSettingsUpdate
from seed import seed_demo
from sync_service import build_mysql_url, ensure_mysql_database

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session) -> DBSettings:
    s = db.query(DBSettings).first()
    if not s:
        s = DBSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/db", response_model=DBSettingsOut)
def get_settings(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("/db", response_model=DBSettingsOut)
def update_settings(data: DBSettingsUpdate, db: Session = Depends(get_db)):
    s = _get_or_create(db)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def _persist_mysql(cfg: dict):
    save_db_config(cfg)
    tmp = DBSettings(**cfg)
    ensure_mysql_database(tmp)


@router.post("/db/test")
def test_connection(db: Session = Depends(get_db)):
    s = _get_or_create(db)
    if s.db_type == "mysql":
        cfg = {"db_type": "mysql", "host": s.host, "port": s.port, "database": s.database, "username": s.username, "password": s.password}
        try:
            _persist_mysql(cfg)
            init_db(build_mysql_url(s))
        except Exception as e:
            raise HTTPException(400, f"连接失败：{e}")
    else:
        save_db_config({"db_type": "sqlite"})
        init_db()
    return {"ok": True, "message": "连接成功", "url": str(database.get_db_url())}


@router.post("/reseed")
def reseed(count: int = 5000, db: Session = Depends(get_db)):
    try:
        db.query(ImportLog).delete()
        db.query(AlertRecord).delete()
        db.query(VisitRecord).delete()
        db.query(Person).delete()
        db.commit()
        n = seed_demo(db, count=count, force=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"重建失败：{e}")
    return {"ok": True, "persons": n, "message": "已重新生成模拟数据"}


@router.post("/drop")
def drop_data(db: Session = Depends(get_db)):
    db.query(ImportLog).delete()
    db.query(AlertRecord).delete()
    db.query(VisitRecord).delete()
    db.query(Person).delete()
    db.commit()
    return {"ok": True, "message": "已清空数据"}
