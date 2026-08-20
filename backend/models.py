# -*- coding: utf-8 -*-
"""ORM 数据模型"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Person(Base):
    """重点人员"""
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, index=True)
    id_card = Column(String(20), nullable=False, unique=True, index=True)
    gender = Column(String(10), default="男")
    age = Column(Integer, default=0)
    phone = Column(String(20), default="")
    category = Column(String(30), index=True)
    risk_level = Column(String(10), default="低", index=True)
    control_status = Column(String(20), default="在控", index=True)
    district = Column(String(50), index=True)
    street = Column(String(50), default="")
    address = Column(String(200), default="")
    longitude = Column(Float, default=0.0)
    latitude = Column(Float, default=0.0)
    manager = Column(String(50), default="")
    photo = Column(String(200), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    visits = relationship("VisitRecord", back_populates="person", cascade="all, delete-orphan")
    alerts = relationship("AlertRecord", back_populates="person", cascade="all, delete-orphan")


class VisitRecord(Base):
    """走访/处置记录"""
    __tablename__ = "visit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), index=True)
    visit_date = Column(DateTime, default=datetime.now, index=True)
    content = Column(Text, default="")
    manager = Column(String(50), default="")
    person = relationship("Person", back_populates="visits")


class AlertRecord(Base):
    """预警记录"""
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), index=True)
    alert_type = Column(String(30), default="异动预警")
    alert_level = Column(String(10), default="中", index=True)
    content = Column(Text, default="")
    district = Column(String(50), default="")
    status = Column(String(10), default="待处置")
    created_at = Column(DateTime, default=datetime.now, index=True)
    person = relationship("Person", back_populates="alerts")


class ImportLog(Base):
    """Excel 导入日志"""
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(200), default="")
    total = Column(Integer, default=0)
    success = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    errors = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class DBSettings(Base):
    """数据库连接配置（支持 MySQL）+ 自动更新开关"""
    __tablename__ = "db_settings"

    id = Column(Integer, primary_key=True)
    db_type = Column(String(10), default="sqlite")
    host = Column(String(100), default="127.0.0.1")
    port = Column(Integer, default=3306)
    database = Column(String(100), default="bigscreen")
    username = Column(String(100), default="root")
    password = Column(String(100), default="")
    auto_sync = Column(Boolean, default=False)
    sync_interval = Column(Integer, default=60)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
