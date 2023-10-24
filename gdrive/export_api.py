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
from gdrive.database import crud, models

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
    try:
        response = export_client.get_qualtrics_response(
            request.surveyId, request.responseId
        )

        log.info("Response found, beginning export.")

        if response["status"] != "Complete":
            raise error.ExportError(
                f"Cannot upload incomplete survery response to raw completions spreadsheet: {request.responseId}"
            )

        # By the time we get here, we can count on the response containing the demographic data
        # as it is included in the Completed flow responses. Responses without complete status
        # throws exception in get_qualtrics_response
        survey_resp = response["response"]

        if request.participant:
            participant = request.participant
            client.upload_participant(
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

        # call function that queries ES for all analytics entries (flow interactionId) with responseId
        interactionIds = export_client.export_response(request.responseId, response)

        log.info("Analytics updated, beginning gdrive export.")

        # export list of interactionIds to gdrive
        for id in interactionIds:
            await upload_file(id)
    except error.ExportError as e:
        log.error(e.args)


class FindModel(BaseModel):
    """
    Request body format for the `/find` endpoint
    """

    responseId: str
    field: str
    values: list[str]
    result_field: str | None = None


@router.post("/find")
async def find(find: FindModel):
    # for given responseid, find all occurences of
    result = find.result_field if find.result_field is not None else find.field
    export_data = export_client.find(find.responseId, find.field, find.values, result)
    return export_data
