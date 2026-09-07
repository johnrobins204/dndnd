from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from dndnd.config import Settings, get_settings
from dndnd.models import Base


def create_database_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    settings.ensure_local_directories()
    engine = create_engine(settings.database_url)
    if settings.database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name == "sqlite":
        with engine.begin() as connection:
            columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(session_runs)")
            }
            if "character_id" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE session_runs ADD COLUMN character_id INTEGER "
                    "REFERENCES characters(id) ON DELETE SET NULL"
                )
            if "game_id" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE session_runs ADD COLUMN game_id INTEGER "
                    "REFERENCES games(id) ON DELETE SET NULL"
                )
            if "quest_id" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE session_runs ADD COLUMN quest_id INTEGER "
                    "REFERENCES quests(id) ON DELETE SET NULL"
                )
            game_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(games)")
            }
            if game_columns and "quest_id" not in game_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE games ADD COLUMN quest_id INTEGER "
                    "REFERENCES quests(id) ON DELETE SET NULL"
                )
            sheet_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(character_sheets)")
            }
            if sheet_columns and "ability_score_method" not in sheet_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE character_sheets "
                    "ADD COLUMN ability_score_method VARCHAR(60) DEFAULT ''"
                )
