# -*- coding: utf-8 -*-
"""重点人员 CRUD + 照片上传"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from config import UPLOAD_DIR
from database import get_db
from models import Person, VisitRecord
from schemas import PersonCreate, PersonUpdate, PersonOut, VisitCreate, VisitOut

router = APIRouter(prefix="/api/persons", tags=["persons"])


def _to_out(p: Person) -> dict:
    return PersonOut.model_validate(p).model_dump()


@router.get("")
def list_persons(q: str = "", category: str = "", risk_level: str = "", control_status: str = "", district: str = "", page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    query = db.query(Person)
    if q:
        like = f"%{q}%"
        query = query.filter(Person.name.like(like) | Person.id_card.like(like) | Person.phone.like(like))
    if category:
        query = query.filter(Person.category == category)
    if risk_level:
        query = query.filter(Person.risk_level == risk_level)
    if control_status:
        query = query.filter(Person.control_status == control_status)
    if district:
        query = query.filter(Person.district == district)
    total = query.count()
    items = query.order_by(Person.updated_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "items": [_to_out(p) for p in items]}


@router.get("/options")
def list_options(db: Session = Depends(get_db)):
    categories = ["涉稳人员", "涉毒人员", "肇事肇祸", "社区矫正", "重点信访", "刑满释放", "精神障碍", "涉邪教"]
    risk_levels = ["高", "中", "低"]
    control_statuses = ["在控", "待核查", "脱管", "在控就医"]
    districts = [r[0] for r in db.query(Person.district).distinct().order_by(Person.district).all()]
    return {"categories": categories, "risk_levels": risk_levels, "control_statuses": control_statuses, "districts": districts}


@router.post("", response_model=PersonOut)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    if db.query(Person).filter(Person.id_card == data.id_card).first():
        raise HTTPException(400, "该身份证号已存在")
    p = Person(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.get("/{person_id}", response_model=PersonOut)
def get_person(person_id: int, db: Session = Depends(get_db)):
    p = db.query(Person).filter(Person.id == person_id).first()
    if not p:
        raise HTTPException(404, "人员不存在")
    return _to_out(p)


@router.put("/{person_id}", response_model=PersonOut)
def update_person(person_id: int, data: PersonUpdate, db: Session = Depends(get_db)):
    p = db.query(Person).filter(Person.id == person_id).first()
    if not p:
        raise HTTPException(404, "人员不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db)):
    p = db.query(Person).filter(Person.id == person_id).first()
    if not p:
        raise HTTPException(404, "人员不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.post("/{person_id}/photo")
def upload_photo(person_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    p = db.query(Person).filter(Person.id == person_id).first()
    if not p:
        raise HTTPException(404, "人员不存在")
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    p.photo = f"/uploads/{fname}"
    db.commit()
    return {"photo": p.photo}


@router.get("/{person_id}/visits", response_model=list[VisitOut])
def list_visits(person_id: int, db: Session = Depends(get_db)):
    return db.query(VisitRecord).filter(VisitRecord.person_id == person_id).order_by(VisitRecord.visit_date.desc()).all()


@router.post("/{person_id}/visits", response_model=VisitOut)
def add_visit(person_id: int, data: VisitCreate, db: Session = Depends(get_db)):
    v = VisitRecord(person_id=person_id, content=data.content, manager=data.manager, visit_date=data.visit_date)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v
