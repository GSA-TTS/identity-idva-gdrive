import logging
import pandas as pd
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build

from gdrive import settings, error

log = logging.getLogger(__name__)

creds = service_account.Credentials.from_service_account_info(
    settings.CREDENTIALS, scopes=settings.SCOPES
)

sheets_service = build("sheets", "v4", credentials=creds)

"""
At present, every function call in this library represents its own API
transaction. If a lot of operations were to be made at once, this would hinder speed
quite a bit. 

Some batching in the future if the use case for this library gets heavier is necessary. 
"""

# Generic functions


def update_cell_value(
    sheet_id: str, page_name: str, range_str: str, value: str, vio="USER_ENTERED"
):
    """
    Write the specifed value to specified range

    Args:
        sheet_id (str): Google sheets object ID
        page_name (str): page target to edit
        range_str (str): range to write the values to
        value (str): value to write to the specified location
        vio (str):
            default (str): "USER_ENTERED" User entered values get resolved by googles parsing function.
                            Functions, Integers and strings can all be entered this way.

    Returns:
        Google API Raw Result
    """
    body = {
        "values": [
            # Cell values
            [
                value,
            ]
            # Other values
        ]
    }

    result = (
        sheets_service.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheet_id,
            range="%s!%s" % (page_name, range_str),
            valueInputOption=vio,
            body=body,
        )
        .execute()
    )

    return result


def add_pivot_tables(
    sheets_id: str,
    target_page_id: str,
    pivot_table_definition: object,
    row_idx: int = 0,
    col_idx: int = 0,
):
    """
    Writes the pivot table definition to the specified location.

    Args:
        sheets_id (str): ID for the sheets object
        target_page_id (str): ID for the target page of the sheets object, (Sheet1 is always 0)
        pivot_table_definition (object): JSON encoded dict
        row_idx (int): Index of the row to write the start of the table
            default: 0
        col_idx (int): Index of the column to write the start of the table
            default: 0

    Returns:
        Google Sheets API Response: RAW response to the write operation
    """
    requests = []
    requests.append(
        {
            "updateCells": {
                "rows": {
                    # I would need to write a whole library to parameterize this well so
                    # Client Code will just need to pass the JSON definitions in.
                    "values": pivot_table_definition
                },
                "start": {
                    "sheetId": target_page_id,
                    "rowIndex": row_idx,
                    "columnIndex": col_idx,
                },
                "fields": "pivotTable",
            }
        }
    )

    body = {"requests": requests}

    response = (
        sheets_service.spreadsheets()
        .batchUpdate(spreadsheetId=sheets_id, body=body)
        .execute()
    )

    return response


def add_new_pages(page_names: [str], sheets_id: str):
    new_sheets_reqs = []
    for label in page_names:
        req = {
            "addSheet": {
                "properties": {
                    "title": label,
                }
            }
        }

        new_sheets_reqs.append(req)

    body = {"requests": new_sheets_reqs}

    result = (
        sheets_service.spreadsheets()
        .batchUpdate(
            spreadsheetId=sheets_id,
            body=body,
        )
        .execute()
    )

    sheet_title_to_id = {}
    for reply in result.get("replies"):
        props = reply.get("addSheet").get("properties")
        sheet_title_to_id[props.get("title")] = props.get("sheetId")

    return sheet_title_to_id


def export_df_to_gdrive_speadsheet(df: pd.DataFrame, sheets_id: str, title="Sheet1"):
    """
    Exports an entire pandas dataframe to a Google Sheets Object.

    Args:
        df (pandas.DataFrame): Tabular data to be exported to a spreadsheet
        title (str): Title for the target spreadsheet to write the data to.
            default: "Sheet1" default value for new Google Sheets sheets object

    Returns:
        Google Sheets API Response: RAW response to the write operation
    """
    body = {"values": df.values.tolist()}
    result = (
        sheets_service.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheets_id,
            range="%s!A1" % (title),
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    if "error" in result:
        raise error.ExportError(result["error"]["message"])

    return result


# Project specific functions


def do_create_pivot_tables(
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

    update_cell_value(sheets_id, page_names[0], "A17", "Total First Visits")
    update_cell_value(
        sheets_id,
        page_names[0],
        "A18",
        '=GETPIVOTDATA("SUM of eventCount",A1, "eventName", "first_visit") + GETPIVOTDATA("SUM of eventCount",F1, "eventName", "first_visit")',
    )
    log.info("Wrote totals to %s" % (page_names[0]))

    update_cell_value(sheets_id, page_names[1], "A17", "Total Sessions")
    update_cell_value(
        sheets_id,
        page_names[1],
        "A18",
        '=GETPIVOTDATA("SUM of eventCount",A1, "eventName", "session_start") + GETPIVOTDATA("SUM of eventCount",F1, "eventName", "session_start")',
    )
    log.info("Wrote totals to %s" % (page_names[1]))


def create_first_visit_pt(sheets_id, page_id, col_dict):
    # Add first visit pivot table, Facebook
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
    )
    # Add first visit pivot table, RT
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
        row_idx=0,
        col_idx=5,
    )


def create_session_start_pt(sheets_id, page_id, col_dict):
    # Add sessions pivot table, facebook
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
    )
    # Add sessions pivot table, rt
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
        row_idx=0,
        col_idx=5,
    )


def create_clicks_pt(sheets_id, page_id, col_dict):
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
    )


def create_feedback_pt(sheets_id, page_id, col_dict):
    add_pivot_tables(
        sheets_id,
        page_id,
        (
            {
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
        ),
    )


def upload_participant(
    first,
    last,
    email,
    responseId,
    time,
    date,
    ethnicity,
    race,
    gender,
    age,
    income,
    skin_tone,
):
    """
    Append participant data to the rekrewt raw completions spreadsheet
    """
    values = [
        [
            first,
            last,
            first + " " + last,
            email,
            responseId,
            time,
            date,
            ethnicity,
            race,
            gender,
            income,
            skin_tone,
        ]
    ]

    body = {"values": values}
    result = (
        sheets_service.spreadsheets()
        .values()
        .append(
            spreadsheetId=settings.SHEETS_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    if "error" in result:
        raise error.ExportError(result["error"]["message"])
    return result
