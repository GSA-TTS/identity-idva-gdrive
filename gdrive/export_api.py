"""
gdrive rest api
"""

import io
import json
import logging

import fastapi
from pydantic import BaseModel, typing
from fastapi import Response, status, HTTPException
from googleapiclient.http import HttpError
from starlette.requests import Request

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
async def survey_upload_response(request: SurveyResponseModel):
    """
    Single endpoint to handle qualtrics response fetching and exporting
    """

    try:
        # call function that invokes qualtrics microservice to get response
        response = export_client.get_qualtrics_response(
            request.surveyId, request.responseId
        )

        # call function that queries ES for all analytics entries (flow interactionId) with responseId
        interactionIds = export_client.export_response(request.responseId, response)

        # export list of interactionIds to gdrive
        for id in interactionIds:
            upload_file(id)

        return response
    except error.ExportError as e:
        raise HTTPException(status_code=400, detail=e.args)
