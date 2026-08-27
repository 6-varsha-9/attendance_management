from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report, Attendance, StatusEnum, ReportStatusEnum, RoleEnum
from app.schemas import ReportOut, ReportReject
from app.deps import require_role, get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate/{student_id}", response_model=ReportOut)
def generate_report(student_id: int, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN, RoleEnum.TEACHER))):
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found")
    total = len(records)
    present = len([r for r in records if r.status == StatusEnum.PRESENT])
    absent = total - present
    percentage = round((present / total) * 100, 2)
    report = Report(
        student_id=student_id,
        generated_by=user.id,
        total_classes=total,
        present=present,
        absent=absent,
        percentage=percentage,
        status=ReportStatusEnum.PENDING
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/", response_model=list[ReportOut])
def get_reports(status: str = None, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN, RoleEnum.PRINCIPAL))):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.all()

@router.put("/{report_id}/approve", response_model=ReportOut)
def approve_report(report_id: int, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.PRINCIPAL))):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = ReportStatusEnum.APPROVED
    report.approved_by = user.id
    db.commit()
    return report

@router.put("/{report_id}/reject", response_model=ReportOut)
def reject_report(report_id: int, payload: ReportReject, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.PRINCIPAL))):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = ReportStatusEnum.REJECTED
    report.approved_by = user.id
    report.remarks = payload.remarks
    db.commit()
    return report