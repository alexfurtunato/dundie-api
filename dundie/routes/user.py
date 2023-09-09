from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from dundie.models.user import User, UserResponse, UserRequest
from dundie.db import ActiveSession
from dundie.auth import AuthenticatedUser, AuthenticatedSuperUser

router = APIRouter()

@router.get("/", dependencies=[AuthenticatedUser])
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


@router.post("/", status_code=201, dependencies=[AuthenticatedSuperUser])
async def create_user(
    *, session: Session = ActiveSession, user: UserRequest
) -> UserResponse:
    """Creates new user"""
    # LBYL - Look at before you leap
    #        Olhe antes de saltar
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Username already taken"
                            )
    
    db_user = User.from_orm(user)  # transform UserRequest in User
    session.add(db_user)
    # EAFP - Easier ask for forgiveness than permission 
    #        Melhor pedir perdão que permissão
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integrityError"
        )
    session.refresh(db_user)
    return db_user