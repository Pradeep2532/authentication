from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import SignupSchema
from app.core.security import hash_password
from app.deps import admin_required

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# Get all users (with roles)
@router.get("/users")
def list_users(
    _: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "roles": [ur.role.name for ur in u.roles]
        }
        for u in users
    ]


# Admin add user (default role: user)
@router.post("/users")
def create_user(
    data: SignupSchema,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "User already exists")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # 🔑 assign default role = user
    user_role = db.query(Role).filter(Role.name == "user").first()
    if user_role:
        db.add(UserRole(user_id=user.id, role_id=user_role.id))
        db.commit()

    return {"message": "User created by admin"}


# Assign role to user
@router.post("/users/{user_id}/roles/{role_name}")
def assign_role(
    user_id: str,
    role_name: str,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.name == role_name).first()

    if not user or not role:
        raise HTTPException(404, "User or role not found")

    exists = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role.id
    ).first()

    if exists:
        raise HTTPException(400, "Role already assigned")

    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()

    return {"message": f"Role '{role_name}' assigned"}


# Remove role from user
@router.delete("/users/{user_id}/roles/{role_name}")
def remove_role(
    user_id: str,
    role_name: str,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.name == role_name).first()

    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role.id
    ).first()

    if not user_role:
        raise HTTPException(404, "Role not assigned")

    db.delete(user_role)
    db.commit()

    return {"message": f"Role '{role_name}' removed"}


# Admin delete user
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted"}
