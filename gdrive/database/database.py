"""
DB Connection for Gdrive
"""
import logging
import sqlalchemy
from sqlalchemy import orm, schema

from gdrive import settings

log = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(
    settings.URI, connect_args={"options": "-csearch_path=%s" % (settings.SCHEMA)}
)

if not engine.dialect.has_schema(engine, settings.SCHEMA):
    engine.execute(schema.CreateSchema(settings.SCHEMA))

SessionLocal = orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)
