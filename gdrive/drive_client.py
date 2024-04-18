import io
import logging
import json
import mimetypes
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from gdrive import settings, error

log = logging.getLogger(__name__)

creds = service_account.Credentials.from_service_account_info(
    settings.CREDENTIALS, scopes=settings.SCOPES
)

service = build("drive", "v3", credentials=creds)


def init():
    drive = drives_list()
    result = (
        service.files()
        .get(fileId=settings.ROOT_DIRECTORY, supportsAllDrives=True)
        .execute()
    )
    driveId = result["id"]
    log.info(f"Connected to Root Directory {driveId}")


def list(count: int = 10, shared: bool = True) -> None:
    """
    Prints the names and ids of the first <count> files the user has access to.
    """

    results = (
        service.files()
        .list(
            pageSize=count,
            fields="*",
            supportsAllDrives=shared,
            includeItemsFromAllDrives=shared,
        )
        .execute()
    )
    items = results.get("files", [])

    if not items:
        log.info("No files found.")
        return
    log.info("Files:")
    log.info("name (id) parents trashed")
    for item in items:
        try:
            log.info(
                "{0} ({1}) {2} {3}".format(
                    item["name"], item["id"], item["parents"], item["trashed"]
                )
            )
        except KeyError as error:
            log.info(f"No such key: {error} in {item}")


def create_empty_spreadsheet(filename: str, parent_id: str) -> str:
    file_metadata = {
        "name": filename,
        "parents": [parent_id],
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }

    file = (
        service.files()
        .create(body=file_metadata, fields="id", supportsAllDrives=True)
        .execute()
    )

    return file.get("id")


def drives_list():
    """
    List available shared drives
    """

    result = service.drives().list().execute()
    return result


def upload_basic(filename: str, parent_id: str, bytes: io.BytesIO) -> str:
    """
    Upload new file to given  parent folder
    Returns : Id of the file uploaded
    """

    file_metadata = {"name": filename, "parents": [parent_id]}

    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype is None:
        # Guess failed, use octet-stream.
        mimetype = "application/octet-stream"

    media = MediaIoBaseUpload(bytes, mimetype=mimetype)

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )

    log.debug(f'File ID: {file.get("id")}')

    return file.get("id")


def create_folder(name: str, parent_id: str) -> str:
    """
    Create a folder and prints the folder ID
    Returns : Folder Id
    """

    file_metadata = {
        "name": name,
        "parents": [parent_id],
        "mimeType": "application/vnd.google-apps.folder",
    }

    existing = (
        service.files()
        .list(
            q=f"name='{name}' and '{parent_id}' in parents",
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
        .get("files", [])
    )

    if not existing:
        file = (
            service.files()
            .create(body=file_metadata, fields="id", supportsAllDrives=True)
            .execute()
        )
        log.debug(f'Folder has created with ID: "{file.get("id")}".')
    else:
        file = existing[0]
        log.debug("Folder already exists")

    return file.get("id")


def get_files(filename: str) -> List:
    """
    Get list of files by filename
    """

    results = (
        service.files()
        .list(
            q=f"name = '{filename}'",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )

    return results["files"]


def get_files_by_drive_id(filename: str, drive_id: str):
    """
    Get list of files by filename
    """

    results = (
        service.files()
        .list(
            q=f"name = '{filename}'",
            corpora="drive",
            driveId=drive_id,
            includeTeamDriveItems=True,
            supportsTeamDrives=True,
        )
        .execute()
    )

    return results["files"]


def get_files_in_folder(id: str) -> List:
    """
    Get list of files within a folder by folder ID
    """
    files = []
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=f"'{id}' in parents and trashed=false",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields="nextPageToken, files(id, name, modifiedTime, createdTime)",  # Add modifiedTime and createdTime
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return files


def delete_file(id: str) -> None:
    """
    Delete file by id
    """

    service.files().delete(fileId=id, supportsAllDrives=True).execute()


def export(id: str) -> any:
    return service.files().get_media(fileId=id).execute()
