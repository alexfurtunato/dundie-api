from sqlmodel import create_engine
from .config import settings

engine = create_engine(
    url=settings.db.uri,
    echo=settings.db.echo,
    connect_args=settings.db.connect_args,
)