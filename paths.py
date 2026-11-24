#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path

PROJECT_ROOT = Path.home() / "airflow-project" / "haze"
DATA_DIR = PROJECT_ROOT / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = PROJECT_ROOT / ".env"


# In[ ]:


def get_raw_json_path(data_date):
    date_string = data_date.strftime("%Y-%m-%d")
    return DATA_DIR / f"raw_psi_{date_string}.json"


# In[ ]:


def get_transformed_parquet_path(data_date):
    date_string = data_date.strftime("%Y-%m-%d")
    return DATA_DIR / f"transformed_psi_{date_string}.parquet"

