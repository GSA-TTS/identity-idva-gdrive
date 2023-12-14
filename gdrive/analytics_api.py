"""
Google Analytics Rest API
"""

from datetime import datetime, timedelta
import logging
from typing import Optional

import fastapi
from pydantic import BaseModel
from fastapi import responses
from gdrive import analytics_client
from gdrive.idva import flow_analytics

log = logging.getLogger(__name__)
router = fastapi.APIRouter()


class AnalyticsRequest(BaseModel):
    startDate: str
    endDate: str


@router.post("/analytics")
async def run_analytics_default(req: Optional[AnalyticsRequest] = None):
    start = None
    end = None
    message = None
    if req is None:
        start = datetime.today() - timedelta(days=1)
        message = "Analytics report for %s complete." % (datetime.date(start))
    else:
        try:
            start = datetime.strptime(req.startDate, analytics_client.API_DATE_FORMAT)
            end = datetime.strptime(req.endDate, analytics_client.API_DATE_FORMAT)
            message = "Analytics report for %s - %s complete." % (
                datetime.date(start),
                datetime.date(end),
            )
        except ValueError as err:
            # @suppress("py/stack-trace-exposure")
            return responses.JSONResponse(
                status_code=422,
                content="Failed (invalid date parameters): %s" % (err),
            )

    run_analytics(start, end)
    return responses.JSONResponse(
        status_code=202,
        content=message,
    )


@router.post("/analytics/list")
async def list_accounts():
    list_accounts()
    return responses.JSONResponse(
        status_code=202, content="List request is being processed."
    )


def run_analytics(start_date: datetime, end_date: datetime):
    try:
        flow_analytics.create_report(start_date, end_date)
    except Exception as e:
        log.error(e)


def list_accounts():
    try:
        list_response = analytics_client.list()
        if list_response is not None:
            log.info("-------------------------------")
            for act in list_response.accounts:
                log.info("Name:\t\t%s" % (act.name))
                log.info("Display name:\t%s" % (act.display_name))
                log.info("-------------------------------")
        else:
            log.warn(
                "List response was none. Ensure credentials are set correctly"
                + " and you have access to the cloud property."
            )
    except Exception as e:
        log.error(e.args)
