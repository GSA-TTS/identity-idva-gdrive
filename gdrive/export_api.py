"""
gdrive rest api
"""

import io
import json
import logging
import sys

import fastapi
from pydantic import BaseModel, Field
from fastapi import BackgroundTasks, responses

from gdrive import export_client, drive_client, sheets_client, settings, error
from gdrive.database import database, crud, models

log = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.post("/export")
async def upload_file(interactionId):
    log.info(f"Export interaction {interactionId}")
    export_data = export_client.export(interactionId)
    export_bytes = io.BytesIO(
        export_client.codename(json.dumps(export_data, indent=2)).encode()
    )
    parent = drive_client.create_folder(interactionId, settings.ROOT_DIRECTORY)
    drive_client.upload_basic("analytics.json", parent, export_bytes)
    log.info(f"Uploading {sys.getsizeof(export_bytes)} bytes to drive folder {parent}")


class ParticipantModel(BaseModel):
    first: str
    last: str
    email: str
    time: str
    date: str


class SurveyParticipantModel(BaseModel):
    """
    Request body format for the `/survey-response` endpoint
    """

    surveyId: str
    responseId: str
    participant: ParticipantModel | None = None


@router.post("/survey-export")
async def survey_upload_response(
    request: SurveyParticipantModel, background_tasks: BackgroundTasks
):
    """
    Single endpoint that kicks off qualtrics response fetching and exporting. Requests response data
    from the Qualtrix API and uploads contact and demographic data to the google drive. Does not upload
    responses without a complete status.
    """

    background_tasks.add_task(survey_upload_response_task, request)

    return responses.JSONResponse(
        status_code=202, content=f"Response {request.responseId} is being processed."
    )


async def survey_upload_response_task(request):
    """
    Background task that handles qualtrics response fetching and exporting
    """
    log.info(f"Gathering response {request.responseId}")
    try:
        response = export_client.get_qualtrics_response(
            request.surveyId, request.responseId
        )

        log.info(f"{request.responseId} response found, beginning export.")

        if response["status"] != "Complete":
            log.warn(
                f"Incomplete survery response to raw completions spreadsheet: {request.responseId}"
            )

        # By the time we get here, we can count on the response containing the demographic data
        # as it is included in the Completed flow responses. Responses without complete status
        # throws exception in get_qualtrics_response
        survey_resp = response["response"]

        if request.participant:
            participant = request.participant
            upload_result = sheets_client.upload_participant(
                participant.first,
                participant.last,
                participant.email,
                request.responseId,
                participant.time,
                participant.date,
                survey_resp["ethnicity"],
                ", ".join(
                    survey_resp["race"]
                ),  # Can have more than one value in a list
                survey_resp["gender"],
                survey_resp["age"],
                survey_resp["income"],
                survey_resp["skin_tone"],
            )

            result_sheet_id = upload_result["spreadsheetId"]
            if upload_result:
                log.info(
                    f"Uploaded response: {request.responseId} to completions spreadsheet {result_sheet_id}"
                )

            crud.create_participant(
                models.ParticipantModel(
                    survey_id=request.surveyId,
                    response_id=request.responseId,
                    rules_consent_id=survey_resp["rules_consent_id"],
                    time=participant.time,
                    date=participant.date,
                    ethnicity=survey_resp["ethnicity"],
                    race=", ".join(
                        survey_resp["race"]
                    ),  # Can have more than one value in a list
                    gender=survey_resp["gender"],
                    age=survey_resp["age"],
                    income=survey_resp["income"],
                    skin_tone=survey_resp["skin_tone"],
                )
            )
            log.info(f"Wrote {request.responseId} to database")

        # call function that queries ES for all analytics entries (flow interactionId) with responseId
        interactionIds = export_client.export_response(request.responseId, response)
        log.info(
            f"Elastic Search returned {len(interactionIds)} interaction ids for response: {request.responseId}"
        )

        # export list of interactionIds to gdrive
        for id in interactionIds:
            await upload_file(id)
            log.info(
                f"Exported response: {request.responseId} interaction: {id} to gdrive"
            )
    except error.ExportError as e:
        log.error(f"Response: {request.responseId} encountered an error: {e.args}")


class FindModel(BaseModel):
    """
    Request body format for the `/find` endpoint
    """

    responseId: str | list[str]
    field: str
    values: list[str] = Field(..., min_items=1)
    result_field: str | None = None


@router.post("/find")
async def find(find: FindModel):
    # for given responseid, find all occurences of
    result = find.result_field if find.result_field is not None else find.field
    responseId = (
        find.responseId if isinstance(find.responseId, list) else [find.responseId]
    )
    export_data = export_client.find(responseId, find.field, find.values, result)
    return export_data


# ------------------------------- Archive API --------------------------------------
class InteractionModel(BaseModel):
    interactionId: str


@router.post("/export/interaction-files")
async def get_files_by_id(request: InteractionModel):
    """
    Returns a list of Google Drive object IDs that contain the
    vendor responses for this particular interaction
    """
    interaction_folders = drive_client.get_files_by_drive_id(
        filename=request.interactionId, drive_id=settings.ROOT_DIRECTORY
    )

    vendor_file_ids = []
    for dir in interaction_folders:
        files = drive_client.get_files_in_folder(id=dir["id"])
        for file in files:
            vendor_file_ids.append(file)

    return responses.JSONResponse(
        status_code=202,
        content={"interaction": request.interactionId, "data": vendor_file_ids},
    )


class ResourceModel(BaseModel):
    resourceId: str


@router.post("/export/directories")
async def get_directories(request: ResourceModel):
    return responses.JSONResponse(
        status_code=202, content=drive_client.get_files_in_folder(id=request.resourceId)
    )


@router.post("/export/resource")
async def export_resource(request: ResourceModel):
    return responses.Response(
        status_code=202, content=drive_client.export(request.resourceId)
    )
