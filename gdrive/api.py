"""
gdrive rest api
"""

import base64 as base64decoder
import io
import logging
import zipfile

import fastapi
from fastapi import Response, status
from googleapiclient.http import HttpError
from starlette.requests import Request

from . import drive_client, settings

log = logging.getLogger(__name__)

router = fastapi.APIRouter()

drive_client.init()


# Patch zip decodeExtra to ignore invalid extra data
def nullDecode(self):
    return


zipfile.ZipInfo._decodeExtra = nullDecode  # type: ignore


@router.post("/upload")
async def upload_file(
    id,
    filename,
    request: Request,
    response: Response,
    base64: bool = False,
    zip: bool = False,
):
    """
    Upload file to gdrive.
    """

    try:
        body = await request.body()

        if base64:
            body = base64decoder.b64decode(body)

        stream = io.BytesIO(body)

        parent = drive_client.create_folder(id, settings.ROOT_DIRECTORY)

        if zip:
            try:
                with zipfile.ZipFile(stream) as archive:
                    files = archive.filelist
                    for file in files:
                        image = io.BytesIO(archive.read(file))
                        client.upload_basic(
                            f"{filename}_{file.filename}", parent, image
                        )
            except zipfile.BadZipFile as error:
                client.upload_basic(filename, parent, stream)
                log.error(f"An error occurred: {error}")
                response.status_code = status.HTTP_400_BAD_REQUEST
        else:
            drive_client.upload_basic(filename, parent, stream)

    except HttpError as error:
        log.error(f"An error occurred: {error}")
        response.status_code = error.status_code


@router.delete("/upload")
async def delete_file(filename, response: Response):
    """
    Delete file from gdrive.
    """

    try:
        files = drive_client.get_files(filename)
        if files:
            for file in files:
                drive_client.delete_file(file["id"])
        else:
            response.status_code = status.HTTP_404_NOT_FOUND

    except HttpError as error:
        log.error(f"An error occurred: {error}")
        response.status_code = error.status_code


@router.get("/list")
async def list():
    """ """
    s = client.list(count=200, parent="0AFrX3czp_UwZUk9PVA")
    print(s)


@router.get("/count")
async def list():
    """ """
    s = drive_client.count(parent="1dz8UklyVsBDLP0wC5HPVSOuKpYGqrNEI")
    print(s)


@router.post("/move")
async def move_file(file: str, source: str, dest: str):
    return drive_client.move(file, source, dest)


@router.post("/create_folder")
async def move_file(name: str, dest: str):
    return drive_client.create_folder(name, dest)
