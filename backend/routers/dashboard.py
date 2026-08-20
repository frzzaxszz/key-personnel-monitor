# -*- coding: utf-8 -*-
"""大屏数据聚合 API（支持省份/类别/状态过滤，用于钻取与图表联动）"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Person, AlertRecord, VisitRecord

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _person_base(db: Session, district="", category="", status="", risk="",
                 month="", alert_type="", alert_date=None, date_from=None, date_to=None):
    """构造「最终过滤后的人员集合」：
    district/category/status/risk/month/date_from/date_to 直接过滤人员字段；
    alert_type / alert_date 则把人员范围限定为「拥有该类预警 / 该日预警」的人员，
    使得预警类型的点击也能联动人员类图表与地图。"""
    q = db.query(Person)
    if district:
        q = q.filter(Person.district == district)
    if category:
        q = q.filter(Person.category == category)
    if status:
        q = q.filter(Person.control_status == status)
    if risk:
        q = q.filter(Person.risk_level == risk)
    if date_from:
        q = q.filter(Person.created_at >= date_from)
    if date_to:
        # 含当天：date_to 结束时间取当日后一天零点
        day_end = datetime(date_to.year, date_to.month, date_to.day) + timedelta(days=1)
        q = q.filter(Person.created_at < day_end)
    if month:
        try:
            y, m = int(month[:4]), int(month[5:7])
            ms = datetime(y, m, 1)
            nxt = ms.replace(year=y + 1, month=1) if m == 12 else ms.replace(month=m + 1)
            q = q.filter(Person.created_at >= ms, Person.created_at < nxt)
        except (ValueError, IndexError):
            pass
    # 预警维度 -> 限定到拥有对应预警的人员
    if alert_type or alert_date:
        aq = db.query(AlertRecord.person_id).distinct()
        if alert_type:
            aq = aq.filter(AlertRecord.alert_type == alert_type)
        if alert_date:
            day = datetime(alert_date.year, alert_date.month, alert_date.day)
            aq = aq.filter(AlertRecord.created_at >= day,
                           AlertRecord.created_at < day + timedelta(days=1))
        pids = [pid for (pid,) in aq.all()]
        q = q.filter(Person.id.in_(pids)) if pids else q.filter(Person.id < 0)
    return q


def _person_filter_active(district="", category="", status="", risk="",
                          month="", alert_type="", alert_date=None, date_from=None, date_to=None):
    return bool(district or category or status or risk or month or alert_type or alert_date or date_from or date_to)


def _parse_date(s: str):
    """把 YYYY-MM-DD 字符串安全解析为 datetime，失败返回 None"""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


@router.get("/summary")
def dashboard_summary(
    district: str = "", category: str = "", status: str = "", risk: str = "",
    alert_type: str = "", month: str = "", alert_date: str = "",
    date_from: str = "", date_to: str = "",
    db: Session = Depends(get_db),
):
    """核心指标 + 各图表数据聚合（可按 district/category/status/risk/month/date_from/date_to 过滤人员；alert_type/alert_date 过滤预警并联动人员）"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 解析日期参数
    _alert_date = _parse_date(alert_date)
    _date_from = _parse_date(date_from)
    _date_to = _parse_date(date_to)

    base = _person_base(db, district, category, status, risk, month, alert_type, _alert_date, _date_from, _date_to)
    active = _person_filter_active(district, category, status, risk, month, alert_type, _alert_date, _date_from, _date_to)
    total = base.count()
    HIGH = ["高"]
    high_risk = base.filter(Person.risk_level.in_(HIGH)).count()
    today_new = base.filter(Person.created_at >= today_start).count()
    yesterday_new = base.filter(Person.created_at >= yesterday_start, Person.created_at < today_start).count()
    control = base.filter(Person.control_status == "在控").count()
    control_rate = round(control / total * 100, 1) if total else 0.0

    mid_risk = base.filter(Person.risk_level == "中").count()
    low_risk = base.filter(Person.risk_level == "低").count()

    # 预警与走访（有过滤时，限定到对应人员）
    alert_q = db.query(AlertRecord)
    visit_q = db.query(VisitRecord)
    if active:
        ids = [pid for (pid,) in base.with_entities(Person.id).all()]
        alert_q = alert_q.filter(AlertRecord.person_id.in_(ids)) if ids else alert_q.filter(AlertRecord.id < 0)
        visit_q = visit_q.filter(VisitRecord.person_id.in_(ids)) if ids else visit_q.filter(VisitRecord.id < 0)
    if alert_type:
        alert_q = alert_q.filter(AlertRecord.alert_type == alert_type)
    if _alert_date:
        alert_q = alert_q.filter(AlertRecord.created_at >= _alert_date,
                                 AlertRecord.created_at < _alert_date + timedelta(days=1))

    pending_alerts = alert_q.filter(AlertRecord.status == "待处置").count()
    today_visits = visit_q.filter(VisitRecord.visit_date >= today_start).count()
    today_alerts = alert_q.filter(AlertRecord.created_at >= today_start).count()
    yesterday_alerts = alert_q.filter(AlertRecord.created_at >= yesterday_start, AlertRecord.created_at < today_start).count()

    # 人员类别构成
    category_data = [{"name": c or "未知", "value": n} for c, n in base.with_entities(Person.category, func.count(Person.id)).group_by(Person.category).all()]

    # 区域分布：全国=>按省；已钻取省份=>按街道
    if district:
        district_data = [{"name": d or "未知", "value": n} for d, n in base.with_entities(Person.street, func.count(Person.id)).group_by(Person.street).all()]
    else:
        district_data = [{"name": d or "未知", "value": n} for d, n in base.with_entities(Person.district, func.count(Person.id)).group_by(Person.district).all()]

    # 管控状态
    status_rows = base.with_entities(Person.control_status, func.count(Person.id)).group_by(Person.control_status).all()
    status_data = [{"name": s or "未知", "value": n} for s, n in status_rows]

    # 风险等级
    risk_data = [
        {"name": "高", "value": high_risk},
        {"name": "中", "value": mid_risk},
        {"name": "低", "value": low_risk},
    ]

    # 近7日新增/处置趋势
    trend_days = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        add = base.filter(Person.created_at >= day_start, Person.created_at < day_end).count()
        visit = visit_q.filter(VisitRecord.visit_date >= day_start, VisitRecord.visit_date < day_end).count()
        trend_days.append({"date": day.strftime("%m-%d"), "新增": add, "处置": visit})

    # 近7日预警趋势
    alert_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        n = alert_q.filter(AlertRecord.created_at >= day_start, AlertRecord.created_at < day_end).count()
        alert_trend.append({"date": day.strftime("%m-%d"), "full_date": day.strftime("%Y-%m-%d"), "预警": n})

    # 最近6个月新增趋势（用于中间下方月度图）
    monthly_trend = []
    for i in range(5, -1, -1):
        day = (now.replace(day=1) - timedelta(days=i * 31))
        month_start = day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        n = base.filter(Person.created_at >= month_start, Person.created_at < month_end).count()
        monthly_trend.append({"month": month_start.strftime("%Y-%m"), "新增": n})

    # 预警类型分布（近30天）
    alert_type_rows = alert_q.filter(
        AlertRecord.created_at >= (now - timedelta(days=30))
    ).with_entities(AlertRecord.alert_type, func.count(AlertRecord.id)).group_by(AlertRecord.alert_type).all()
    alert_type_data = [{"name": t or "其他", "value": n} for t, n in alert_type_rows]

    # 最新预警
    alerts = (
        alert_q.outerjoin(Person, AlertRecord.person_id == Person.id)
        .order_by(AlertRecord.created_at.desc()).limit(8).all()
    )
    alert_list = [{
        "id": a.id, "person_id": a.person_id,
        "person_name": (db.query(Person.name).filter(Person.id == a.person_id).scalar()) or "未知",
        "alert_type": a.alert_type, "alert_level": a.alert_level, "content": a.content,
        "district": a.district, "status": a.status, "created_at": a.created_at,
    } for a in alerts]

    # 最新动态（走访）
    recent_rows = (
        visit_q.outerjoin(Person, VisitRecord.person_id == Person.id)
        .order_by(VisitRecord.visit_date.desc()).limit(10).all()
    )
    visit_list = [{
        "person_id": v.person_id,
        "person_name": (db.query(Person.name).filter(Person.id == v.person_id).scalar()) or "未知",
        "district": (db.query(Person.district).filter(Person.id == v.person_id).scalar()) or "",
        "content": v.content, "manager": v.manager, "visit_date": v.visit_date,
    } for v in recent_rows]

    return {
        "total": total, "high_risk": high_risk,
        "control_rate": control_rate, "pending_alerts": pending_alerts,
        "today_visits": today_visits, "today_new": today_new, "yesterday_new": yesterday_new,
        "today_alerts": today_alerts, "yesterday_alerts": yesterday_alerts,
        "mid_risk": mid_risk, "low_risk": low_risk,
        "category_data": category_data, "district_data": district_data,
        "status_data": status_data, "risk_data": risk_data,
        "trend_data": trend_days, "alert_trend": alert_trend,
        "alert_type_data": alert_type_data, "monthly_trend": monthly_trend,
        "alerts": alert_list, "recent_visits": visit_list,
        "filter": {"district": district, "category": category, "status": status, "risk": risk, "alert_type": alert_type, "month": month, "alert_date": alert_date, "date_from": date_from, "date_to": date_to},
    }


