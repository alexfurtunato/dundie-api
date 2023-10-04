from pydantic import BaseModel, root_validator
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Session, select, Field, Relationship
from dundie.db import engine
from dundie.security import HashedPassword, get_password_hash
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from dundie.models.transaction import Transaction, Balance

class User(SQLModel, table=True):
    """ User model """

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(nullable=False)
    email: str = Field(nullable=None)
    password: HashedPassword
    name: str = Field(nullable=None)
    avatar: Optional[str] = None
    bio: Optional[str] = None
    dept: Optional[str] = Field(nullable=False)
    currency: Optional[str] = Field(nullable=False)

    incomes: Optional[list["Transaction"]] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"primaryjoin": 'User.id == Transaction.user_id'}
    )

    expenses: Optional[list["Transaction"]] = Relationship(
        back_populates="from_user",
        sa_relationship_kwargs={"primaryjoin": 'User.id == Transaction.from_id'}
    )

    _balance: Optional["Balance"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "dynamic"}
    )

    @property
    def balance(self) -> int:
        """Returns the current balance of the user"""
        if (user_balance := self._balance.first()) is not None:
            return user_balance.value
        return 0

    @property
    def superuser(self):
        """Users belonging to management dept are admins"""
        return self.dept == "management"


def generate_username(name: str) -> str:
    """Generates a slug username from a name"""
    return name.lower().replace(" ", "-")


def get_user(username: str) -> Optional[User]:
    query = select(User).where(User.username == username)
    with Session(engine) as session:
        return session.exec(query).first()


class UserResponse(BaseModel):
    """Serializer for User Response"""
    name: str
    username: str
    dept: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    currency: str


class UserResponseWithBalance(UserResponse):
    balance: Optional[int] =  None

    @root_validator(pre=True)
    def set_balance(cls, values):
        instance = values['_sa_instance_state'].object  # Instrospeccao do SQLAlchemy para evitar fazer nova query com session
        values['balance'] = instance.balance
        return values

class UserRequest(BaseModel):
    """Serializer for User request payload"""
    name: str
    email: str
    dept: str
    password: str
    currency: str = "USD"
    username: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None

    @root_validator(pre=True)
    def generate_username_if_not_set(cls, values):
        """Generates username if not set"""
        if values.get("username") is None:
            values["username"] = generate_username(values["name"])
        return values


class UserProfilePatchRequest(BaseModel):
    """Serializer for User Profile"""
    avatar: Optional[str] = None
    bio: Optional[str] = None


class UserPasswordPatchRequest(BaseModel):
    password: str
    password_confirm: str

    @root_validator(pre=True)
    def check_passwords_match(cls, values):
        """Checks if passwords match"""
        if values.get("password") != values.get("password_confirm"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        return values

    @property
    def hashed_password(self) -> str:
        """Returns hashed password"""
        return get_password_hash(self.password)