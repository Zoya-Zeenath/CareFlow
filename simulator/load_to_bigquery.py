"""
CareFlow - Step 2: load the raw EHR event log into BigQuery.

Run from D:\\careflow\\simulator:
    python load_to_bigquery.py
"""
import os

import pandas as pd
from google.cloud import bigquery

KEY_PATH = r"D:\secrets\gcp-key.json"          # key lives OUTSIDE the repo
CSV_PATH = r"D:\careflow\data\ehr_events_raw.csv"

PROJECT_ID = "careflow-511009"
DATASET = "careflow_raw"
TABLE = "ehr_events_raw"
# ------------------------------------------------------------------------

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
print(f"Read {len(df):,} rows from {CSV_PATH}")

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",  # re-running replaces the table
    schema=[
        bigquery.SchemaField("case_id", "STRING"),
        bigquery.SchemaField("activity", "STRING"),
        bigquery.SchemaField("lifecycle", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("resource", "STRING"),
        bigquery.SchemaField("severity", "INTEGER"),
        bigquery.SchemaField("age_group", "STRING"),
        bigquery.SchemaField("gender", "STRING"),
    ],
)

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()  # wait until the upload finishes

table = client.get_table(table_id)
print(f"Loaded {table.num_rows:,} rows into {table_id}")
