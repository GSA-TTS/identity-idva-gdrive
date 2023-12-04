import json
from typing import List
from opensearchpy import OpenSearch
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread


# Access to Prod GDrive
service_account_info = json.load(open('prj-p-tts-idva-equity-prod.json'))
creds = service_account.Credentials.from_service_account_info(
    service_account_info)
service = build("drive", "v3", credentials=creds)


def main():
    # -----------------------------------------
    # This is what will run
    # -----------------------------------------

    # change dates/time to desired search ignore the last 50 minutes
    # so you are sure to only record finished flows
    # could make a chron job if you save the time last ran and set as start

    endTime = '2023-12-05T00:00:00'
    startTime = '2023-12-04T17:35:37'
    print("--------------------------------------------------------")
    print("Flows from " + startTime + " to " + endTime)
    print("--------------------------------------------------------")

    list = query_opensearch(endTime, startTime)
    process_query(list)


def query_opensearch(endTime, startTime):
    # -----------------------------------------
    # Returns list of parent flows given times
    # -----------------------------------------
    es = OpenSearch(
        hosts=[{"host": 'localhost', "port": 4343}], timeout=300
    )

    query_flows = {
        # size note: use 500 at least per day to be safe
        "size": 500,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"properties.outcomeType.value": "survey_data"}},
                    {"range": {"tsEms": {
                        "gte": startTime,
                        "lt": endTime
                    }}
                    },
                ]
            },

        },
        "sort": {"tsEms": {"order": "asc"}},
    }

    output = []

    flows = es.search(body=json.dumps(query_flows), index="_all")

    for hit in flows["hits"]["hits"]:
        if hit["_source"].get("capabilityName") == "logOutcome":
            output.append(hit["_source"])

    return output


def process_query(results):
    # -----------------------------------------------------
    # Processes list of parent flows and writes to sheet
    # -----------------------------------------------------
    counter = 0
    worksheet = getWorksheet()
    allInteractionIdsInSheet = getWorksheetInteractionIds(worksheet)

    for r in results:
        interactionId = r["interactionId"]
        tsEms = r["tsEms"]
        flowId = r["flowId"]
        #  Anbu: TODO update this when we promote flows
        if flowId == '45925e1294e607f3cc12c73376545054':
            flowId = 'v1.0.56'
        surveyData = json.loads(r["properties"]["outcomeDescription"]["value"])
        responseId = surveyData["responseId"]

        # if the interaction doesnt exist already in the sheet
        # and the file is found in the gdrive write row on sheet
        if interactionId in allInteractionIdsInSheet:
            print(tsEms + " - " + interactionId + " already exists")
        else:
            counter = write_to_google_sheet(
                worksheet, interactionId, tsEms, flowId, responseId, counter)

    print("-------------------------------------------------")
    print("New Lines:" + str(counter))
    print("Overlap:" + str(len(results)-counter))
    print("-------------------------------------------------")


# --------------------------------------------------------------------
# Opensearch Query Helper Fuctions
# --------------------------------------------------------------------


def get_all_subflow_ids(parentInteractionId):
    # --------------------------------------------------------------------
    # get all subflow interactionIds associated with parent interactionId
    # --------------------------------------------------------------------
    es = OpenSearch(
        hosts=[{"host": 'localhost', "port": 4343}], timeout=300
    )

    subflowquery = {
        "size": 500,
        "query": {
            "bool": {
                "should": [
                    {
                        'bool': {
                            'must': [
                                {'match_phrase': {'parentInteractionProps.parentInteractionId':
                                                  parentInteractionId}},
                                {'exists': {'field': 'interactionId'}}
                            ]
                        }
                    },
                    {
                        'bool': {
                            'must': [
                                {'match_phrase': {
                                    'properties.outcomeDescription.value': parentInteractionId}},
                                {'match_phrase': {
                                    'properties.outcomeType.value': 'parent_id'}}
                            ]
                        }
                    }
                ]
            }
        },
        "_source": ["interactionId"],
    }

    subs = es.search(body=json.dumps(subflowquery), index="_all")

    sub_interactionIds_match = list(
        map(
            lambda res: res["_source"]["interactionId"],
            subs["hits"]["hits"],
        )
    )
    return sub_interactionIds_match


def find(interactionId, field, values, result):
    # --------------------------------------------------------------------
    # find values in find for all subflows and parent flow
    # field and result should be one of:
    #   properties.outcomeDescription.value
    #   properties.outcomeStatus.value
    #   properties.outcomeType.value
    #   properties.outcomeDetail.value
    # --------------------------------------------------------------------

    es = OpenSearch(
        hosts=[{"host": 'localhost', "port": 4343}], timeout=300
    )

    all_interactionIds = get_all_subflow_ids(interactionId)
    all_interactionIds.append(interactionId)

    if len(all_interactionIds) == 0:
        return {"found": []}

    all_interactionIds_match = list(
        map(lambda res: {"match": {"interactionId": f"{res}"}},
            all_interactionIds)
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
        "_source": [result],
    }

    found_result = es.search(body=json.dumps(query_found), index="_all")

    list_found = list(
        map(
            lambda x: recursive_decent(x["_source"], result.split(".")),
            found_result["hits"]["hits"],
        )
    )

    return list_found


