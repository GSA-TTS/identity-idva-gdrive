import logging
import json
import re
import requests

from opensearchpy import OpenSearch

from gdrive import settings, error

log = logging.getLogger(__name__)


def export(interactionId):
    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    subflowquery = {
        "size": 500,
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "parentInteractionProps.parentInteractionId": interactionId
                                    }
                                },
                                {"exists": {"field": "interactionId"}},
                            ]
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "properties.outcomeDescription.value": interactionId
                                    }
                                },
                                {
                                    "match_phrase": {
                                        "properties.outcomeType.value": "parent_id"
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
        },
        "_source": ["interactionId"],
    }

    query = {
        "size": 1000,
        "query": {
            "bool": {"should": [{"match_phrase": {"interactionId": interactionId}}]}
        },
        "sort": {"tsEms": {"order": "asc"}},
    }

    # get subflow ids
    subs = es.search(body=json.dumps(subflowquery), index="_all")
    for sub in subs["hits"]["hits"]:
        clause = {"match_phrase": {"interactionId": sub["_source"]["interactionId"]}}
        query["query"]["bool"]["should"].append(clause)

    qstring = json.dumps(query)
    r = es.search(body=qstring, index="dev-eventsoutcome-*")

    output = []

    for hit in r["hits"]["hits"]:
        if hit["_source"].get("capabilityName") == "logOutcome":
            output.append(hit["_source"])

    return output


def codename(data: str):
    codenames = settings.CODE_NAMES

    for service, codename in codenames.items():
        data = re.sub(service, codename, data, flags=re.IGNORECASE)

    return data


def export_response(responseId, survey_response):
    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    query_interactionId = {
        # "size": 1000,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"properties.outcomeType.value": "survey_data"}},
                    {"match": {"properties.outcomeDescription.value": f"{responseId}"}},
                ]
            }
        },
    }

    # query for interaction IDs
    # update+query on document IDS from interaction IDs

    # get subflow ids
    results_interacitonId = es.search(
        body=json.dumps(query_interactionId), index="_all"
    )

    # query for ineteraction IDs associated with responseID
    interactionIds_match = []

    # double encode json to force quote escape
    # due to it being stored as a string at rest
    double_encoded_response = json.dumps(json.dumps(survey_response))

    query_response_data = {
        "script": {
            "source": f"ctx._source.properties.outcomeDescription.value = {double_encoded_response}"
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "properties.outcomeType.value": "survey_response"
                        }
                    },
                    {"bool": {"should": interactionIds_match}},
                ]
            }
        },
    }

    for hit in results_interacitonId["hits"]["hits"]:
        if hit["_source"]["capabilityName"] == "logOutcome":
            interactionId = hit["_source"]["interactionId"]
            match = {"match": {"interactionId": f"{interactionId}"}}
            interactionIds_match.append(match)

    if len(interactionIds_match) == 0:
        raise error.ExportError(
            f"No flow interactionId match for responseId: {responseId}"
        )

    results_update = es.update_by_query(
        index="_all", body=query_response_data, refresh=True
    )

    return list(map(lambda id: id["match"]["interactionId"], interactionIds_match))


def get_qualtrics_response(surveyId: str, responseId: str):
    url = f"http://{settings.QUALTRICS_APP_URL}:{settings.QUALTRICS_APP_PORT}/response"

    r = requests.post(
        url,
        json={"surveyId": surveyId, "responseId": responseId},
        timeout=30,  # qualtrics microservice retries as it waits for response to become available
    )
    if r.status_code != 200:
        raise error.ExportError(
            f"No survey response found for responseId: {responseId}"
        )

    return r.json()
