"""
Google Analytics Rest API
"""

from datetime import datetime
import logging

import fastapi
from pydantic import BaseModel
from fastapi import BackgroundTasks, responses
import pandas as pd

from gdrive import error, settings, analytics_client, sheets_client, drive_client

log = logging.getLogger(__name__)
router = fastapi.APIRouter()


class AnalyticsRequest(BaseModel):
    startDate: str = None
    endDate: str = None


@router.post("/analytics")
async def run_analytics(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_analytics_task, datetime.today(), None)
    return responses.JSONResponse(
        status_code=202,
        content="Analytics request for %s is being processed."
        % (datetime.date(datetime.today())),
    )


@router.post("/analytics/daterange")
async def run_analytics(background_tasks: BackgroundTasks, req: AnalyticsRequest):
    try:
        date_format = "%Y-%m-%d"
        start_date = datetime.strptime(req.startDate, date_format)
        end_date = datetime.strptime(req.endDate, date_format)

        background_tasks.add_task(run_analytics_task, start_date, end_date)
        return responses.JSONResponse(
            status_code=202,
            content="Analytics request for %s - %s is being processed."
            % (datetime.date(start_date), datetime.date(end_date)),
        )

    except ValueError as err:
        return responses.JSONResponse(
            status_code=422,
            content="Failed (invalid date parameters): %s" % (err),
        )


@router.post("/analytics/list")
async def list_accounts(backgroud_tasks: BackgroundTasks):
    backgroud_tasks.add_task(list_accounts_task)
    return responses.JSONResponse(
        status_code=202, content="List request is being processed."
    )


async def run_analytics_task(start_date: datetime, end_date: datetime):
    try:
        analytics_df = analytics_client.download(
            settings.ANALYTICS_PROPERTY_ID, start_date, end_date
        )
        sheets_id = export(analytics_df, start_date, end_date)
        analytics_export_post_processing(analytics_df, sheets_id=sheets_id)
    except Exception as e:
        log.error(e)


async def list_accounts_task():
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


def export(
    df: pd.DataFrame, date_of_report: datetime, end_date: datetime = None
) -> str:
    """
    Transform the downloaded response from the google analytics API into a
    Google Sheets Object.

    This function first touches a Google Sheets object with the drive API, then
    writes the analytics data to that object. As of right now there is no way to do
    this in one API transaction.

    Args:
        df (pandas.DataFrame): Tabular data to export to Google Sheets object
        date_of_report (datetime): Date the report was run
    Returns:
        str: Google Sheets ID of the new Sheets object
    """
    filename_str = generate_filename(date_of_report, end_date)
    analytics_folder_id = drive_client.create_folder(
        "Google Analytics", parent_id=settings.ANALYTICS_ROOT
    )

    # We have to do this in multiple steps with more than one client because the Sheets API
    # doesnt support opening a file in a given directory.
    sheets_id = drive_client.create_empty_spreadsheet(filename_str, analytics_folder_id)
    log.info("Uploading to folder %s (%s)" % ("Google Analytics", analytics_folder_id))
    result = sheets_client.export_df_to_gdrive_speadsheet(df, sheets_id)
    log.info(
        "Successfully created %s (%s)" % (filename_str, result.get("spreadsheetId"))
    )
    return sheets_id


def analytics_export_post_processing(df: pd.DataFrame, sheets_id: str):
    """
    Add new pages and pivot tables.

    This function is fairly naive and inefficient. If we ever want to make Google Sheets
    more often than once a day, we should refactor this to limit the number of API transactions.

    Args:
        df (pandas.DataFrame): Tabular data in the spreadsheet
        sheets_id (str): Google Sheets object ID
    """

    page1 = "Rekrewt Pivot Table - First Visit"
    page2 = "Rekrewt Pivot Table - Sessions"
    page3 = "GSA Use Pivot Table"
    page4 = "Completions"

    new_sheet_name_to_id = sheets_client.add_new_pages(
        [page1, page2, page3, page4], sheets_id
    )
    log.info("Added %s pages to %s" % (len(new_sheet_name_to_id.keys()), sheets_id))
    sheets_client.do_create_pivot_tables(
        df, (page1, page2, page3, page4), new_sheet_name_to_id, sheets_id
    )


def generate_filename(date: datetime, end_date: datetime = None):
    """
    Return filename for the new spreadsheet to be saved as

    Args:
        date (datetime): date to format
    Return:
        str: Formatted Date
    """
    ret = date.strftime("%Y%m%d")
    if end_date is not None and end_date != date:
        ret += "-%s" % (end_date.strftime("%Y%m%d"))
    return ret
