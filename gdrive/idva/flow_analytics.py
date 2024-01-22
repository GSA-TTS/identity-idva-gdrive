import datetime
from enum import Enum
import pandas as pd
import logging

from gdrive import settings, sheets_client, drive_client, analytics_client
from gdrive.idva.pivot_director import IDVAPivotDirector
from gdrive.sheets.builders import FormulaBuilder
from gdrive.sheets.types import FormulaEnum, Range, StringLiteral

log = logging.getLogger(__name__)
idva = IDVAPivotDirector()


class SheetsEnum(str, Enum):
    REKREWT = "Rekrewt Pivot Tables"
    GSA = "GSA Use Pivot Table"


def create_report(start_date: datetime, end_date: datetime):
    response = analytics_client.download(
        settings.ANALYTICS_PROPERTY_ID, start_date, end_date
    )

    analytics_df = analytics_client.create_df_from_analytics_response(response)
    analytics_df = preprocess_report(analytics_df)

    sheets_id = export(analytics_df, start_date, end_date)
    names_to_id = create_pages(sheets_id)
    create_pivot_tables(analytics_df, names_to_id, sheets_id)


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


def preprocess_report(df: pd.DataFrame) -> pd.DataFrame:
    tracked_events = ["first_visit", "session_start"]
    tracked_sources = [
        "m.facebook.com",
        "fb.com",
        "([a-zA-Z].+)craigslist.org",
        "reddit.com",
        "redd.it",
        "t.co",
        "x.com",
        "twitter",
        "linked.com",
        "lnkd.in",
    ]
    tracked_mediums = ["fb", "cl", "rd", "tx", "ln"]

    for event in tracked_events:
        tracked_df = df[df[0] == event]
        for source in tracked_sources:
            if tracked_df[tracked_df[3].str.match(source)].empty:
                add_source_placeholder_row(df, event, source)

        for medium in tracked_mediums:
            if tracked_df[tracked_df[2].str.match(medium)].empty:
                add_medium_placeholder_row(df, event, medium)

    return df


def add_source_placeholder_row(df: pd.DataFrame, event: str, source: str) -> None:
    logging.info(f"Adding placeholder {event} for {source}")
    df.loc[len(df.index)] = [event, "---", "---", source, "---", "---", 0, 0, 0, 0, 0]


def add_medium_placeholder_row(df: pd.DataFrame, event: str, medium: str) -> None:
    logging.info(f"Adding placeholder {event} for {medium}")
    df.loc[len(df.index)] = [event, "---", medium, "---", "---", "---", 0, 0, 0, 0, 0]


def create_pages(sheets_id: str) -> dict:
    """
    Add new pages and pivot tables.

    This function is fairly naive and inefficient. If we ever want to make Google Sheets
    more often than once a day, we should refactor this to limit the number of API transactions.

    Args:
        df (pandas.DataFrame): Tabular data in the spreadsheet
        sheets_id (str): Google Sheets object ID
    Returns:
        names_to_id (dict): A Dictionary mapping string sheet names to IDs
    """
    new_sheet_name_to_id = sheets_client.add_new_pages(
        [SheetsEnum.REKREWT.value, SheetsEnum.GSA.value], sheets_id, column_count=30
    )
    log.info("Added %s pages to %s" % (len(new_sheet_name_to_id.keys()), sheets_id))
    return new_sheet_name_to_id


def create_pivot_tables(df: pd.DataFrame, names_to_id: dict, sheets_id: str):
    # Make a dictionary mapping the name of the column to its index, useful for the pivot tables.
    col_dict = {}
    for idx, val in enumerate(df.iloc[0]):
        col_dict[val] = idx

    facebook_pivot(sheets_id, names_to_id, col_dict)
    craigslist_pivot(sheets_id, names_to_id, col_dict)
    reddit_pivot(sheets_id, names_to_id, col_dict)
    twitter_x_pivot(sheets_id, names_to_id, col_dict)
    linkedin_pivot(sheets_id, names_to_id, col_dict)
    linked_pivot(sheets_id, names_to_id, col_dict)

    sheets_client.add_pivot_tables(
        sheets_id, names_to_id[SheetsEnum.GSA.value], idva.clicks(col_dict)
    )

    # Add formulas for some totals here
    session_sum = FormulaBuilder(FormulaEnum.SUM, params=[Range("C2", "G2")])
    first_visit_sum = FormulaBuilder(FormulaEnum.SUM, params=[Range("C3", "G3")])

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "A2", "Sessions"
    )  # Sessions for each source label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "A3", "First Visits"
    )  # First visits for each source label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "B1", "Total"
    )  # Total of each event label

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "B2", session_sum.render()
    )  # total value
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "B3", first_visit_sum.render()
    )  # total value


def facebook_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "A5", "FACEBOOK"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "C1", "FACEBOOK"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.facebook(col_dict),
        row_idx=5,
        col_idx=0,
    )

    facebook_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "A6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    facebook_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "A6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "C2", facebook_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "C3", facebook_visit.render()
    )


def craigslist_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "G5", "CRAIGSLIST"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "D1", "CRAIGSLIST"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.craigslist(col_dict),
        row_idx=5,
        col_idx=6,
    )

    craigslist_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "G6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    craigslist_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "G6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "D2", craigslist_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "D3", craigslist_visit.render()
    )


def reddit_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "L5", "REDDIT"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "E1", "REDDIT"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.reddit(col_dict),
        row_idx=5,
        col_idx=11,
    )

    reddit_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "L6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    reddit_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "L6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "E2", reddit_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "E3", reddit_visit.render()
    )


def twitter_x_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "Q5", "TWITTER/X"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "F1", "TWITTER/X"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.twitter_x(col_dict),
        row_idx=5,
        col_idx=16,
    )

    twitter_x_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "Q6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    twitter_x_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "Q6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "F2", twitter_x_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "F3", twitter_x_visit.render()
    )


def linkedin_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "V5", "LINKEDIN"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "G1", "LINKEDIN"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.linkedin(col_dict),
        row_idx=5,
        col_idx=21,
    )

    linkedin_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "V6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    linkedin_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "V6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "G2", linkedin_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "G3", linkedin_visit.render()
    )


def linked_pivot(sheets_id, names_to_id, col_dict):
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "AA5", "LINKED.COM"
    )  # Pivot table Label
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "H1", "LINKED.COM"
    )  # Totals label

    sheets_client.add_pivot_tables(
        sheets_id,
        names_to_id[SheetsEnum.REKREWT.value],
        idva.linked(col_dict),
        row_idx=5,
        col_idx=26,
    )

    linkedin_sessions = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "AA6",
            StringLiteral("eventName"),
            StringLiteral("session_start"),
        ],
    )

    linkedin_visit = FormulaBuilder(
        FormulaEnum.GET_PIVOT_DATA,
        params=[
            StringLiteral("SUM of eventCount"),
            "AA6",
            StringLiteral("eventName"),
            StringLiteral("first_visit"),
        ],
    )

    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "H2", linkedin_sessions.render()
    )
    sheets_client.update_cell_value(
        sheets_id, SheetsEnum.REKREWT.value, "H3", linkedin_visit.render()
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
