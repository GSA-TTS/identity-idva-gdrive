import logging

import fastapi
from fastapi import responses
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from gdrive.database import database, models, crud

log = logging.getLogger(__name__)
router = fastapi.APIRouter()


class CreateResponseRequest(BaseModel):
    interactionId: str
    responseId: str
    sessionId: str
    surveyId: str
    dist: str


@router.post("/database")
async def database_info():
    if database.SessionLocal():
        log.info(database.engine)
        return responses.JSONResponse(
            status_code=202, content="Database connected as %s" % (database.engine.name)
        )

    return responses.JSONResponse(status_code=404, content="No database session found.")


@router.post("/database/response")
async def process_response_header(req: CreateResponseRequest):
    try:
        # Create new response record
        if database.SessionLocal():
            record = create_response(req)
            log.info("New response (interaction_id: %s)" % (record.interaction_id))
            return responses.JSONResponse(
                status_code=202, content="Successfully created new response record"
            )
    except SQLAlchemyError as sql_err:
        log.error(sql_err)
        return responses.JSONResponse(
            status_code=500, content="Error trying to complete response create"
        )

    return responses.JSONResponse(status_code=404, content="No database session found.")


def create_response(resp_req: CreateResponseRequest):
    return crud.create_response(
        models.ResponseModel(
            interaction_id=resp_req.interactionId,
            response_id=resp_req.responseId,
            session_id=resp_req.sessionId,
            survey_id=resp_req.surveyId,
            dist=resp_req.dist,
        )
    )
