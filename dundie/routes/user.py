from typing import List

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from dundie.models.user import User, UserResponse, UserRequest
from dundie.db import ActiveSession

router = APIRouter()

@router.get("/")
async def list_users(*, session: Session = ActiveSession) -> List[UserResponse]:
    """List all users from database"""
    users = session.exec(select(User)).all()
    return users


@router.get("/{username}/")
async def get_user_by_username(
    *, session: Session = ActiveSession, username: str
) -> UserResponse:
    """Get user by username"""
    query = select(User).where(User.username == username)
    user = session.exec(query).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", status_code=201)
async def create_user(
    *, session: Session = ActiveSession, user: UserRequest
) -> UserResponse:
    """Creates new user"""
    db_user = User.from_orm(user)  # transform UserRequest in User
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user