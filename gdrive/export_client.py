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


def get_all_InteractionIds(responseId):
    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    # query for all parent flow intraction ids for a given response id
    query_interactionId = {
        "size": 500,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"properties.outcomeType.value": "survey_data"}},
                    {"match": {"properties.outcomeDescription.value": f"{responseId}"}},
                ]
            }
        },
        "_source": ["interactionId"],
    }

    results_interacitonId = es.search(
        body=json.dumps(query_interactionId), index="_all"
    )

    if results_interacitonId["hits"]["total"]["value"] == 0:
        return []

    interactionIds_match = list(
        map(
            lambda res: res["_source"]["interactionId"],
            results_interacitonId["hits"]["hits"],
        )
    )

    subflow_query_1 = list(
        map(
            lambda res: {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                "parentInteractionProps.parentInteractionId": f'{res["_source"]["interactionId"]}'
                            }
                        },
                        {"exists": {"field": "interactionId"}},
                    ]
                }
            },
            results_interacitonId["hits"]["hits"],
        )
    )

    subflow_query_2 = list(
        map(
            lambda res: {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                "properties.outcomeDescription.value": f'{res["_source"]["interactionId"]}'
                            }
                        },
                        {"match_phrase": {"properties.outcomeType.value": "parent_id"}},
                    ]
                }
            },
            results_interacitonId["hits"]["hits"],
        )
    )

    subflowquery = {
        "size": 500,
        "query": {"bool": {"should": subflow_query_1 + subflow_query_2}},
        "_source": ["interactionId"],
    }

    subs = es.search(body=json.dumps(subflowquery), index="_all")

    sub_interactionIds_match = list(
        map(
            lambda res: res["_source"]["interactionId"],
            subs["hits"]["hits"],
        )
    )

    return interactionIds_match + sub_interactionIds_match


def find(responseId, field, values, result):
    # find values in find for all flow for a given responseId
    # field and result should be one of:
    #   properties.outcomeDescription.value
    #   properties.outcomeStatus.value
    #   properties.outcomeType.value
    #   properties.outcomeDetail.value

    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    all_interactionIds = []
    for resid in responseId:
        all_interactionIds.extend(get_all_InteractionIds(resid))

    if len(all_interactionIds) == 0:
        return {"found": []}

    all_interactionIds_match = list(
        map(lambda res: {"match": {"interactionId": f"{res}"}}, all_interactionIds)
    )

    values_match = list(
        map(
            lambda res: {"match_phrase": {field: res}},
            values,
        )
    )

    query_found = {
        "size": 500,
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": values_match,
                        }
                    },
                    {
                        "bool": {
                            "should": all_interactionIds_match,
                        }
                    },
                ]
            }
        },
        "_source": ["interactionId", result],
    }

    found_result = es.search(body=json.dumps(query_found), index="_all")

    list_found = list(
        map(
            lambda x: recursive_decent(x["_source"], result.split(".")),
            found_result["hits"]["hits"],
        )
    )

    return {"found": list_found}


def recursive_decent(obj: dict | str, query: list[str]):
    # given dict and a dot notated key name, return value of key
    if query == [] or not isinstance(obj, dict):
        return obj
    return recursive_decent(obj.get(query[0], ""), query[1:])
