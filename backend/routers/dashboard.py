# -*- coding: utf-8 -*-
"""大屏数据聚合 API（支持省份/类别/状态过滤，用于钻取与图表联动）"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Person, AlertRecord, VisitRecord

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _filtered(db, district=None, category=None, status=None, risk=None):
    q = db.query(Person)
    if district:
        q = q.filter(Person.district == district)
    if category:
        q = q.filter(Person.category == category)
    if status:
        q = q.filter(Person.control_status == status)
    if risk:
        q = q.filter(Person.risk_level == risk)
    return q


@router.get("/summary")
def dashboard_summary(district: str = "", category: str = "", status: str = "", risk: str = "", alert_type: str = "", db: Session = Depends(get_db)):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    base = _filtered(db, district, category, status, risk)
    total = base.count()
    high_risk = base.filter(Person.risk_level.in_(["高"])).count()
    today_new = base.filter(Person.created_at >= today_start).count()
    yesterday_new = base.filter(Person.created_at >= yesterday_start, Person.created_at < today_start).count()
    control = base.filter(Person.control_status == "在控").count()
    control_rate = round(control / total * 100, 1) if total else 0.0
    mid_risk = base.filter(Person.risk_level == "中").count()
    low_risk = base.filter(Person.risk_level == "低").count()

    alert_q = db.query(AlertRecord)
    visit_q = db.query(VisitRecord)
    if district or category or status or risk:
        ids = [pid for (pid,) in base.with_entities(Person.id).all()]
        alert_q = alert_q.filter(AlertRecord.person_id.in_(ids)) if ids else alert_q.filter(AlertRecord.id < 0)
        visit_q = visit_q.filter(VisitRecord.person_id.in_(ids)) if ids else visit_q.filter(VisitRecord.id < 0)
    if alert_type:
        alert_q = alert_q.filter(AlertRecord.alert_type == alert_type)

    pending_alerts = alert_q.filter(AlertRecord.status == "待处置").count()
    today_visits = visit_q.filter(VisitRecord.visit_date >= today_start).count()
    today_alerts = alert_q.filter(AlertRecord.created_at >= today_start).count()
    yesterday_alerts = alert_q.filter(AlertRecord.created_at >= yesterday_start, AlertRecord.created_at < today_start).count()

    category_data = [{"name": c or "未知", "value": n} for c, n in base.with_entities(Person.category, func.count(Person.id)).group_by(Person.category).all()]
    if district:
        district_data = [{"name": d or "未知", "value": n} for d, n in base.with_entities(Person.street, func.count(Person.id)).group_by(Person.street).all()]
    else:
        district_data = [{"name": d or "未知", "value": n} for d, n in base.with_entities(Person.district, func.count(Person.id)).group_by(Person.district).all()]
    status_data = [{"name": s or "未知", "value": n} for s, n in base.with_entities(Person.control_status, func.count(Person.id)).group_by(Person.control_status).all()]
    risk_data = [{"name": "高", "value": high_risk}, {"name": "中", "value": mid_risk}, {"name": "低", "value": low_risk}]

    trend_days = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        trend_days.append({"date": day.strftime("%m-%d"), "新增": base.filter(Person.created_at >= ds, Person.created_at < de).count(), "处置": visit_q.filter(VisitRecord.visit_date >= ds, VisitRecord.visit_date < de).count()})

    alert_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        alert_trend.append({"date": day.strftime("%m-%d"), "预警": alert_q.filter(AlertRecord.created_at >= ds, AlertRecord.created_at < de).count()})

    monthly_trend = []
    for i in range(5, -1, -1):
        day = now.replace(day=1) - timedelta(days=i * 31)
        ms = day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if ms.month == 12:
            me = ms.replace(year=ms.year + 1, month=1)
        else:
            me = ms.replace(month=ms.month + 1)
        monthly_trend.append({"month": ms.strftime("%Y-%m"), "新增": base.filter(Person.created_at >= ms, Person.created_at < me).count()})

    alert_type_rows = alert_q.filter(AlertRecord.created_at >= (now - timedelta(days=30))).with_entities(AlertRecord.alert_type, func.count(AlertRecord.id)).group_by(AlertRecord.alert_type).all()
    alert_type_data = [{"name": t or "其他", "value": n} for t, n in alert_type_rows]

    alerts = alert_q.outerjoin(Person, AlertRecord.person_id == Person.id).order_by(AlertRecord.created_at.desc()).limit(8).all()
    alert_list = [{"id": a.id, "person_name": next((x for x in (db.query(Person.name).filter(Person.id == a.person_id).scalar(),)), "未知"), "alert_type": a.alert_type, "alert_level": a.alert_level, "content": a.content, "district": a.district, "status": a.status, "created_at": a.created_at} for a in alerts]
    recent_rows = visit_q.outerjoin(Person, VisitRecord.person_id == Person.id).order_by(VisitRecord.visit_date.desc()).limit(10).all()
    visit_list = [{"person_name": (db.query(Person.name).filter(Person.id == v.person_id).scalar()) or "未知", "district": (db.query(Person.district).filter(Person.id == v.person_id).scalar()) or "", "content": v.content, "manager": v.manager, "visit_date": v.visit_date} for v in recent_rows]

    return {
        "total": total, "high_risk": high_risk, "control_rate": control_rate, "pending_alerts": pending_alerts,
        "today_visits": today_visits, "today_new": today_new, "yesterday_new": yesterday_new,
        "today_alerts": today_alerts, "yesterday_alerts": yesterday_alerts,
        "mid_risk": mid_risk, "low_risk": low_risk,
        "category_data": category_data, "district_data": district_data, "status_data": status_data, "risk_data": risk_data,
        "trend_data": trend_days, "alert_trend": alert_trend, "alert_type_data": alert_type_data, "monthly_trend": monthly_trend,
        "alerts": alert_list, "recent_visits": visit_list,
        "filter": {"district": district, "category": category, "status": status, "risk": risk, "alert_type": alert_type},
    }


@router.get("/map")
def dashboard_map(district: str = "", category: str = "", status: str = "", risk: str = "", db: Session = Depends(get_db)):
    base = _filtered(db, district, category, status, risk)
    agg_col = Person.street if district else Person.district
    districts = {}
    for d, n in base.with_entities(agg_col, func.count(Person.id)).group_by(agg_col).all():
        districts[d] = n
    points = []
    for p in base.filter(Person.longitude != 0).limit(2000).all():
        points.append({"id": p.id, "name": p.name, "category": p.category, "risk_level": p.risk_level, "district": p.district, "longitude": p.longitude, "latitude": p.latitude})
    bounds = None
    if not district:
        lngs = [p["longitude"] for p in points if p["longitude"]]
        if lngs:
            bounds = {"maxLng": max(lngs), "minLng": min(lngs), "maxLat": max(p["latitude"] for p in points), "minLat": min(p["latitude"] for p in points)}
    return {"districts": districts, "points": points, "bounds": bounds}
