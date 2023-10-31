import datetime
import pandas as pd
import logging

from gdrive import settings, sheets_client, drive_client, analytics_client

log = logging.getLogger(__name__)


def create_report(start_date: datetime, end_date: datetime):
    response = analytics_client.download(
        settings.ANALYTICS_PROPERTY_ID, start_date, end_date
    )

    analytics_df = analytics_client.create_df_from_analytics_response(response)
    sheets_id = export(analytics_df, start_date, end_date)
    create_pages_and_pivot_tables(analytics_df, sheets_id=sheets_id)


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


def create_pages_and_pivot_tables(df: pd.DataFrame, sheets_id: str):
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
    create_pivot_tables(
        df, (page1, page2, page3, page4), new_sheet_name_to_id, sheets_id
    )


def create_pivot_tables(
    df: pd.DataFrame, page_names: (str, str, str), names_to_id: dict, sheets_id: str
):
    # Make a dictionary mapping the name of the column to its index, useful for the pivot tables.
    col_dict = {}
    for idx, val in enumerate(df.iloc[0]):
        col_dict[val] = idx

    create_first_visit_pt(sheets_id, names_to_id[page_names[0]], col_dict)
    log.info(
        "Added 2 pivot tables to %s (%s)" % (page_names[0], names_to_id[page_names[0]])
    )

    create_session_start_pt(sheets_id, names_to_id[page_names[1]], col_dict)
    log.info(
        "Added 2 pivot tables to %s (%s)" % (page_names[1], names_to_id[page_names[1]])
    )

    create_clicks_pt(sheets_id, names_to_id[page_names[2]], col_dict)
    log.info(
        "Added pivot table to %s (%s)" % (page_names[2], names_to_id[page_names[2]])
    )

    create_feedback_pt(sheets_id, names_to_id[page_names[3]], col_dict)
    log.info(
        "Added pivot table to %s (%s)" % (page_names[3], names_to_id[page_names[3]])
    )

    sheets_client.update_cell_value(
        sheets_id, page_names[0], "A17", "Total First Visits"
    )
    sheets_client.update_cell_value(
        sheets_id,
        page_names[0],
        "A18",
        '=GETPIVOTDATA("SUM of eventCount",A1, "eventName", "first_visit") + GETPIVOTDATA("SUM of eventCount",F1, "eventName", "first_visit")',
    )
    log.info("Wrote totals to %s" % (page_names[0]))

    sheets_client.update_cell_value(sheets_id, page_names[1], "A17", "Total Sessions")
    sheets_client.update_cell_value(
        sheets_id,
        page_names[1],
        "A18",
        '=GETPIVOTDATA("SUM of eventCount",A1, "eventName", "session_start") + GETPIVOTDATA("SUM of eventCount",F1, "eventName", "session_start")',
    )
    log.info("Wrote totals to %s" % (page_names[1]))


def create_first_visit_pt(sheets_id, page_id, col_dict):
    first_visit_facebook_pt_def = {
        "pivotTable": {
            "source": {
                # First Sheet (Sheet1) is always ID 0
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["firstUserSource"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "filterSpecs": [
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "first_visit",
                                }
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["eventName"],
                },
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "facebook",
                                },
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["firstUserSource"],
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }
    first_visit_rt_pt_def = {
        "pivotTable": {
            "source": {
                # First Sheet (Sheet1) is always ID 0
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["firstUserSource"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "filterSpecs": [
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "first_visit",
                                }
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["eventName"],
                },
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "rt",
                                },
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["firstUserSource"],
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }

    sheets_client.add_pivot_tables(
        sheets_id,
        page_id,
        first_visit_facebook_pt_def,
    )
    sheets_client.add_pivot_tables(
        sheets_id,
        page_id,
        first_visit_rt_pt_def,
        row_idx=0,
        col_idx=5,
    )


def create_session_start_pt(sheets_id, page_id, col_dict):
    # Add sessions pivot table, facebook
    sessions_facebook_pt_def = {
        "pivotTable": {
            "source": {
                # First Sheet (Sheet1) is always ID 0
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["firstUserSource"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "filterSpecs": [
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "session_start",
                                }
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["eventName"],
                },
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "facebook",
                                },
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["firstUserSource"],
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }
    sessions_rt_pt_def = {
        "pivotTable": {
            "source": {
                # First Sheet (Sheet1) is always ID 0
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["firstUserSource"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "filterSpecs": [
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "session_start",
                                }
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["eventName"],
                },
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "rt",
                                },
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["firstUserSource"],
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }

    sheets_client.add_pivot_tables(sheets_id, page_id, sessions_facebook_pt_def)
    sheets_client.add_pivot_tables(
        sheets_id, page_id, sessions_rt_pt_def, row_idx=0, col_idx=5
    )


def create_clicks_pt(sheets_id, page_id, col_dict):
    clicks_pt_def = {
        "pivotTable": {
            "source": {
                # First Sheet (Sheet1) is always ID 0
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }

    sheets_client.add_pivot_tables(sheets_id, page_id, clicks_pt_def)


def create_feedback_pt(sheets_id, page_id, col_dict):
    feedback_pt_def = {
        "pivotTable": {
            "source": {
                "sheetId": 0,
            },
            "rows": [
                {
                    "sourceColumnOffset": col_dict["eventName"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
                {
                    "sourceColumnOffset": col_dict["eventCount"],
                    "showTotals": True,
                    "sortOrder": "ASCENDING",
                },
            ],
            "filterSpecs": [
                {
                    "filterCriteria": {
                        "condition": {
                            "type": "TEXT_CONTAINS",
                            "values": [
                                {
                                    "userEnteredValue": "feedback",
                                }
                            ],
                        },
                        "visibleByDefault": True,
                    },
                    "columnOffsetIndex": col_dict["linkUrl"],
                },
            ],
            "values": [
                {
                    "summarizeFunction": "SUM",
                    "sourceColumnOffset": col_dict["eventCount"],
                }
            ],
            "valueLayout": "HORIZONTAL",
        }
    }

    sheets_client.add_pivot_tables(sheets_id, page_id, feedback_pt_def)


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
