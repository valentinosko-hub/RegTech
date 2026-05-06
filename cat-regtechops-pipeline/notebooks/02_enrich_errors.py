# Databricks notebook source
"""CAT error enrichment and trade-status reconciliation."""

from __future__ import annotations

import hashlib
import traceback
from datetime import datetime, timezone
from typing import Optional

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType, TimestampType


SCHEMA = "regtech_ops_stg"
TABLE_PREFIX = "bi_output_regtechops_"
BASE_LOCATION = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"

PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_process_log"
RAW_ERRORS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_linkage_errors"
DICTIONARY_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_error_dictionary"
ENRICHED_ERRORS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_enriched_errors"
RAW_SUBMISSIONS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_raw_submissions"
TRADE_STATUS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_trade_status"


def current_run_id() -> Optional[str]:
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        run_id = context.currentRunId()
        return str(run_id.get()) if run_id.isDefined() else None
    except Exception:
        return None


RUN_ID = current_run_id()


def ensure_enrichment_tables() -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {ENRICHED_ERRORS_TABLE} (
          enriched_error_key STRING NOT NULL,
          error_record_key STRING NOT NULL,
          source_file_key STRING NOT NULL,
          source_file_name STRING NOT NULL,
          error_file_type STRING NOT NULL,
          trade_date DATE,
          submitter STRING,
          reporter STRING,
          file_sequence STRING,
          row_number BIGINT,
          error_code STRING,
          error_description STRING NOT NULL,
          error_category STRING,
          processing_stage STRING,
          action_type STRING,
          error_roe_id STRING,
          event_type STRING,
          raw_record STRING,
          record_match_hash STRING,
          raw_line STRING,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_enriched_errors'
        """
    )
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {TRADE_STATUS_TABLE} (
          trade_status_key STRING NOT NULL,
          submission_record_key STRING NOT NULL,
          source_file_key STRING NOT NULL,
          source_file_name STRING NOT NULL,
          trade_date DATE,
          event_type STRING,
          status STRING NOT NULL,
          error_code STRING,
          error_description STRING,
          error_record_key STRING,
          raw_record_hash STRING NOT NULL,
          record_match_hash STRING NOT NULL,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_trade_status'
        """
    )
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
    task_name: str,
    status: str,
    started_ts: datetime,
    records_read: Optional[int] = None,
    records_written: Optional[int] = None,
    message: Optional[str] = None,
    exception_class: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    completed_ts = datetime.now(timezone.utc)
    process_log_id = hashlib.sha256(
        "||".join([str(RUN_ID), task_name, status, started_ts.isoformat(), completed_ts.isoformat()]).encode("utf-8")
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
    rows = [
        (
            process_log_id,
            RUN_ID,
            task_name,
            None,
            None,
            status,
            started_ts,
            completed_ts,
            records_read,
            records_written,
            message,
            exception_class,
            error_message,
            completed_ts,
            completed_ts,
        )
    ]
    spark.createDataFrame(rows, schema).write.format("delta").mode("append").saveAsTable(PROCESS_LOG_TABLE)


def merge_delta(source_df: DataFrame, target_table: str, temp_view: str, merge_key: str) -> int:
    source_df.createOrReplaceTempView(temp_view)
    spark.sql(
        f"""
        MERGE INTO {target_table} AS target
        USING {temp_view} AS source
        ON target.{merge_key} = source.{merge_key}
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    return source_df.count()


def canonical_dictionary() -> DataFrame:
    order_window = Window.partitionBy("error_code").orderBy(
        F.col("processing_stage").asc_nulls_last(),
        F.col("severity").asc_nulls_last(),
        F.col("error_description").asc_nulls_last(),
    )
    return (
        spark.table(DICTIONARY_TABLE)
        .withColumn("dictionary_rank", F.row_number().over(order_window))
        .where(F.col("dictionary_rank") == 1)
        .drop("dictionary_rank", "created_ts", "updated_ts")
    )


def build_enriched_errors() -> DataFrame:
    errors = spark.table(RAW_ERRORS_TABLE).alias("err")
    dictionary = canonical_dictionary().alias("dict")
    return errors.join(dictionary, F.col("err.error_code") == F.col("dict.error_code"), "left").select(
        F.sha2(F.col("err.error_record_key"), 256).alias("enriched_error_key"),
        F.col("err.error_record_key"),
        F.col("err.source_file_key"),
        F.col("err.source_file_name"),
        F.col("err.error_file_type"),
        F.col("err.trade_date"),
        F.col("err.submitter"),
        F.col("err.reporter"),
        F.col("err.file_sequence"),
        F.col("err.row_number"),
        F.col("err.error_code"),
        F.coalesce(F.col("dict.error_description"), F.lit("UNKNOWN_ERROR_CODE")).alias("error_description"),
        F.col("dict.error_category").alias("error_category"),
        F.col("dict.processing_stage").alias("processing_stage"),
        F.col("err.action_type"),
        F.col("err.error_roe_id"),
        F.col("err.event_type"),
        F.col("err.raw_record"),
        F.col("err.record_match_hash"),
        F.col("err.raw_line"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )


def build_trade_status() -> DataFrame:
    submissions = spark.table(RAW_SUBMISSIONS_TABLE).alias("sub")
    errors_by_record = (
        spark.table(ENRICHED_ERRORS_TABLE)
        .where(F.col("record_match_hash").isNotNull())
        .groupBy("trade_date", "record_match_hash")
        .agg(
            F.concat_ws(";", F.sort_array(F.collect_set("error_code"))).alias("error_code"),
            F.concat_ws("; ", F.sort_array(F.collect_set("error_description"))).alias("error_description"),
            F.min("error_record_key").alias("error_record_key"),
        )
        .alias("err")
    )
    joined = submissions.join(
        errors_by_record,
        (F.col("sub.trade_date").eqNullSafe(F.col("err.trade_date")))
        & (F.col("sub.record_match_hash") == F.col("err.record_match_hash")),
        "left",
    )
    return joined.select(
        F.sha2(F.col("sub.submission_record_key"), 256).alias("trade_status_key"),
        F.col("sub.submission_record_key"),
        F.col("sub.source_file_key"),
        F.col("sub.source_file_name"),
        F.col("sub.trade_date"),
        F.col("sub.event_type"),
        F.when(F.col("err.error_record_key").isNotNull(), F.lit("REJECTED")).otherwise(F.lit("ACCEPTED")).alias("status"),
        F.col("err.error_code"),
        F.col("err.error_description"),
        F.col("err.error_record_key"),
        F.col("sub.raw_record_hash"),
        F.col("sub.record_match_hash"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )


ensure_enrichment_tables()
run_started = datetime.now(timezone.utc)
try:
    enriched = build_enriched_errors()
    enriched_count = merge_delta(enriched, ENRICHED_ERRORS_TABLE, "cat_enriched_errors_src", "enriched_error_key")

    trade_status = build_trade_status()
    status_count = merge_delta(trade_status, TRADE_STATUS_TABLE, "cat_trade_status_src", "trade_status_key")

    process_log(
        "02_enrich_errors",
        "SUCCESS",
        run_started,
        records_read=enriched_count,
        records_written=status_count,
        message=f"Enriched {enriched_count} error rows and reconciled {status_count} submission status rows.",
    )
except Exception as exc:
    error = f"{exc}\n{traceback.format_exc()}"
    process_log(
        "02_enrich_errors",
        "FAILED",
        run_started,
        exception_class=exc.__class__.__name__,
        error_message=error[-4000:],
    )
    raise
