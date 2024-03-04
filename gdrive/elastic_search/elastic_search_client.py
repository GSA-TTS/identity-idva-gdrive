import json
import logging

from opensearchpy import OpenSearch
from sqlalchemy import exc
from gdrive import settings
from gdrive.database import crud, models

log = logging.getLogger(__name__)


def get_interaction_sk_event(interaction_id: str):
    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    query = {
        "query": {
            "bool": {"should": [{"match_phrase": {"interactionId": interaction_id}}]}
        },
        "sort": {"tsEms": {"order": "asc"}},
    }

    qstring = json.dumps(query)
    r = es.search(body=qstring, index="dev-skevents-*")
    for hit in r["hits"]["hits"]:
        model = models.SkEventModel(
            id=hit["_id"],
            interaction_id=hit["_source"]["interactionId"],
            json_content=hit["_source"],
            timestamp=hit["_source"]["tsEms"],
        )
        try:
            crud.create_row(model)
        except exc.IntegrityError as _:
            log.error("Error writing id=%s" % model.id)

    return r


def get_interaction_event_outcome(interaction_id: str):
    es = OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    query = {
        "query": {
            "bool": {"should": [{"match_phrase": {"interactionId": interaction_id}}]}
        },
        "sort": {"tsEms": {"order": "asc"}},
    }

    qstring = json.dumps(query)
    r = es.search(body=qstring, index="dev-eventsoutcome-*")
    for hit in r["hits"]["hits"]:
        model = models.EventOutcomeModel(
            id=hit["_id"],
            company_id=hit["_source"]["companyId"],
            connection_id=hit["_source"]["companyId"],
            connector_id=hit["_source"]["connectorId"],
            flow_id=hit["_source"]["flowId"],
            flow_version_id=hit["_source"]["flowVersionId"],
            event_id=hit["_source"]["id"],
            interaction_id=hit["_source"]["interactionId"],
            name=hit["_source"]["name"],
            node_description=hit["_source"]["properties"]["nodeDescription"]["value"],
            node_title=hit["_source"]["properties"]["nodeTitle"]["value"],
            outcome_description=hit["_source"]["properties"]["outcomeDescription"][
                "value"
            ],
            outcome_status=hit["_source"]["properties"]["outcomeStatus"]["value"],
            outcome_type=hit["_source"]["properties"]["outcomeType"]["value"],
            should_continue_on_error=hit["_source"]["properties"][
                "shouldContinueOnError"
            ]["value"],
            template_precompile=hit["_source"]["properties"]["templatePrecompile"],
            signal_id=hit["_source"]["signalId"],
            transition_id=hit["_source"]["transitionId"],
            timestamp=hit["_source"]["tsEms"],
        )

        try:
            crud.create_row(model)
        except exc.IntegrityError as _:
            log.error("Error writing id=%s" % model.id)

    return r
