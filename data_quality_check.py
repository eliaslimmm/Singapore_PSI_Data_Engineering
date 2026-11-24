#!/usr/bin/env python
# coding: utf-8

# In[5]:


import pandas as pd
import logging 
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO) 


# In[1]:


def check_future_timestamps(df):
    """
    Checking if any future timestamp exists.
    """
    timestamp_columns = ["timestamp", "updated_timestamp"]

    try:
        current_timestamp = pd.Timestamp.now(tz="Asia/Singapore")

        for col in timestamp_columns:
            timestamps = pd.to_datetime(df[col], utc=False)
            timestamps = timestamps.dt.tz_convert("Asia/Singapore")

            future_count = (timestamps > current_timestamp).sum()

            if future_count == 0:
                logging.info(f"{col} passed, future_count = {future_count}")

            else:
                logging.warning(f"{col} failed, future_count = {future_count}")
                return False

        return True

    except Exception as e:
        logging.error(f"check_future_timestamps failed: {e}")
        raise        


# In[2]:


def check_future_date(df):
    """
    Checking if any future date exists.
    """
    try:
        current_date = pd.Timestamp.now(tz="Asia/Singapore").date()

        dates = pd.to_datetime(df["date"]).dt.date

        future_count = (dates > current_date).sum()

        if future_count == 0:
            logging.info(f"date passed, future_count = {future_count}")

        else:
            logging.warning(f"date failed, future_count = {future_count}")
            return False

        return True

    except Exception as e:
        logging.error(f"check_future_date failed: {e}")
        raise        


# In[ ]:


def negative_check(df):
    """
    Check for negative values.
    """
    try:
        negative_value_count = (df["value"] < 0).sum()
        negative_value_count

        if negative_value_count == 0:
            logging.info(f"value passed, negative_value_count = {negative_value_count}")
            return True

        else:
            logging.warning(f"value failed, negative_value_count = {negative_value_count}")
            return False

    except Exception as e:
        logging.error(f"negative_check failed: {e}")
        raise  