@router.get("/map")
def dashboard_map(
    district: str = "", category: str = "", status: str = "", risk: str = "",
    alert_type: str = "", month: str = "", alert_date: str = "",
    date_from: str = "", date_to: str = "",
    db: Session = Depends(get_db),
):
    """地图打点数据：按区域聚合 + 人员坐标（支持过滤与省份钻取、日期范围）"""
    _alert_date = _parse_date(alert_date)
    _date_from = _parse_date(date_from)
    _date_to = _parse_date(date_to)

    base = _person_base(db, district, category, status, risk, month, alert_type, _alert_date, _date_from, _date_to)

    agg_col = Person.street if district else Person.district
    districts = {}
    for d, n in base.with_entities(agg_col, func.count(Person.id)).group_by(agg_col).all():
        districts[d] = n

    points = []
    for p in base.filter(Person.longitude != 0).limit(2000).all():
        points.append({
            "id": p.id, "name": p.name, "category": p.category,
            "risk_level": p.risk_level, "district": p.district,
            "longitude": p.longitude, "latitude": p.latitude,
        })

    # 全国范围四至（用于钻取时聚焦）
    bounds = None
    if not district:
        lngs = [p["longitude"] for p in points if p["longitude"]]
        if lngs:
            bounds = {"maxLng": max(lngs), "minLng": min(lngs), "maxLat": max(p["latitude"] for p in points), "minLat": min(p["latitude"] for p in points)}
    return {"districts": districts, "points": points, "bounds": bounds}
