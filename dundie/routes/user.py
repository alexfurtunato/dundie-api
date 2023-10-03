from typing import List

from fastapi import APIRouter, HTTPException, status, Body, BackgroundTasks
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from dundie.models.user import User, UserResponse, UserRequest, UserProfilePatchRequest, UserPasswordPatchRequest
from dundie.db import ActiveSession
from dundie.auth import AuthenticatedUser, AuthenticatedSuperUser, CanChangeUserPassword
from dundie.tasks.user import try_to_send_pwd_reset_email

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


@router.patch("/{username}/")
async def update_user(
    *,
    session: Session = ActiveSession,
    patch_data: UserProfilePatchRequest,
    current_user: User = AuthenticatedUser,
    username: str
) -> UserResponse:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id != current_user.id and not current_user.superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own profle")
    
    # Update
    user.avatar = patch_data.avatar
    user.bio = patch_data.bio

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/{username}/password/")
async def change_password(
    *,
    session: Session = ActiveSession,
    patch_data: UserPasswordPatchRequest,
    user: User = CanChangeUserPassword
) -> UserResponse:
    user.password = patch_data.hashed_password  
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/pwd_reset_token/")
async def send_password_reset_token(
    *, 
    email: str = Body(embed=True),
    background_tasks: BackgroundTasks):
    """Sends an email with the token to reset password."""
    background_tasks.add_task(
        try_to_send_pwd_reset_email, email=email
    )
    return {
        "message": "If we found a user with that email, we sent a password reset token to it."
    }