from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/protected",
    tags=["Protected"]
)

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "roles": [ur.role.name for ur in current_user.roles],
        "is_active": current_user.is_active
    }
