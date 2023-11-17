"""
DB Connection for Gdrive
"""
import logging
import sqlalchemy
from sqlalchemy import orm

from gdrive import settings
from gdrive.database import models

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

engine = None
if settings.DB_URI:
    engine = sqlalchemy.create_engine(
        settings.DB_URI,
        connect_args={"options": "-csearch_path=%s" % (settings.SCHEMA)},
    )
else:
    log.info("No database configuration found. Creating in memory DB.")
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)


SessionLocal = orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)
