# Databricks notebook source
"""CAT pipeline monitoring checks and operational summaries."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType, TimestampType


SCHEMA = "regtech_ops_stg"
TABLE_PREFIX = "bi_output_regtechops_"
BASE_LOCATION = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"

REGISTRY_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_file_registry"
META_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_meta_feedback"
ENRICHED_ERRORS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_enriched_errors"
TRADE_STATUS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_trade_status"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_process_log"


def widget_value(name: str, default: str) -> str:
    try:
        dbutils.widgets.text(name, default)
        value = dbutils.widgets.get(name)
        return value if value not in (None, "") else default
    except Exception:
        return default


FAIL_ON_FAILED_FILES = widget_value("fail_on_failed_files", "false").lower() == "true"
FAIL_ON_UNKNOWN_ERROR_CODES = widget_value("fail_on_unknown_error_codes", "false").lower() == "true"


def current_run_id() -> Optional[str]:
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        run_id = context.currentRunId()
        return str(run_id.get()) if run_id.isDefined() else None
    except Exception:
        return None


RUN_ID = current_run_id()


def ensure_process_log() -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {PROCESS_LOG_TABLE} (
          process_log_id STRING NOT NULL,
          job_run_id STRING,
          task_name STRING NOT NULL,
          file_key STRING,
          source_file_name STRING,
          status STRING NOT NULL,
          started_ts TIMESTAMP NOT NULL,
          completed_ts TIMESTAMP,
          records_read BIGINT,
          records_written BIGINT,
          message STRING,
          exception_class STRING,
          error_message STRING,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_process_log'
        """
    )


def process_log(
    status: str,
    started_ts: datetime,
    records_read: Optional[int] = None,
    message: Optional[str] = None,
    exception_class: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    completed_ts = datetime.now(timezone.utc)
    process_log_id = hashlib.sha256(
        "||".join([str(RUN_ID), "03_monitoring", status, started_ts.isoformat(), completed_ts.isoformat()]).encode(
            "utf-8"
        )
    ).hexdigest()
    schema = StructType(
        [
            StructField("process_log_id", StringType(), False),
            StructField("job_run_id", StringType(), True),
            StructField("task_name", StringType(), False),
            StructField("file_key", StringType(), True),
            StructField("source_file_name", StringType(), True),
            StructField("status", StringType(), False),
            StructField("started_ts", TimestampType(), False),
            StructField("completed_ts", TimestampType(), True),
            StructField("records_read", LongType(), True),
            StructField("records_written", LongType(), True),
            StructField("message", StringType(), True),
            StructField("exception_class", StringType(), True),
            StructField("error_message", StringType(), True),
            StructField("created_ts", TimestampType(), False),
            StructField("updated_ts", TimestampType(), False),
        ]
    )
    row = [
        (
            process_log_id,
            RUN_ID,
            "03_monitoring",
            None,
            None,
            status,
            started_ts,
            completed_ts,
            records_read,
            None,
            message,
            exception_class,
            error_message,
            completed_ts,
            completed_ts,
        )
    ]
    spark.createDataFrame(row, schema).write.format("delta").mode("append").saveAsTable(PROCESS_LOG_TABLE)


ensure_process_log()
run_started = datetime.now(timezone.utc)

file_lifecycle_summary = (
    spark.table(REGISTRY_TABLE)
    .groupBy("file_type", "status")
    .agg(F.count("*").alias("file_count"), F.max("updated_ts").alias("last_update_ts"))
    .orderBy("file_type", "status")
)

meta_feedback_summary = (
    spark.table(META_TABLE)
    .groupBy("trade_date", "stage", "status", "severity")
    .agg(
        F.count("*").alias("feedback_rows"),
        F.sum(F.coalesce(F.col("error_count"), F.lit(0))).alias("error_count"),
        F.sum(F.coalesce(F.col("total_records_count"), F.lit(0))).alias("total_records_count"),
        F.max("updated_ts").alias("last_update_ts"),
    )
    .orderBy(F.col("trade_date").desc_nulls_last(), "stage", "status")
)

trade_status_summary = (
    spark.table(TRADE_STATUS_TABLE)
    .groupBy("trade_date", "event_type", "status")
    .agg(F.count("*").alias("record_count"), F.max("updated_ts").alias("last_update_ts"))
    .orderBy(F.col("trade_date").desc_nulls_last(), "event_type", "status")
)

unknown_error_codes = (
    spark.table(ENRICHED_ERRORS_TABLE)
    .where(F.col("error_description") == "UNKNOWN_ERROR_CODE")
    .groupBy("error_code", "error_file_type", "trade_date")
    .agg(F.count("*").alias("error_rows"), F.max("updated_ts").alias("last_seen_ts"))
    .orderBy(F.col("last_seen_ts").desc())
)

failed_files = (
    spark.table(REGISTRY_TABLE)
    .where(F.col("status") == "FAILED")
    .select("file_key", "file_name", "file_type", "trade_date", "error_message", "updated_ts")
    .orderBy(F.col("updated_ts").desc())
)

display(file_lifecycle_summary)
display(meta_feedback_summary)
display(trade_status_summary)
display(unknown_error_codes)
display(failed_files)

unknown_count = unknown_error_codes.count()
failed_count = failed_files.count()
message = f"Monitoring completed. failed_files={failed_count}; unknown_error_codes={unknown_count}."

if (FAIL_ON_FAILED_FILES and failed_count > 0) or (FAIL_ON_UNKNOWN_ERROR_CODES and unknown_count > 0):
    process_log("FAILED", run_started, records_read=failed_count + unknown_count, message=message)
    raise RuntimeError(message)

process_log("SUCCESS", run_started, records_read=failed_count + unknown_count, message=message)
