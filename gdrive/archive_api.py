"""
Google Analytics Rest API
"""
import logging

import fastapi
from opensearchpy import OpenSearch
from pydantic import BaseModel
from fastapi import responses

from gdrive import settings
from gdrive.elastic_search import elastic_search_client

log = logging.getLogger(__name__)
router = fastapi.APIRouter()


class ArchiveInteractionEventsRequest(BaseModel):
    interaction_id: str


@router.post("/archive/interaction-sk-events")
async def archive_interaction_events(req: ArchiveInteractionEventsRequest):
    return responses.JSONResponse(
        status_code=202,
        content=elastic_search_client.get_interaction_sk_event(req.interaction_id),
    )


@router.post("/archive/interaction-events-outcome")
async def archive_interaction_events(req: ArchiveInteractionEventsRequest):
    return responses.JSONResponse(
        status_code=202,
        content=elastic_search_client.get_interaction_event_outcome(req.interaction_id),
    )
