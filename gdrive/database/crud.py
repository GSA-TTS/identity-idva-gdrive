import sqlalchemy
from sqlalchemy import orm

from gdrive.database import models, schemas


def create_test_content(session: orm.Session, content: schemas.TestCreate):
    db_item = models.TestModel(**content.dict())
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
