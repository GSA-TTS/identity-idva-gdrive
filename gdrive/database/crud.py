from gdrive.database import database


def create_row(db_item):
    session = database.SessionLocal()
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    session.close()
    return db_item
