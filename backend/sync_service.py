# -*- coding: utf-8 -*-
"""自动更新服务：后台定时任务，模拟从外部数据库同步 / 生成实时动态与预警"""
import random
from datetime import datetime

from sqlalchemy.orm import Session

from models import Person, AlertRecord, VisitRecord, DBSettings

ALERT_TYPES = ["异动预警", "越界预警", "失控预警", "签到异常", "新增登记"]
DYNAMIC_TYPES = [
    ("人员新增", "完成重点人员登记，纳入管控台账"),
    ("走访处置", "完成入户走访，情况正常"),
    ("预警处置", "预警事件处置完毕，销号闭环"),
    ("数据同步", "外部数据库同步完成"),
]


def build_mysql_url(settings: DBSettings) -> str:
    return (f"mysql+pymysql://{settings.username}:{settings.password}"
            f"@{settings.host}:{settings.port}/{settings.database}?charset=utf8mb4")


def build_mysql_url_from_dict(cfg: dict) -> str:
    return (f"mysql+pymysql://{cfg.get('username', 'root')}:{cfg.get('password', '')}"
            f"@{cfg.get('host', '127.0.0.1')}:{cfg.get('port', 3306)}/{cfg.get('database', 'bigscreen')}?charset=utf8mb4")


def ensure_mysql_database(settings: DBSettings):
    import pymysql
    conn = pymysql.connect(
        host=settings.host, port=settings.port,
        user=settings.username, password=settings.password, connect_timeout=6,
    )
    try:
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % settings.database)
        conn.commit()
    finally:
        conn.close()


def simulate_realtime(db: Session, interval_seconds: int = 60):
    now = datetime.now()
    if now.second % max(interval_seconds, 10) > 3:
        return None
    people = db.query(Person).all()
    if not people:
        return None
    if random.random() < 0.45:
        p = random.choice(people)
        db.add(AlertRecord(
            person_id=p.id, alert_type=random.choice(ALERT_TYPES),
            alert_level=random.choice(["高", "中", "低"]),
            content=random.choice([
                f"{p.name}发生越界行为，超出管控范围", f"{p.name}签到异常，请核实位置",
                f"{p.name}出现异动，建议走访", f"{p.name}失联超时，启动失联核查",
            ]),
            district=p.district, status="待处置", created_at=now,
        ))
        db.commit()
        return {"type": "预警", "content": f"{p.name}新增预警", "time": now.strftime("%H:%M:%S")}
    else:
        p = random.choice(people)
        db.add(VisitRecord(
            person_id=p.id, visit_date=now,
            content=random.choice(["入户走访，情况正常", "电话回访，情绪稳定", "实地核查，未见异常"]),
            manager=p.manager,
        ))
        db.commit()
        return {"type": "动态", "content": f"{p.district} {p.name} 完成一次走访处置", "time": now.strftime("%H:%M:%S")}
