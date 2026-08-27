from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RoleEnum
from app.schemas import UserCreate
from app.auth import hash_password
from app.deps import require_role


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    user=Depends(require_role(RoleEnum.ADMIN))
):
    return db.query(User).all()


@router.post("/")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(RoleEnum.ADMIN))
):
    existing_user = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    new_user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "username": new_user.username,
        "role": new_user.role
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(RoleEnum.ADMIN))
):
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if target_user.id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot delete their own account"
        )

    db.delete(target_user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }