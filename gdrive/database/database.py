"""
DB Connection for Gdrive
"""
import logging
import sqlalchemy
from sqlalchemy import orm, schema

from gdrive import settings

log = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(
    settings.DB_URI, connect_args={"options": "-csearch_path=%s" % (settings.SCHEMA)}
)

SessionLocal = orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)


def db_ready():
    return engine.dialect.has_schema(engine, settings.SCHEMA)
