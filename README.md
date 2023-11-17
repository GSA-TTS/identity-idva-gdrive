# IDVA GDrive Microservice
The IDVA GDrive microservice is a Python Fast API
application that interfaces IDVA applications to the Google Drive API.

## Building Locally

### Pre-requisites
Make sure you have the following installed if you intend to build the project locally.
- [Python 3.11](https://www.python.org/)
- [CloudFoundry CLI](https://docs.cloudfoundry.org/cf-cli/)

### Development Setup
To set up your environment, run the following commands (or the equivalent
commands if not using a bash-like terminal):

```shell
# Clone the project
git clone https://github.com/GSA-TTS/identity-idva-gdrive
cd identity-idva-gdrive

# Set up Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
# .venv\Scripts\Activate.ps1 on Windows

# Install dependencies and pre-commit hooks
python -m pip install -r requirements-dev.txt
pre-commit install
```
### Database Setup & Usage

Gdrive utilizes a postgres database to write various persistent data points. (ex. writing raw completion data from the `survey-export` endpoint) If the user does not wish to make use of this feature, no action is required. A NoSQL in memory DB is created with SQL Alchemy. 

However, if the user does wish to work on this DB locally, follow steps to [install PostgresDB](https://dev.to/sfpear/install-and-use-postgres-in-wsl-423d#:~:text=To%20install%20Postgres%20and%20run%20it%20in%20WSL%2C,installation%20and%20get%20the%20version%20number%3A%20psql%20--version). 

> **_NOTE:_** Once installed, a schema needs to be created for IDVA. `env.py` in alembic handles this dynamically, using SqlAlchemy to check if the schema is present and creating if not. This is done before any migrations take place and should be safe to run on a fresh db install.

Once the above SQL has been run on postgres, alembic can be used to build the DDL Dependencies.

Alembic uses the same connection string and schema as the gdrive module, loading the 
values in `settings.py` from the enviorment variable `IDVA_DB_CONN_STR`. In case a different URI is needed, the URI alembic uses can be configured manually in `alembic.ini`.
```ini
# Update Alembic connection string in Alembic.ini
sqlalchemy.url = postgresql://postgres:{PASSWORD}@{URL}:{PORT}
```
Use alembic to build database entities, and app is ready.
```shell
# This step may be nessessary if doing a rebuild of the whole schema, 
# clean install does not need to worry about this step. 
$ alembic downgrade base
# Updates the empty db schema with all of the DDL app dependencies
$ alembic upgrade head
#The project can be ran locally with:
$ uvicorn gdrive.main:app
```

### Running the application
After completing [development setup](#development-setup) application locally with:
```shell
python -m pytest
```

### API Endpoints


### Upload file
Upload a single file

`POST /upload`

```
Query parameters:
id: <parent interaciton id>
filename: <see codenames>
base64: <is base 64>
```

```
Request body:
<file data>
```

### Delete file
Upload a single file

`DELETE /upload`

```
Query parameters:
filename: <see codenames>
```


#### Analytics Export
Exports flow analytics from single interaction id.

`POST /export`

```
Query parameters:
interactionId: <parent flow interaciton id>
```


#### Analytics + Survey Response Export
Exports analytics in bulk that are associated with a survey response. Also uploads
participant data to google spread sheet. Data provided in the request body, as well
as demographic data collected from Qualtrix api will be uploaded. Only responses that 
have a Complete status (user has completed the survey) will be uploaded to the google spead sheet. 

`POST /survey-export`

```
Request body:
{
  "surveyId": str
  "responseId": str
  "participant": {
    "first": str
    "last": str
    "email": str
    "time": str
  }
}
```

#### Product Analytics Bulk Upload
Exports Google Analytics data gathered from the IDVA flow to Google Drive, as a google sheets object. Routine then builds pivot tables to enable user to read data easily. Default behaviour for the API `/analytics` writes data for the previous day.

The ID of the Google Drive folder is configurable in `ANALYTICS_ROOT`. (`settings`)

Optionally, the user can pass in a date range to be uploaded. The data is collated into a single document, and the same pivot tables are written on the collated data.

`POST /analytics`
```
Query parameters: None
```
`POST /analytics/daterange`
```JSON
// Request body
{
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD"
}
```


### Deploying to Cloud.gov during development
All deployments require having the correct Cloud.gov credentials in place. If
you haven't already, visit [Cloud.gov](https://cloud.gov) and set up your
account and CLI.

*manifest.yml* file contains the deployment configuration for cloud.gov, and expects
a vars.yaml file that includes runtime variables referenced. For info, see
[cloud foundry manifest files reference](https://docs.cloudfoundry.org/devguide/deploy-apps/manifest-attributes.html)

Running the following `cf` command will deploy the application to cloud.gov
```shell
cf push --vars-file vars.yaml \
  --var ENVIRONMENT=<env>
```

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in
[CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright
and related rights in the work worldwide are waived through the
[CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication.
By submitting a pull request, you are agreeing to comply with this waiver of
copyright interest.
