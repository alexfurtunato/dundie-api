from typing import Optional
from sqlmodel import Session, select
from dundie.db import engine
from dundie.models import User, Transaction, Balance


class TransactionError(Exception):
    """Can't add transaction"""


def add_transaction(
    *,
    user: User,
    from_user: User,
    value: int,
    session: Optional[Session] = None
):
    """Adds a new transaction to the specified user.
    
    params: 
        user: The user to add transaction to.
        from_user: The user where amount is coming from os superuser.
        value: The value being added
    """
    
    session = session or Session(engine)

    # TODO: Está dando erro quando usa o from_user pq a opracao com lay field diz q
    # o objeto está desconectado da sessão. O que não faz sentido.
    from_user = session.exec(select(User).where(User.id==from_user.id)).first()

    if not from_user.superuser and from_user.balance < value:
        raise TransactionError("Insufficient balance")
    
    transaction = Transaction(user=user, from_user=from_user, value=value)
    session.add(transaction)
    session.commit()  # HERE BE THE DRAGONS!!!
    session.refresh(user)
    session.refresh(from_user)

    for holder in (user, from_user):
        total_income = sum([t.value for t in holder.incomes])
        total_expense = sum([t.value for t in holder.expenses])
        balance = session.get(Balance, holder.id) or Balance(user=holder, value=0)
        balance.value = total_income - total_expense
        session.add(balance)

    session.commit()