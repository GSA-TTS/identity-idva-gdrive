"""
Configuration for the gdrive microservice settings.
Context is switched based on if the app is in debug mode.
"""
import json
import logging
import os

log = logging.getLogger(__name__)

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG set is set to True if env var is "True"
DEBUG = os.getenv("DEBUG", "False") == "True"

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.getLevelName(logging.INFO))
logging.basicConfig(level=LOG_LEVEL)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
SERVICE_ACCOUNT_FILE = "credentials.json"
ROOT_DIRECTORY = ""
CODE_NAMES = None
CREDENTIALS = None

ES_HOST = os.getenv("ES_HOST")
ES_PORT = os.getenv("ES_PORT")

QUALTRICS_APP_URL = os.getenv("QUALTRICS_APP_URL")
QUALTRICS_APP_PORT = os.getenv("QUALTRICS_APP_PORT")

try:
    vcap_services = os.getenv("VCAP_SERVICES")
    config = {}
    if vcap_services:
        user_services = json.loads(vcap_services)["user-provided"]
        for service in user_services:
            if service["name"] == "gdrive":
                log.info("Loading credentials from env var")
                config = service["credentials"]
                break
    else:
        with open(SERVICE_ACCOUNT_FILE) as file:
            log.info("Loading credentials from creds file")
            config = json.load(file)
    CREDENTIALS = config["credentials"]
    ROOT_DIRECTORY = config["root_directory"]
    CODE_NAMES = config["code_names"]
    SHEETS_ID = config["sheets_id"]
except (json.JSONDecodeError, KeyError, FileNotFoundError) as err:
    log.warning("Unable to load credentials from VCAP_SERVICES")
    log.debug("Error: %s", str(err))
