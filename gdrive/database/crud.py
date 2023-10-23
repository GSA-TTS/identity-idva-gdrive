import sqlalchemy
from sqlalchemy import orm

from gdrive.database import database, models


def create_participant(db_item: models.ParticipantModel):
    session = database.SessionLocal()
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    session.close()
    return db_item
