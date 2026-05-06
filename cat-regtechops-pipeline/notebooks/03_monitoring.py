# Databricks notebook source
import json
import uuid
from datetime import datetime

from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


# COMMAND ----------
SCHEMA = "regtech_ops_stg"
TABLE_FILE_REGISTRY = "bi_output_regtechops_cat_file_registry"
TABLE_ENRICHED_ERRORS = "bi_output_regtechops_cat_enriched_errors"
TABLE_TRADE_STATUS = "bi_output_regtechops_cat_trade_status"
TABLE_PROCESS_LOG = "bi_output_regtechops_cat_process_log"

FILE_REGISTRY_TABLE = f"{SCHEMA}.{TABLE_FILE_REGISTRY}"
ENRICHED_ERRORS_TABLE = f"{SCHEMA}.{TABLE_ENRICHED_ERRORS}"
TRADE_STATUS_TABLE = f"{SCHEMA}.{TABLE_TRADE_STATUS}"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PROCESS_LOG}"

RUN_ID = str(uuid.uuid4())


# COMMAND ----------
def write_process_log(
    status: str,
    records_read: int,
    records_written: int,
    details: dict,
    error_message: str = None,
) -> None:
    now = datetime.utcnow()
    payload = [
        (
            str(uuid.uuid4()),
            "03_monitoring",
            RUN_ID,
            now,
            status,
            int(records_read),
            int(records_written),
            json.dumps(details, sort_keys=True),
            error_message,
            now,
            now,
        )
    ]
    schema = StructType(
        [
            StructField("process_log_id", StringType(), False),
            StructField("process_name", StringType(), False),
            StructField("run_id", StringType(), False),
            StructField("batch_ts", TimestampType(), False),
            StructField("status", StringType(), False),
            StructField("records_read", LongType(), False),
            StructField("records_written", LongType(), False),
            StructField("details", StringType(), True),
            StructField("error_message", StringType(), True),
            StructField("created_ts", TimestampType(), False),
            StructField("updated_ts", TimestampType(), False),
        ]
    )
    spark.createDataFrame(payload, schema=schema).write.mode("append").saveAsTable(
        PROCESS_LOG_TABLE
    )


def ensure_tables_exist() -> None:
    required = [
        TABLE_FILE_REGISTRY,
        TABLE_ENRICHED_ERRORS,
        TABLE_TRADE_STATUS,
        TABLE_PROCESS_LOG,
    ]
    missing = [
        table_name
        for table_name in required
        if not spark.catalog.tableExists(f"{SCHEMA}.{table_name}")
    ]
    if missing:
        raise RuntimeError(
            f"Missing required tables for monitoring: {', '.join(missing)}. "
            "Run sql/create_tables.sql before running this notebook."
        )


# COMMAND ----------
ensure_tables_exist()

pipeline_health_df = spark.sql(
    f"""
    SELECT
      date_trunc('hour', updated_ts) AS pipeline_hour,
      file_type,
      lifecycle_status,
      parse_status,
      enrich_status,
      COUNT(*) AS file_count,
      MAX(updated_ts) AS last_updated_ts
    FROM {FILE_REGISTRY_TABLE}
    GROUP BY
      date_trunc('hour', updated_ts),
      file_type,
      lifecycle_status,
      parse_status,
      enrich_status
    ORDER BY pipeline_hour DESC, file_type
    """
)

unknown_errors_df = spark.sql(
    f"""
    SELECT
      trade_date,
      source_file_name,
      error_code,
      COUNT(*) AS unknown_error_count,
      MAX(updated_ts) AS last_seen_ts
    FROM {ENRICHED_ERRORS_TABLE}
    WHERE error_description = 'UNKNOWN_ERROR_CODE'
    GROUP BY trade_date, source_file_name, error_code
    ORDER BY last_seen_ts DESC
    """
)

trade_status_summary_df = spark.sql(
    f"""
    SELECT
      trade_date,
      event_type,
      status,
      COUNT(*) AS trade_count
    FROM {TRADE_STATUS_TABLE}
    GROUP BY trade_date, event_type, status
    ORDER BY trade_date DESC, event_type, status
    """
)

stuck_processing_df = spark.sql(
    f"""
    SELECT
      file_name,
      file_type,
      lifecycle_status,
      parse_status,
      enrich_status,
      updated_ts
    FROM {FILE_REGISTRY_TABLE}
    WHERE (
      lifecycle_status = 'PROCESSING'
      OR parse_status = 'PROCESSING'
      OR enrich_status = 'PROCESSING'
    )
      AND updated_ts < current_timestamp() - INTERVAL 2 HOURS
    ORDER BY updated_ts ASC
    """
)

display(pipeline_health_df)
display(unknown_errors_df)
display(trade_status_summary_df)
display(stuck_processing_df)

unknown_error_count = unknown_errors_df.agg(
    F.coalesce(F.sum("unknown_error_count"), F.lit(0)).alias("cnt")
).collect()[0]["cnt"]
stuck_processing_count = stuck_processing_df.count()

status = "SUCCESS" if stuck_processing_count == 0 else "FAILED"
error_message = (
    None
    if stuck_processing_count == 0
    else f"{stuck_processing_count} file(s) stuck in PROCESSING status for >2 hours."
)

write_process_log(
    status=status,
    records_read=pipeline_health_df.count(),
    records_written=0,
    details={
        "unknown_error_count": str(unknown_error_count),
        "stuck_processing_count": str(stuck_processing_count),
    },
    error_message=error_message,
)

if stuck_processing_count > 0:
    raise RuntimeError(error_message)
