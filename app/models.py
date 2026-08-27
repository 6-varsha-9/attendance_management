from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PRINCIPAL = "PRINCIPAL"
    TEACHER = "TEACHER"

class StatusEnum(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"

class ReportStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(Enum(RoleEnum))

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    roll_number = Column(String, unique=True)
    email = Column(String, unique=True)
    attendance = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    status = Column(Enum(StatusEnum))
    student = relationship("Student", back_populates="attendance")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    generated_by = Column(Integer, ForeignKey("users.id"))
    total_classes = Column(Integer)
    present = Column(Integer)
    absent = Column(Integer)
    percentage = Column(Float)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(String, nullable=True)
    student = relationship("Student")