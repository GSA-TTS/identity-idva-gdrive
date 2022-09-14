"""
Configuration for the gdrive microservice settings.
Context is switched based on if the app is in debug mode.
"""
import json
import logging
import os

log = logging.getLogger(__name__)

def load_credentials():
    vcap_services = os.getenv("VCAP_SERVICES")
    if vcap_services is not None:
        try:
            gdrive_service = json.loads(vcap_services)["user-provided"][0]
            if gdrive_service["name"] == "gdrive":
                return gdrive_service["credentials"]
            else:
                return None
        except (json.JSONDecodeError, KeyError) as err:
            log.warning("Unable to load credentials from VCAP_SERVICES")
            log.debug("Error: %s", str(err))
            return None
    return None

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG set is set to True if env var is "True"
DEBUG = os.getenv("DEBUG", "False") == "True"

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.getLevelName(logging.INFO))

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credentials.json"
ROOT_DIRECTORY = "1hIo6ynbn2ErRIWF4RqMQB6QDcebJ4R5E"
CREDENTIALS = load_credentials()
