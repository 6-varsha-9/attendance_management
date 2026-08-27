from pydantic import BaseModel

from datetime import date

from typing import Optional

from app.models import RoleEnum, StatusEnum, ReportStatusEnum


class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class StudentCreate(BaseModel):
    name: str
    roll_number: str
    email: str


class StudentOut(StudentCreate):
    id: int

    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: StatusEnum


class AttendanceOut(AttendanceCreate):
    id: int

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    student_id: int
    total_classes: int
    present: int
    absent: int
    percentage: float
    status: ReportStatusEnum
    approved_by: Optional[int] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class ReportReject(BaseModel):
    remarks: str