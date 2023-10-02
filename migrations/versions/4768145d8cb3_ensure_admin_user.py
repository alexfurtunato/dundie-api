"""ensure_admin_user

Revision ID: 4768145d8cb3
Revises: 29c640b061ee
Create Date: 2023-10-01 23:39:56.163316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from dundie.models.user import User
from sqlmodel import Session


# revision identifiers, used by Alembic.
revision: str = '4768145d8cb3'
down_revision: Union[str, None] = '29c640b061ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    admin = User(
        name="Admin",
        username="admin",
        email="admin@admin.com",
        dept="management",
        password="admin", # ler de envvars/secrets - colocar password em settings ou envvars
        currency="USD"
    )

    try:
        session.add(admin)
        session.commit()
    except sa.exc.IntegrityError:
        session.rollback()


def downgrade() -> None:
    pass
