from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Attendance, RoleEnum
from app.schemas import AttendanceCreate, AttendanceOut
from app.deps import require_role

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/", response_model=AttendanceOut)
def mark_attendance(record: AttendanceCreate, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.TEACHER, RoleEnum.ADMIN))):
    exists = db.query(Attendance).filter(
        Attendance.student_id == record.student_id,
        Attendance.date == record.date
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")
    new_record = Attendance(**record.dict())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@router.get("/", response_model=list[AttendanceOut])
def get_attendance(db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.TEACHER, RoleEnum.ADMIN, RoleEnum.PRINCIPAL))):
    return db.query(Attendance).all()

@router.put("/{record_id}", response_model=AttendanceOut)
def update_attendance(record_id: int, updated: AttendanceCreate, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.TEACHER, RoleEnum.ADMIN))):
    record = db.query(Attendance).filter(Attendance.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for k, v in updated.dict().items():
        setattr(record, k, v)
    db.commit()
    return record