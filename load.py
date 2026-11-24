#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os 
from dotenv import load_dotenv
import logging

import pandas as pd

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import sqlalchemy as db
from sqlalchemy import inspect, text
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy.dialects.postgresql import insert

from haze.paths import ENV_FILE, get_transformed_parquet_path


# In[ ]:


def insert_ignore_duplicates(pd_table, conn, keys, data_iter):
    """Insert new records and skip duplicate PSI records."""

    # Get the destination PostgreSQL table
    table = pd_table.table

    # Convert each row into a dictionary of column names and values
    records = [
        dict(zip(keys, row))
        for row in data_iter
    ]

    # Nothing to insert if the batch is empty
    if not records:
        return 0

    # Skip records that violate our named unique constraint
    stmt = insert(table).on_conflict_do_nothing(
        constraint="uq_haze_psi_record"
    )

    # Execute the insert using the connection pandas provides
    result = conn.execute(stmt, records)

    return result.rowcount


# In[ ]:


def load_postgres(data_date):
    """
    Load transformed PSI data into PostgreSQL,
    skipping records that already exist.
    """

    # Establish connection and create database.
    load_dotenv(ENV_FILE)

    PG_USERNAME = 'postgres'
    PG_PASSWORD = os.getenv("PG_PASSWORD") # Get your postgresql password from environment
    PG_HOST     = os.getenv("PG_HOST", "localhost") # Get your postgresql host from environment
    PG_PORT     = '5432'
    PG_DB_NAME  = 'haze_psi' #enter your database name

    if not PG_PASSWORD:
        raise ValueError(
            "PostgreSQL password not found in .env.")

    # Read transformed data into a DataFrame
    transformed_parquet_path = get_transformed_parquet_path(data_date)

    df = pd.read_parquet(transformed_parquet_path)

    if df.empty:
        raise ValueError("No data available to load.")

    CONNECTION_STRING = f'postgresql://{PG_USERNAME}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'
    print(f"Connection string: postgresql://{PG_USERNAME}:****@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}")

    engine = db.create_engine(CONNECTION_STRING)

    # load to postgresql
    try:
        if not database_exists(engine.url):
            create_database(engine.url)
            logging.info("Database haze_psi created.")
        else:
            logging.info("Database haze_psi already exists.")

        with engine.begin() as connection:

            # Remove existing records for this date
            connection.execute(
                text("""
                    DELETE FROM haze_psi
                    WHERE "date"::date = :data_date
                """),
                {"data_date": data_date}
            )

            # Insert the complete day's records
            df.to_sql(
                "haze_psi",
                connection,
                index=False,
                if_exists="append",
                method=insert_ignore_duplicates
            )

        logging.info(
            "Loaded %s rows for %s.",
            len(df),
            data_date
        )

    finally:
        engine.dispose()

    return None


# In[ ]:


def get_next_data_dates():
    """
    Returns a list of dates that require its data to be processed.
    """
    load_dotenv(ENV_FILE)

    PG_USERNAME = "postgres"
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    PG_HOST = os.getenv("PG_HOST", "172.20.160.1")
    PG_PORT = "5432"
    PG_DB_NAME = "haze_psi"

    if not PG_PASSWORD:
        raise ValueError("PostgreSQL password not found in .env.")

    CONNECTION_STRING = (
        f"postgresql://{PG_USERNAME}:{PG_PASSWORD}"
        f"@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
    )

    engine = db.create_engine(CONNECTION_STRING)

    # Initial date for historical extraction
    start_date = date(2026, 8, 1)

    # Only process data up to yesterday (Singapore time)
    yesterday = (
        datetime.now(ZoneInfo("Asia/Singapore")).date()
        - timedelta(days=1)
    )

    expected_timestamps = 24
    dates_to_process = []

    try:
        # Check whether the table exists
        if not inspect(engine).has_table("haze_psi"):
            current_date = start_date

            while current_date <= yesterday:
                dates_to_process.append(current_date)
                current_date += timedelta(days=1)

            return dates_to_process

        # Retrieve timestamp counts for each date
        query = text("""
            SELECT
                "date"::date AS data_date,
                COUNT(DISTINCT "timestamp") AS timestamp_count
            FROM haze_psi
            WHERE "date"::date BETWEEN :start_date AND :end_date
            GROUP BY "date"::date
        """)

        with engine.connect() as connection:
            results = connection.execute(
                query,
                {
                    "start_date": start_date,
                    "end_date": yesterday
                }
            ).mappings().all()

        # Convert query results into a dictionary
        date_counts = {
            row["data_date"]: row["timestamp_count"]
            for row in results
        }

        # Find the earliest missing or incomplete date
        current_date = start_date

        while current_date <= yesterday:

            count = date_counts.get(current_date, 0)

            if count != expected_timestamps:
                logging.info(
                    "Data for %s is incomplete. Found %s timestamps.",
                    current_date,
                    count
                )

                dates_to_process.append(current_date)

            current_date += timedelta(days=1)

        logging.info("Found %s dates to process: %s", len(dates_to_process), dates_to_process)

        return dates_to_process

    finally:
        engine.dispose()

