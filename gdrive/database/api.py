"""
gdrive rest api
"""

import io
import json
import logging

import fastapi
from pydantic import BaseModel
from sqlalchemy import orm
from fastapi import BackgroundTasks, responses

from gdrive.database import database, crud, schemas

log = logging.getLogger(__name__)

router = fastapi.APIRouter()


def get_db():
    """
    get db connection
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        print("Closing DB")
        db.close()


@router.post("/test")
async def test(req: schemas.TestCreate, session: orm.Session = fastapi.Depends(get_db)):
    session = crud.create_test_content(session, req)
    return responses.JSONResponse(status_code=202, content="Done")
