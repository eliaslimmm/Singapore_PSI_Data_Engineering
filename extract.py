#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# %pip install python-dotenv


# In[ ]:


import os
import json
import logging
import requests
import time

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from haze.paths import ENV_FILE, get_raw_json_path


# In[ ]:


def extract(data_date):
    """
    Extract data from data.gov.sg via REST API.
    """
    load_dotenv(ENV_FILE)

    API_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"

    # Get api key from environment
    data_gov__key = os.getenv("api_key")
    headers = {"x-api-key": data_gov__key}

    if not data_gov__key:
        raise ValueError("API key not found. Check your environment variable.")

    # Send request to API
    response = requests.get(
        API_URL,
        headers=headers,
        params={"date" : data_date.isoformat()},
        timeout=30
    )

    # Check status
    status = response.status_code
    emoji = "✅" if status == 200 else "❌"
    print(f"{emoji} Status code: {status}")

    if status != 200:
        print("   Request did not succeed. Check the URL and try again.")
        response.raise_for_status()

    # Check reponse object type
    print(f"Response type    : {type(response)}")

    # Content type from headers
    print(f"Content-Type     : {response.headers.get('Content-Type', 'N/A')}")

    # Convert JSON response to Python dictionary
    # .json() automatically decodes the JSON text to a Python dict
    raw_data = response.json()

    print(f"Type of data       : {type(raw_data)}")
    print(f"Top-level keys     : {list(raw_data.keys())}")

    # Inspect the nested structure
    # This API uses 'data' as the key containing records
    # Recall the dictionary get() method returns the value of the item with the specified key.
    print(f"Number of records  : {len(raw_data.get('data', []))}") 
    print()

    # Preview first record
    items = raw_data.get("data", {}).get("items", [])

    if not items:
        raise ValueError(f"No PSI data returned for {data_date}.")

    # Log a warning if the record is less than 24 for a particular date.
    if len(items) < 24:
        logging.warning("Expected 24 timestamps for %s, but received %s.", data_date, len(items))

    else:
        print("First record (formatted):")
        print(json.dumps(raw_data['data']['items'][0], indent=2))

    # Save raw JSON
    raw_json_path = get_raw_json_path(data_date)

    # json.dumps() method can convert a Python object into a JSON string.
    with raw_json_path.open("w", encoding="utf-8") as file:
        json.dump(raw_data, file, indent=2)

    logging.info("Extracted %s timestamp records for %s", len(items), data_date)

    return None


# In[ ]:


def extract_dates(data_dates):
    """
    Extract PSI data for multiple dates sequentially.
    """

    for index, data_date in enumerate(data_dates):

        extract(data_date)

        # Pause before sending the next API request
        if index < len(data_dates) - 1:
            logging.info("Waiting 2 seconds before next API request...")
            time.sleep(2)

    return data_dates


# def extract_historic_data():
#     """
#     Extract PSI data from 1 August 2026 up to the current date.
#     Combine all daily API responses into one JSON file.
#     """
# 
#     load_dotenv(ENV_FILE)
# 
#     API_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
# 
#     # Get api key from environment
#     data_gov__key = os.getenv("api_key")
#     headers = {"x-api-key": data_gov__key}
#     
#     if not data_gov__key:
#         raise ValueError("API key not found. Check your environment variable.")
#     
#     start_date = date(2026, 8, 1)
#     current_date = datetime.now(ZoneInfo("Asia/Singapore")).date()
# 
#     all_items = []
#     combined_payload = None
# 
#     while start_date <= current_date:
# 
#         date_string = start_date.strftime("%Y-%m-%d")
# 
#         logging.info("Extracting PSI data for %s", date_string)
# 
#         response = requests.get(
#             API_URL,
#             headers=headers,
#             params={"date": date_string},
#             timeout=30
#         )
# 
#         if response.status_code == 429:
#             logging.warning("Rate limit reached. Waiting 5 seconds...")
#             time.sleep(5)
#         
#             response = requests.get(
#                 API_URL,
#                 headers=headers,
#                 params={"date": date_string},
#                 timeout=30
#             )
# 
#         response.raise_for_status()
# 
#         time.sleep(2)
# 
#         daily_data = response.json()
# 
#         if "data" not in daily_data:
#             raise ValueError(
#                 f"Unexpected API response for {date_string}"
#             )
# 
#         # Preserve the original API response structure.
#         if combined_payload is None:
#             combined_payload = daily_data.copy()
#             combined_payload["data"] = daily_data["data"].copy()
# 
#         # Collect the readings from this date.
#         daily_items = daily_data["data"].get("items", [])
# 
#         all_items.extend(daily_items)
# 
#         logging.info(
#             "Extracted %s records for %s",
#             len(daily_items),
#             date_string
#         )
# 
#         start_date += timedelta(days=1)
# 
#     # Replace the first day's items with all collected items.
#     combined_payload["data"]["items"] = all_items
# 
#     # Save everything into one JSON file.
#     with open(RAW_JSON_PATH, "w") as file:
#         json.dump(combined_payload, file, indent=4)
# 
#     logging.info(
#         "Extraction completed. Total records collected: %s",
#         len(all_items)
#     )
# 
#     return None

# In[ ]:




