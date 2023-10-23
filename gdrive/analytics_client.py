import datetime

from google.oauth2 import service_account
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

import logging
import pandas as pd

from gdrive import settings

log = logging.getLogger(__name__)

creds = service_account.Credentials.from_service_account_info(settings.CREDENTIALS)
API_DATE_FORMAT = "%Y-%m-%d"

"""
Client for the Google Analytics (GA4) API

This class contains functions relating to downloading analytics data
for the IDVA flow.
"""


def download(
    property_id, target_date: datetime, end_date: datetime = None
) -> pd.DataFrame:
    """
    Access Google Analytics (GA4) api and download desired analytics report.
    """
    if end_date is None:
        end_date = target_date

    request = RunReportRequest(
        property=f"properties/{property_id}",
        limit="250",
        # https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
        dimensions=[
            Dimension(name="eventName"),
            Dimension(name="firstUserCampaignName"),
            Dimension(name="firstUserMedium"),
            Dimension(name="firstUserSource"),
            Dimension(name="isConversionEvent"),
            Dimension(name="linkUrl"),
        ],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="eventCountPerUser"),
            Metric(name="conversions"),
        ],
        date_ranges=[
            DateRange(
                start_date=format_date_for_api(target_date),
                end_date=format_date_for_api(end_date),
            )
        ],
    )

    return BetaAnalyticsDataClient(credentials=creds).run_report(request)


def list():
    """
    List the available properties the user has access to. Can be run to
    verify setup of the enviornment is correct.
    """
    client = AnalyticsAdminServiceClient(credentials=creds)
    return client.list_accounts()


def format_date_for_api(date: datetime):
    """
    Formats datetime object for Google Analytics Api (GA4) input
    """
    return date.strftime(API_DATE_FORMAT)


def create_df_from_analytics_response(response):
    """
    Extracts values from Google Analytics API response and transforms
    them into pandas DataFrame for ease of use. This enables the analytics
    client to do any processing of the data desired, if something comes up in
    the future we want to do but isnt supported in GA4.
    """
    all_headers = []
    for _, header in enumerate(response.dimension_headers):
        all_headers += [header.name]
    for _, header in enumerate(response.metric_headers):
        all_headers += [header.name]

    arr = [all_headers]
    for _, row in enumerate(response.rows):
        row_li = []
        for _, val in enumerate(row.dimension_values):
            row_li += [val.value]
        for _, val in enumerate(row.metric_values):
            row_li += [val.value]
        arr += [row_li]

    return pd.DataFrame(arr)
