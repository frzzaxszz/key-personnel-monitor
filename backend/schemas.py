# -*- coding: utf-8 -*-
"""Pydantic Schemas"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class PersonBase(BaseModel):
    name: str
    id_card: str
    gender: str = "男"
    age: Optional[int] = 0
    phone: str = ""
    category: str = "涉稳人员"
    risk_level: str = "低"
    control_status: str = "在控"
    district: str = ""
    street: str = ""
    address: str = ""
    longitude: Optional[float] = 0.0
    latitude: Optional[float] = 0.0
    manager: str = ""
    notes: str = ""


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    id_card: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    control_status: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    manager: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None


class PersonOut(PersonBase):
    id: int
    photo: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VisitOut(BaseModel):
    id: int
    person_id: int
    visit_date: datetime
    content: str
    manager: str

    class Config:
        from_attributes = True


class VisitCreate(BaseModel):
    person_id: int
    content: str = ""
    manager: str = ""
    visit_date: Optional[datetime] = None


class DBSettingsOut(BaseModel):
    id: int
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    auto_sync: bool
    sync_interval: int

    class Config:
        from_attributes = True


class DBSettingsUpdate(BaseModel):
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_interval: Optional[int] = None
