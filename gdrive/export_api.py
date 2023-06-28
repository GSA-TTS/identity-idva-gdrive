"""
gdrive rest api
"""

import io
import json
import logging

import fastapi
from pydantic import BaseModel
from fastapi import BackgroundTasks, responses

from gdrive import export_client, client, settings, error

log = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.post("/export")
async def upload_file(interactionId):
    export_data = export_client.export(interactionId)
    export_bytes = io.BytesIO(
        export_client.codename(json.dumps(export_data, indent=2)).encode()
    )
    parent = client.create_folder(interactionId, settings.ROOT_DIRECTORY)
    client.upload_basic("analytics.json", parent, export_bytes)


class SurveyResponseModel(BaseModel):
    surveyId: str
    responseId: str


@router.post("/survey-export")
async def survey_upload_response(
    request: SurveyResponseModel, background_tasks: BackgroundTasks
):
    """
    Single endpoint that kicks off qualtrics response fetching and exporting
    """

    background_tasks.add_task(
        survey_upload_response_task, request.responseId, request.surveyId
    )

    return responses.JSONResponse(
        status_code=202, content=f"Response {request.responseId} is being processed."
    )


async def survey_upload_response_task(responseId, surveyId):
    """
    Background task that handles qualtrics response fetching and exporting
    """
    try:
        response = export_client.get_qualtrics_response(surveyId, responseId)

        # call function that queries ES for all analytics entries (flow interactionId) with responseId
        interactionIds = export_client.export_response(responseId, response)

        # export list of interactionIds to gdrive
        for id in interactionIds:
            await upload_file(id)
    except error.ExportError as e:
        log.error(e.args)
