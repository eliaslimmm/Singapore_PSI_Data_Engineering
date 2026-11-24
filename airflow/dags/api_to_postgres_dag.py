#!/usr/bin/env python
# coding: utf-8

# In[10]:


# %pip install import-ipynb


# In[12]:


import pandas as pd
import sys
from pathlib import Path

PROJECT_PARENT = Path.home() / "airflow-project"
sys.path.insert(0, str(PROJECT_PARENT))

from haze.paths import get_transformed_parquet_path


# In[18]:


from haze.extract import extract_dates
from haze.transform import transform
from haze.data_quality_check import check_future_timestamps, check_future_date, negative_check
from haze.load import load_postgres, get_next_data_dates


# In[ ]:


from datetime import date

from airflow.sdk import dag, task
from airflow.exceptions import AirflowSkipException
from pendulum import datetime


# In[ ]:


@dag(
    dag_id="haze_etl",
    start_date=datetime(2026, 8, 1, tz="Asia/Singapore"),
    schedule="0 11 * * *",
    catchup=False,
    max_active_runs=1
)

def haze_etl():

    @task
    def get_data_dates():
        data_dates = get_next_data_dates()

        if not data_dates:
            raise AirflowSkipException(
                "No incomplete dates found. Nothing to process."
            )

        # Convert dates into strings for Airflow XCom
        return [data_date.isoformat() for data_date in data_dates]

    @task
    def extract_task(data_dates):        
        dates = [
            date.fromisoformat(data_date)
            for data_date in data_dates
        ]

        extract_dates(dates)

        return data_dates

    @task
    def transform_task(data_dates):
        for data_date in data_dates:
            transform(date.fromisoformat(data_date))

        return data_dates

    @task
    def data_quality_task(data_dates):
        for data_date in data_dates:
            data_date = date.fromisoformat(data_date)

            # Read the Parquet file into a DataFrame
            parquet_path = get_transformed_parquet_path(data_date)
            df = pd.read_parquet(parquet_path)

            if df.empty:
                raise ValueError(f"Data quality check failed for {data_date}: empty DataFrame.")

            if not check_future_timestamps(df):
                raise ValueError(f"Future timestamp check failed for {data_date}")

            if not check_future_date(df):
                raise ValueError(f"Future date check failed for {data_date}")

            if not negative_check(df):
                raise ValueError(f"Negative value check failed for {data_date}")

        return data_dates

    @task
    def load_task(data_dates):
        for data_date in data_dates:
            load_postgres(date.fromisoformat(data_date))

    # Calculate the data date once
    data_dates = get_data_dates()

    # Pass the same date to all tasks
    extracted_dates = extract_task(data_dates)
    transformed_dates = transform_task(extracted_dates)
    checked_dates = data_quality_task(transformed_dates)
    load_task(checked_dates)

haze_etl() 


# In[ ]:




