from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth, students, attendance, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Attendance Management System", version="1.0.0")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(reports.router)

@app.get("/")
def home():
    return {"message": "Attendance Management System API is running"}