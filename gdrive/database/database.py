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

if engine.dialect.has_schema(engine, settings.SCHEMA):
    print("------------------ WIP DROP gdrive ------------------")
    engine.execute(schema.DropSchema(settings.SCHEMA, cascade=True))

engine.execute(schema.CreateSchema(settings.SCHEMA))

SessionLocal = orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)
