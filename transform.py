#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import logging

import pandas as pd

from haze.paths import get_raw_json_path, get_transformed_parquet_path


# In[1]:


def transform(data_date):
    """
    Transform extracted json data.

    Arg: data = json data from extract()
    """

    raw_json_path = get_raw_json_path(data_date)

    # Read the raw API response
    with raw_json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    items = data["data"]["items"]

    rows = []

    for item in items:
        timestamp = item["timestamp"]
        date = item["date"]
        updated_timestamp = item["updatedTimestamp"]

        for metric, regional_values in item["readings"].items():
            for region, value in regional_values.items():
                rows.append({
                    "timestamp": timestamp,
                    "date": date,
                    "updated_timestamp": updated_timestamp,
                    "metric": metric,
                    "region": region,
                    "value": value
                })

    # Create the DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("Transformation produced an empty DataFrame.")

    # Convert timestamp fields into proper datetime types
    for col in ["timestamp", "date", "updated_timestamp"]:
        df[col] = pd.to_datetime(df[col])

    # Save the transformed DataFrame
    transformed_parquet_path = get_transformed_parquet_path(data_date)

    df.to_parquet(
        transformed_parquet_path,
        index=False)

    logging.info("Transformed data saved to %s", transformed_parquet_path)
    logging.info("DataFrame shape: %s", df.shape)

    return None

