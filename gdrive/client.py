import io
import mimetypes
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from gdrive import settings

log = logging.getLogger(__name__)

if settings.CREDENTIALS != None:
    log.info("Loading credentials from env var")
    creds = service_account.Credentials.from_service_account_info(
        settings.CREDENTIALS, scopes=settings.SCOPES
    )
else:
    log.info("Loading credentials from file")
    creds = service_account.Credentials.from_service_account_file(
        settings.SERVICE_ACCOUNT_FILE, scopes=settings.SCOPES
    )

def list(count: int):
    """
    Prints the names and ids of the first <count> files the user has access to.
    """

    try:
        service = build("drive", "v3", credentials=creds)

        results = (
            service.files()
            .list(
                pageSize=count, fields="nextPageToken, files(id, name, parents, trashed)"
            )
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        print("name (id) parents trashed")
        for item in items:
            print(
                "{0} ({1}) {2} {3}".format(
                    item["name"], item["id"], item["parents"], item["trashed"]
                )
            )
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


def upload_basic(filename: str, parent_id: str, bytes: io.BytesIO):
    """Insert new file.
    Returns : Id's of the file uploaded
    """

    try:
        service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": filename, "parents": [parent_id]}

        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            # Guess failed, use octet-stream.
            mimetype = "application/octet-stream"

        media = MediaIoBaseUpload(bytes, mimetype=mimetype)

        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        
        print(f'File ID: {file.get("id")}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    return file.get("id")


def create_folder(name: str, parent_id: str):
    """Create a folder and prints the folder ID
    Returns : Folder Id
    """

    try:
        service = build("drive", "v3", credentials=creds)
        file_metadata = {
            "name": name,
            "parents": [parent_id],
            "mimeType": "application/vnd.google-apps.folder",
        }

        existing = service.files().list(q=f"name='{name}' and '{parent_id}' in parents", fields="files(id, name)").execute().get("files", [])

        if not existing:
            file = service.files().create(body=file_metadata, fields="id").execute()
            print(f'Folder has created with ID: "{file.get("id")}".')
        else:
            file = existing[0]
            print("Folder already exists")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    return file.get("id")


def delete_file(id: str):

    try:
        service = build("drive", "v3", credentials=creds)

        service.files().delete(fileId=id).execute()

    except HttpError as error:
        print(f"An error occurred: {error}")
