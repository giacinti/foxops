from fastapi import APIRouter, Security

from foxops.dependencies import get_current_user
from foxops.models import User

#: Holds the router for the user endpoint
router = APIRouter(prefix="/user", tags=["users"])


@router.get("/me", response_model=User)
def current_user(cur_user: User = Security(get_current_user)) -> User:
    """get current user"""
    return cur_user
