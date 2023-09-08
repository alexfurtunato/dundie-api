from typing import Optional
from sqlmodel import SQLModel, Field
from dundie.security import HashedPassword


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

    @property
    def superuser(self):
        """Users belonging to management dept are admins"""
        return self.dept == "management"

def generate_username(name: str) -> str:
    """Generates a slug username from a name"""
    return name.lower().replace(" ", "-")