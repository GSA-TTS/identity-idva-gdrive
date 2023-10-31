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
    pt_def: object,
    row_idx: int = 0,
    col_idx: int = 0,
):
    """
    Writes the pivot table definition to the specified location.

    Args:
        sheets_id (str): ID for the sheets object
        target_page_id (str): ID for the target page of the sheets object, (Sheet1 is always 0)
        pt_def (object): JSON encoded dict
        row_idx (int): Index of the row to write the start of the table
            default: 0
        col_idx (int): Index of the column to write the start of the table
            default: 0

    Returns:
        Google Sheets API Response: RAW response to the write operation
    """
    requests = [
        {
            "updateCells": {
                "rows": {
                    # I would need to write a whole library to parameterize this well so
                    # Client Code will just need to pass the JSON definitions in.
                    "values": pt_def
                },
                "start": {
                    "sheetId": target_page_id,
                    "rowIndex": row_idx,
                    "columnIndex": col_idx,
                },
                "fields": "pivotTable",
            }
        }
    ]

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
