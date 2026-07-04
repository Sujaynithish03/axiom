from sqlmodel import SQLModel, Session, create_engine
from config import settings

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db():
    import models  # noqa: F401 - register tables
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
