from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlmodel import Session, select, text
from sqlalchemy.orm import aliased

from dundie.models.user import User
from dundie.tasks.transaction import add_transaction, TransactionError, Transaction
from dundie.db import ActiveSession
from dundie.auth import AuthenticatedUser
from dundie.models.serializers import TransactionResponse

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()

@router.post("/{username}/", status_code=201)
async def create_transaction(
    *, 
    username: str,
    value: int = Body(embed=True),
    current_user: User = AuthenticatedUser,
    session: Session = ActiveSession
):
    """Adds a new transaction to a specified user"""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        add_transaction(user=user, from_user=current_user, value=value, session=session)
    except TransactionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return {"message": "Transaction added"}


@router.get("/", response_model=Page[TransactionResponse])
async def list_transactions(
    *,
    current_user: User = AuthenticatedUser,
    session: Session = ActiveSession,
    params: Params = Depends(),
    user: Optional[str] = None,
    from_user: Optional[str] = None,
    order_by: Optional[str] = None,   # &order_by=date ou &order_by=-date 
):
    """List all transactions"""
    query = select(Transaction)

    # Optional filters
    if user:
        query = query.join(
            User, Transaction.user_id == User.id
        ).where(User.username == user)
    if from_user:
        FromUser = aliased(User)  # aliased needed to desambiguous the join
        query = query.join(
            FromUser, Transaction.from_id == FromUser.id
        ).where(FromUser.username == from_user)

    # access filters
    if not current_user.superuser:
        query = query.where(
            (Transaction.user_id == current_user.id) | (Transaction.from_id == current_user.id)
        )

    if order_by:
        order_text = text(
            f"{order_by.replace('-', '')} {('desc' if '-' in order_by else 'asc')}" 
        )
        query = query.order_by(order_text)

    return paginate(query=query, session=session, params=params)
