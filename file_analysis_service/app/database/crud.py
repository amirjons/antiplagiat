from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.report import Report
from ..schemas.report import ReportCreate

def create_report(db: Session, report: ReportCreate) -> Report:
    db_report = Report(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).first()

def get_report_by_work_id(db: Session, work_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.work_id == work_id).first()

def get_reports_by_assignment(db: Session, assignment_id: str) -> List[Report]:
    return db.query(Report).filter(Report.assignment_id == assignment_id).order_by(Report.created_at).all()

def get_all_reports(db: Session, skip: int = 0, limit: int = 100) -> List[Report]:
    return db.query(Report).offset(skip).limit(limit).all()