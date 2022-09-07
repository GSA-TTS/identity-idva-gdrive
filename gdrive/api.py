"""
gdrive rest api
"""

import base64 as base64decoder
import io
import logging

import fastapi
from fastapi import Body
from starlette.requests import Request

from . import client, settings

log = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.post("/upload")
async def upload_file(id, filename, request: Request, base64: bool = False):
    """
    Upload file to gdrive.
    """
    body = await request.body()

    if base64:
        body = base64decoder.b64decode(body)

    stream = io.BytesIO(body)

    parent = client.create_folder(id, settings.ROOT_DIRECTORY)
    client.upload_basic(filename, parent, stream)
