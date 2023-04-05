"""
gdrive rest api
"""

import base64 as base64decoder
import io
import logging

import fastapi
from fastapi import Response, status
from googleapiclient.http import HttpError
from starlette.requests import Request

from . import client, settings

log = logging.getLogger(__name__)

router = fastapi.APIRouter()

client.init()


@router.post("/upload")
async def upload_file(
    id, filename, request: Request, response: Response, base64: bool = False
):
    """
    Upload file to gdrive.
    """

    try:
        body = await request.body()

        if base64:
            body = base64decoder.b64decode(body)

        stream = io.BytesIO(body)

        parent = client.create_folder(id, settings.ROOT_DIRECTORY)
        client.upload_basic(filename, parent, stream)

    except HttpError as error:
        log.error(f"An error occurred: {error}")
        response.status_code = error.status_code


@router.delete("/upload")
async def delete_file(filename, response: Response):
    """
    Delete file from gdrive.
    """

    try:
        files = client.get_files(filename)
        if files:
            for file in files:
                client.delete_file(file["id"])
        else:
            response.status_code = status.HTTP_404_NOT_FOUND

    except HttpError as error:
        log.error(f"An error occurred: {error}")
        response.status_code = error.status_code
