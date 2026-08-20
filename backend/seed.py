# -*- coding: utf-8 -*-
"""初始化演示数据（模拟真实分布，生成一批重点人员、走访与预警记录）"""
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Person, VisitRecord, AlertRecord

# 省份及近似省会坐标中心（用于地图打点）
DISTRICTS = {
    "北京市": (116.4074, 39.9042),
    "天津市": (117.1902, 39.1256),
    "河北省": (114.5149, 38.0428),
    "山西省": (112.5493, 37.8570),
    "内蒙古自治区": (111.6708, 40.8183),
    "辽宁省": (123.4315, 41.8057),
    "吉林省": (125.3245, 43.8868),
    "黑龙江省": (126.6424, 45.7570),
    "上海市": (121.4737, 31.2304),
    "江苏省": (118.7674, 32.0415),
    "浙江省": (120.1536, 30.2875),
    "安徽省": (117.2830, 31.8612),
    "福建省": (119.3062, 26.0753),
    "江西省": (115.8922, 28.6765),
    "山东省": (117.1201, 36.6512),
    "河南省": (113.6654, 34.7580),
    "湖北省": (114.2986, 30.5844),
    "湖南省": (112.9823, 28.1941),
    "广东省": (113.2806, 23.1252),
    "广西壮族自治区": (108.3200, 22.8240),
    "海南省": (110.3312, 20.0310),
    "重庆市": (106.5049, 29.5332),
    "四川省": (104.0657, 30.6595),
    "贵州省": (106.7135, 26.5783),
    "云南省": (102.7123, 25.0406),
    "西藏自治区": (91.1322, 29.6604),
    "陕西省": (108.9480, 34.2632),
    "甘肃省": (103.8236, 36.0580),
    "青海省": (101.7789, 36.6232),
    "宁夏回族自治区": (106.2782, 38.4664),
    "新疆维吾尔自治区": (87.6177, 43.7928),
}

CATEGORIES = ["涉稳人员", "涉毒人员", "肇事肇祸", "社区矫正", "重点信访", "刑满释放", "精神障碍", "涉邪教"]
RISK_LEVELS = ["高", "中", "低"]
STATUSES = ["在控", "待核查", "脱管", "在控就医"]
ALERT_TYPES = ["异动预警", "越界预警", "失控预警", "签到异常", "新增登记"]

SURNAMES = "王李张刘陈杨黄赵吴周徐孙马朱胡郭何林罗郑梁谢宋唐许韩冯邓曹彭"
GIVEN = "伟芳娜敏静丽强磊军洋勇艳杰娟涛明超秀兰霞平刚桂英"

MANAGERS = ["张警官", "李警官", "王警官", "赵警官", "刘警官", "陈警官", "网格员小林", "网格员小张", "网格员小王"]


def _rand_name():
    return random.choice(SURNAMES) + "".join(random.sample(GIVEN, 2))


def _gen_id_card():
    prefix = "1101" + str(random.randint(0, 9))
    body = "".join(str(random.randint(0, 9)) for _ in range(11))
    check = str(random.randint(0, 9))
    return prefix + body + check


def seed_demo(db: Session, count: int = 800, force: bool = False):
    if not force and db.query(Person).count() > 0:
        return 0

    now = datetime.now()
    created = []
    for i in range(count):
        district = random.choice(list(DISTRICTS.keys()))
        lng, lat = DISTRICTS[district]
        lng += random.uniform(-0.08, 0.08)
        lat += random.uniform(-0.06, 0.06)
        category = random.choice(CATEGORIES)
        if category in ("涉毒人员", "肇事肇祸", "涉邪教"):
            risk = random.choices(RISK_LEVELS, weights=[45, 40, 15])[0]
        else:
            risk = random.choices(RISK_LEVELS, weights=[10, 45, 45])[0]
        status = random.choices(STATUSES, weights=[78, 12, 6, 4])[0]
        created_dt = now - timedelta(days=random.randint(0, 1200))
        p = Person(
            name=_rand_name(), id_card=_gen_id_card(), gender=random.choice(["男", "男", "女"]),
            age=random.randint(18, 78),
            phone="13" + "".join(str(random.randint(0, 9)) for _ in range(9)),
            category=category, risk_level=risk, control_status=status, district=district,
            street=random.choice(["和平街道", "建国街道", "中山街道", "双井街道", "金台街道", "万柳街道"]),
            address=f"{district}{random.choice(['阳光小区', '幸福苑', '朝阳里', '润景花园'])}{random.randint(1, 60)}栋{random.randint(1, 30)}室",
            longitude=round(lng, 5), latitude=round(lat, 5),
            manager=random.choice(MANAGERS),
            notes=random.choice(["定期走访", "重点关注", "纳入台账", "按时签到", ""]),
            created_at=created_dt, updated_at=created_dt,
        )
        db.add(p)
        created.append(p)
    db.flush()

    for p in random.sample(created, min(300, count)):
        for _ in range(random.randint(1, 4)):
            db.add(VisitRecord(
                person_id=p.id,
                visit_date=now - timedelta(days=random.randint(0, 30)),
                content=random.choice(["入户走访，情况正常", "电话回访，情绪稳定", "实地核查，未见异常", "家属沟通，配合良好"]),
                manager=p.manager,
            ))

    for _ in range(random.randint(80, 130)):
        p = random.choice(created)
        level = random.choices(RISK_LEVELS, weights=[30, 45, 25])[0]
        db.add(AlertRecord(
            person_id=p.id,
            alert_type=random.choice(ALERT_TYPES),
            alert_level=level,
            content=random.choice([
                f"{p.name}发生越界行为，超出管控范围", f"{p.name}签到异常，请核实位置",
                f"{p.name}出现异动，建议走访", f"{p.name}失联超时，启动失联核查",
                f"{p.name}新增关联风险，请关注",
            ]),
            district=p.district,
            status=random.choices(["待处置", "已处置"], weights=[60, 40])[0],
            created_at=now - timedelta(minutes=random.randint(10, 60 * 24 * 7)),
        ))
    db.commit()
    return count
