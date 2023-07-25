# IDVA GDrive Microservice
The IDVA Token microservice is a Python Flask
application that exposes an API for generating and validating simple tokens.

Tokens are at default valid for 7 days and have 1 use. Time and uses can be adjusted when registering a token.

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

The project can be ran locally with:
```shell
uvicorn gdrive.main:app
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
participant data to google spread sheet.

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
