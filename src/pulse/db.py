from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pulse.models import Base
from pulse.settings import Settings, get_settings


def make_engine(settings: Settings | None = None):
    settings = settings or get_settings()
    url = settings.database_url
    kwargs: dict = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def init_db(settings: Settings | None = None):
    settings = settings or get_settings()
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    settings.outbound_dir.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
        from pathlib import Path

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(settings)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def session_scope(settings: Settings | None = None) -> Iterator[Session]:
    engine = make_engine(settings)
    Factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
