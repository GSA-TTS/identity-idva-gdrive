"""
gdrive rest api
"""

import base64 as base64decoder
import io
import json
import logging
import zipfile

import fastapi
from fastapi import Response, status
from googleapiclient.http import HttpError
from starlette.requests import Request

from . import export_client, client, settings

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
