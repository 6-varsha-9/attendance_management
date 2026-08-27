from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, RoleEnum
from app.schemas import StudentCreate, StudentOut
from app.deps import require_role

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/", response_model=StudentOut)
def create_student(student: StudentCreate, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN))):
    new_student = Student(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.get("/", response_model=list[StudentOut])
def get_students(db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN, RoleEnum.TEACHER, RoleEnum.PRINCIPAL))):
    return db.query(Student).all()

@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN, RoleEnum.TEACHER, RoleEnum.PRINCIPAL))):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, updated: StudentCreate, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN))):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for k, v in updated.dict().items():
        setattr(student, k, v)
    db.commit()
    return student

@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), user=Depends(require_role(RoleEnum.ADMIN))):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}