def recursive_decent(obj: dict | str, query: list[str]):
    # given dict and a dot notated key name, return value of key
    if query == [] or not isinstance(obj, dict):
        return obj
    return recursive_decent(obj.get(query[0], ""), query[1:])


def list_completed_checks(interactionId):
    # -----------------------------------------------------
    # Query for checks completed
    # -----------------------------------------------------
    found = find(interactionId, 'properties.outcomeType.value', ["lexisnexis_device_risk", "socure_document_authentication", "lexisnexis_document_authentication", "authenticid_document_authentication",
                 "incode_document_authentication", "jumio_document_authentication", "lexisnexis_pii", "redviolet_pii", "socure_pii", "lexisnexis_securitycode", "verification"], 'properties.outcomeType.value')
    return found


# --------------------------------------------------------------------
#
# Googlesheet Helper Fuctions
#
# --------------------------------------------------------------------


def write_to_google_sheet(worksheet, interactionId, tsEms, flowId, responseId, counter):
    # -----------------------------------------------------
    # If folder in GDrive writes row to sheet
    # -----------------------------------------------------
    row = next_available_row(worksheet)
    cell = 'A' + row + ":J" + row
    date = tsEms.split('T')
    link = get_gdrive_link(interactionId)
    checks = get_checks(interactionId)
    if link != 'file not found':
        print(tsEms + " - " + interactionId + " ADDED!")
        worksheet.update(range_name=cell, values=[
                         [date[0], '', link, flowId, interactionId, None, checks, '', '', responseId]])
        counter += 1
    else:
        print(interactionId + ' file not found')
    return counter


def getWorksheet():
    gc = gspread.service_account(filename='prj-p-tts-idva-equity-prod.json')
    spread_sheet = gc.open_by_key(
        '1eQ1wWwxNuAgUl1wSVkDN7dcD2Wi1nDtbrvpMgsLmuuA')
    worksheet = spread_sheet.worksheet('fill_w_script')
    return worksheet


def getWorksheetInteractionIds(worksheet):
    # ---------------------------------------------------
    # checks for interaction Id in 5th column
    # ---------------------------------------------------
    worksheet.col_values(5)
    return [item for item in worksheet.col_values(5) if item]


def next_available_row(worksheet):
    # ---------------------------------------------------
    # gets next empty row to populate
    # ---------------------------------------------------
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)


def get_gdrive_link(interactionId):
    # -----------------------------------------------------
    # get link from gdrive
    # -----------------------------------------------------
    link = generate_link(interactionId)
    return link


def generate_link(filename: str):
    # ---------------------------------------------------
    # generates sharable link for folder given name
    # ---------------------------------------------------
    file = get_files(filename)
    if file:
        link = 'https://drive.google.com/drive/folders/' + \
            file[0]['id'] + '?usp=share_link'
    else:
        link = 'file not found'
    return link


def get_files(filename: str) -> List:
    # ---------------------------------------------------
    # checks for file name in GDrive
    # ---------------------------------------------------
    results = (
        service.files()
        .list(
            q=f"name = '{filename}'",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    return results["files"]


def get_checks(interactionId):
    # -----------------------------------------------------
    # Get the checks in order
    # -----------------------------------------------------
    found = list_completed_checks(interactionId)
    # order the checks
    allChecks = ["lexisnexis_device_risk", "socure_document_authentication", "lexisnexis_document_authentication", "authenticid_document_authentication",
                 "incode_document_authentication", "jumio_document_authentication", "lexisnexis_pii", "redviolet_pii", "socure_pii", "lexisnexis_securitycode", "verification"]
    foundChecks = set(found)
    foundChecksOrdered = [x for x in allChecks if x in foundChecks]
    # abbreviate the checks
    foundChecksOrdered = abbreviate_checks(foundChecksOrdered)
    foundStr = " ".join(str(x) for x in foundChecksOrdered)
    return foundStr


def abbreviate_checks(my_list):
    # -----------------------------------------------------
    # Abbreviates the checks
    # -----------------------------------------------------
    my_dict = {"device": "lexisnexis_device_risk", "B": "socure_document_authentication", "H": "lexisnexis_document_authentication", "W": "authenticid_document_authentication",
               "M": "incode_document_authentication", "D": "jumio_document_authentication", "H_pii": "lexisnexis_pii", "redviolet_pii": "redviolet_pii", "B_pii": "socure_pii", "OTP": "lexisnexis_securitycode", "verification": "verification"}
    for key, value in my_dict.items():
        if value not in my_list:
            continue
        index = my_list.index(value)
        my_list[index] = key
    return my_list


def formatDateTime(formatDate):
    a = str(formatDate)
    b = a.split(".")
    return b[0].replace(" ", "T")


if __name__ == '__main__':
    main()
