"""
DB Connection for Gdrive
"""
import logging
import sqlalchemy
from sqlalchemy import orm, schema

from gdrive import settings

log = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(
    settings.URI, connect_args={"options": "-csearch_path=%s" % (settings.SCHEMA_NAME)}
)

print("Create engine successful")

if not engine.dialect.has_schema(engine, settings.SCHEMA_NAME):
    engine.execute(schema.CreateSchema(settings.SCHEMA_NAME))

print("Has schema successful")

SessionLocal = orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)


print("Session maker successful")
