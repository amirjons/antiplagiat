from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.work import Work
from ..schemas.work import WorkCreate

def create_work(db: Session, work: WorkCreate) -> Work:
    db_work = Work(**work.dict())
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work

def get_work_by_id(db: Session, work_id: int) -> Optional[Work]:
    return db.query(Work).filter(Work.id == work_id).first()

def get_work_by_hash(db: Session, file_hash: str) -> Optional[Work]:
    return db.query(Work).filter(Work.file_hash == file_hash).first()

def get_works_by_assignment(db: Session, assignment_id: str) -> List[Work]:
    return db.query(Work).filter(Work.assignment_id == assignment_id).order_by(Work.uploaded_at).all()

def get_all_works(db: Session, skip: int = 0, limit: int = 100) -> List[Work]:
    return db.query(Work).offset(skip).limit(limit).all()