from sqlmodel import Session, create_engine, SQLModel
from .config import settings
from fastapi import Depends

engine = create_engine(
    url=settings.db.uri,
    echo=settings.db.echo,
    connect_args=settings.db.connect_args,
)

def get_session():
    with Session(engine) as session:
        yield session

ActiveSession = Depends(get_session)