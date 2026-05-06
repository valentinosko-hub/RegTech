# Databricks notebook source
"""CAT landed file parser.

Loads the CAT error dictionary once, parses newly landed meta, submission,
delete, ingestion error, and linkage error files, and appends/merges immutable
raw records into external Delta tables.
"""

from __future__ import annotations

import hashlib
import csv
import traceback
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType, TimestampType


SCHEMA = "regtech_ops_stg"
TABLE_PREFIX = "bi_output_regtechops_"
BASE_LOCATION = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"

REGISTRY_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_file_registry"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_process_log"
META_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_meta_feedback"
RAW_SUBMISSIONS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_raw_submissions"
RAW_ERRORS_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_linkage_errors"
DICTIONARY_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_error_dictionary"

MATCH_FIELD_SEPARATOR = "\x1f"
ERROR_ROW_SCHEMA = StructType(
    [
        StructField("error_code", StringType(), True),
        StructField("action_type", StringType(), True),
        StructField("error_roe_id", StringType(), True),
        StructField("raw_record", StringType(), True),
    ]
)


def widget_value(name: str, default: str) -> str:
    try:
        dbutils.widgets.text(name, default)
        value = dbutils.widgets.get(name)
        return value if value not in (None, "") else default
    except Exception:
        return default


ERROR_DICTIONARY_PATH = widget_value(
    "error_dictionary_path",
    f"{BASE_LOCATION}/_config/cat_error_dictionary_full_v4_1_0.json",
)
MAX_FILES_PER_RUN = int(widget_value("max_files_per_run", "500"))
RELOAD_ERROR_DICTIONARY = widget_value("reload_error_dictionary", "false").lower() == "true"


def current_run_id() -> Optional[str]:
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        run_id = context.currentRunId()
        return str(run_id.get()) if run_id.isDefined() else None
    except Exception:
        return None


RUN_ID = current_run_id()


def ensure_parse_tables() -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {META_TABLE} (
          meta_feedback_key STRING NOT NULL,
          source_file_key STRING NOT NULL,
          source_file_name STRING NOT NULL,
          source_file_type STRING NOT NULL,
          trade_date DATE,
          version STRING,
          submitter STRING,
          reporter STRING,
          file_date DATE,
          cat_file_name STRING,
          receipt_timestamp TIMESTAMP,
          stage STRING,
          stage_complete_timestamp TIMESTAMP,
          status STRING,
          severity STRING,
          error_code STRING,
          error_count BIGINT,
          total_records_count BIGINT,
          error_file_name STRING,
          raw_line STRING NOT NULL,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_meta_feedback'
        """
    )
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {RAW_SUBMISSIONS_TABLE} (
          submission_record_key STRING NOT NULL,
          source_file_key STRING NOT NULL,
          source_file_name STRING NOT NULL,
          source_file_type STRING NOT NULL,
          trade_date DATE,
          submitter STRING,
          reporter STRING,
          file_sequence STRING,
          row_number BIGINT NOT NULL,
          event_type STRING,
          raw_record STRING NOT NULL,
          raw_record_hash STRING NOT NULL,
          record_match_hash STRING NOT NULL,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_raw_submissions'
        """
    )
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {RAW_ERRORS_TABLE} (
          error_record_key STRING NOT NULL,
          source_file_key STRING NOT NULL,
          source_file_name STRING NOT NULL,
          error_file_type STRING NOT NULL,
          trade_date DATE,
          submitter STRING,
          reporter STRING,
          file_sequence STRING,
          row_number BIGINT NOT NULL,
          error_code STRING,
          action_type STRING,
          error_roe_id STRING,
          event_type STRING,
          raw_record STRING,
          record_match_hash STRING,
          raw_line STRING NOT NULL,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_linkage_errors'
        """
    )
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {DICTIONARY_TABLE} (
          error_dictionary_key STRING NOT NULL,
          error_code STRING NOT NULL,
          error_description STRING NOT NULL,
          error_category STRING NOT NULL,
          processing_stage STRING NOT NULL,
          severity STRING,
          source_version STRING,
          source_file STRING,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_error_dictionary'
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
    file_key: Optional[str] = None,
    source_file_name: Optional[str] = None,
    records_read: Optional[int] = None,
    records_written: Optional[int] = None,
    message: Optional[str] = None,
    exception_class: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    completed_ts = datetime.now(timezone.utc)
    process_log_id = hashlib.sha256(
        "||".join(
            [
                str(RUN_ID),
                task_name,
                str(file_key),
                status,
                started_ts.isoformat(),
                completed_ts.isoformat(),
            ]
        ).encode("utf-8")
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
            task_name,
            file_key,
            source_file_name,
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
    spark.createDataFrame(row, schema).write.format("delta").mode("append").saveAsTable(PROCESS_LOG_TABLE)


def read_text_with_row_numbers(path: str) -> DataFrame:
    rdd = spark.sparkContext.textFile(path).zipWithIndex().map(lambda row: (int(row[1]) + 1, row[0]))
    return spark.createDataFrame(rdd, ["row_number", "raw_line"]).where(F.length(F.trim(F.col("raw_line"))) > 0)


def processed_file_keys(task_name: str) -> DataFrame:
    return (
        spark.table(PROCESS_LOG_TABLE)
        .where((F.col("task_name") == task_name) & (F.col("status") == "SUCCESS") & F.col("file_key").isNotNull())
        .select("file_key")
        .distinct()
    )


def files_pending_parse() -> DataFrame:
    parsed = processed_file_keys("01_parse_files")
    return (
        spark.table(REGISTRY_TABLE)
        .where((F.col("status") == "SUCCESS") & F.col("landing_path").isNotNull())
        .join(parsed, "file_key", "left_anti")
        .orderBy("remote_modified_ts", "file_name")
        .limit(MAX_FILES_PER_RUN)
    )


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


def array_item(parts_col: F.Column, index: int) -> F.Column:
    return parts_col.getItem(index)


def numeric_or_null(value_col: F.Column) -> F.Column:
    return F.when(F.trim(value_col).rlike(r"^\d+$"), F.trim(value_col).cast("bigint"))


def parse_cat_timestamp(value_col: F.Column) -> F.Column:
    return F.coalesce(
        F.to_timestamp(value_col, "yyyyMMdd'T'HHmmss.SSSSSSSSS"),
        F.to_timestamp(value_col, "yyyyMMdd'T'HHmmss.SSSSSS"),
        F.to_timestamp(value_col, "yyyyMMdd'T'HHmmss"),
    )


def parse_csv_fields(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    text = value.lstrip("\ufeff").rstrip("\r\n")
    try:
        return [field.strip() for field in next(csv.reader([text], skipinitialspace=True))]
    except Exception:
        return [field.strip() for field in text.split(",")]


def csv_field(value: Optional[str], index: int) -> Optional[str]:
    fields = parse_csv_fields(value)
    return fields[index] if len(fields) > index else None


def canonical_record(value: Optional[str]) -> Optional[str]:
    fields = parse_csv_fields(value)
    if not fields:
        return None
    return MATCH_FIELD_SEPARATOR.join(fields)


def split_error_line(value: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    if value is None:
        return (None, None, None, None)
    text = value.lstrip("\ufeff").rstrip("\r\n")
    in_quotes = False
    delimiter_count = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if in_quotes and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            delimiter_count += 1
            if delimiter_count == 3:
                header_fields = parse_csv_fields(text[:index])
                header_fields = (header_fields + [None, None, None])[:3]
                return (header_fields[0], header_fields[1], header_fields[2], text[index + 1 :])
        index += 1
    header_fields = parse_csv_fields(text)
    header_fields = (header_fields + [None, None, None])[:3]
    return (header_fields[0], header_fields[1], header_fields[2], None)


csv_field_udf = F.udf(csv_field, StringType())
canonical_record_udf = F.udf(canonical_record, StringType())
split_error_line_udf = F.udf(split_error_line, ERROR_ROW_SCHEMA)


def load_error_dictionary_once() -> int:
    started = datetime.now(timezone.utc)
    try:
        if not RELOAD_ERROR_DICTIONARY and spark.table(DICTIONARY_TABLE).limit(1).count() > 0:
            process_log(
                "01_load_error_dictionary",
                "SUCCESS",
                started,
                records_read=0,
                records_written=0,
                message="CAT error dictionary already loaded; reusing Delta table.",
            )
            return 0
        dictionary_raw = spark.read.option("multiLine", "true").json(ERROR_DICTIONARY_PATH)
        entries = dictionary_raw.select(
            F.col("version").alias("source_version"),
            F.col("source_file"),
            F.explode("entries").alias("entry"),
        )
        stage = F.upper(F.col("entry.stage"))
        severity = F.upper(F.col("entry.severity"))
        dictionary = entries.select(
            F.sha2(
                F.concat_ws(
                    "||",
                    F.col("entry.code").cast("string"),
                    F.col("entry.stage"),
                    F.col("entry.severity"),
                    F.col("entry.text"),
                ),
                256,
            ).alias("error_dictionary_key"),
            F.col("entry.code").cast("string").alias("error_code"),
            F.col("entry.text").alias("error_description"),
            F.when(severity.contains("WARN"), F.lit("Warning"))
            .when(stage.contains("INTEGRITY"), F.lit("Integrity"))
            .when(stage.contains("INGESTION"), F.lit("Ingestion"))
            .when(stage.contains("LINKAGE"), F.lit("Linkage"))
            .otherwise(F.lit("Ingestion"))
            .alias("error_category"),
            F.col("entry.stage").alias("processing_stage"),
            F.col("entry.severity").alias("severity"),
            F.col("source_version"),
            F.col("source_file"),
            F.current_timestamp().alias("created_ts"),
            F.current_timestamp().alias("updated_ts"),
        )
        written = merge_delta(dictionary, DICTIONARY_TABLE, "cat_error_dictionary_src", "error_dictionary_key")
        process_log(
            "01_load_error_dictionary",
            "SUCCESS",
            started,
            records_read=written,
            records_written=written,
            message=f"Loaded CAT error dictionary from {ERROR_DICTIONARY_PATH}",
        )
        return written
    except Exception as exc:
        error = f"{exc}\n{traceback.format_exc()}"
        process_log(
            "01_load_error_dictionary",
            "FAILED",
            started,
            exception_class=exc.__class__.__name__,
            error_message=error[-4000:],
        )
        raise


def parse_meta_file(file_row) -> int:
    df = read_text_with_row_numbers(file_row.landing_path)
    parts = F.split(F.col("raw_line"), ",", -1)
    parsed = df.select(
        F.sha2(F.concat_ws("||", F.lit(file_row.file_key), F.col("row_number"), F.col("raw_line")), 256).alias(
            "meta_feedback_key"
        ),
        F.lit(file_row.file_key).alias("source_file_key"),
        F.lit(file_row.file_name).alias("source_file_name"),
        F.lit(file_row.file_type).alias("source_file_type"),
        F.lit(file_row.trade_date).cast("date").alias("trade_date"),
        array_item(parts, 0).alias("version"),
        array_item(parts, 1).alias("submitter"),
        array_item(parts, 2).alias("reporter"),
        F.to_date(array_item(parts, 3), "yyyyMMdd").alias("file_date"),
        array_item(parts, 4).alias("cat_file_name"),
        parse_cat_timestamp(array_item(parts, 5)).alias("receipt_timestamp"),
        array_item(parts, 6).alias("stage"),
        parse_cat_timestamp(array_item(parts, 7)).alias("stage_complete_timestamp"),
        array_item(parts, 8).alias("status"),
        array_item(parts, 9).alias("severity"),
        array_item(parts, 10).alias("error_code"),
        F.coalesce(numeric_or_null(array_item(parts, 11)), numeric_or_null(array_item(parts, 12))).alias("error_count"),
        F.coalesce(numeric_or_null(array_item(parts, 14)), numeric_or_null(array_item(parts, 16))).alias(
            "total_records_count"
        ),
        F.when(array_item(parts, 11).rlike(r"(?i)\.csv\.bz2$"), array_item(parts, 11)).alias("error_file_name"),
        F.col("raw_line"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_delta(parsed, META_TABLE, "cat_meta_feedback_src", "meta_feedback_key")


def parse_submission_file(file_row) -> int:
    df = read_text_with_row_numbers(file_row.landing_path)
    parsed = df.select(
        F.sha2(F.concat_ws("||", F.lit(file_row.file_key), F.col("row_number"), F.col("raw_line")), 256).alias(
            "submission_record_key"
        ),
        F.lit(file_row.file_key).alias("source_file_key"),
        F.lit(file_row.file_name).alias("source_file_name"),
        F.lit(file_row.file_type).alias("source_file_type"),
        F.lit(file_row.trade_date).cast("date").alias("trade_date"),
        F.lit(file_row.submitter).alias("submitter"),
        F.lit(file_row.reporter).alias("reporter"),
        F.lit(file_row.file_sequence).alias("file_sequence"),
        F.col("row_number"),
        csv_field_udf(F.col("raw_line"), F.lit(1)).alias("event_type"),
        F.col("raw_line").alias("raw_record"),
        F.sha2(F.col("raw_line"), 256).alias("raw_record_hash"),
        F.sha2(canonical_record_udf(F.col("raw_line")), 256).alias("record_match_hash"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_delta(parsed, RAW_SUBMISSIONS_TABLE, "cat_raw_submissions_src", "submission_record_key")


def parse_error_file(file_row) -> int:
    df = read_text_with_row_numbers(file_row.landing_path)
    split = split_error_line_udf(F.col("raw_line"))
    parsed_base = df.withColumn("parsed_error", split)
    parsed = parsed_base.select(
        F.sha2(F.concat_ws("||", F.lit(file_row.file_key), F.col("row_number"), F.col("raw_line")), 256).alias(
            "error_record_key"
        ),
        F.lit(file_row.file_key).alias("source_file_key"),
        F.lit(file_row.file_name).alias("source_file_name"),
        F.lit(file_row.file_type).alias("error_file_type"),
        F.lit(file_row.trade_date).cast("date").alias("trade_date"),
        F.lit(file_row.submitter).alias("submitter"),
        F.lit(file_row.reporter).alias("reporter"),
        F.lit(file_row.file_sequence).alias("file_sequence"),
        F.col("row_number"),
        F.col("parsed_error.error_code").alias("error_code"),
        F.col("parsed_error.action_type").alias("action_type"),
        F.col("parsed_error.error_roe_id").alias("error_roe_id"),
        csv_field_udf(F.col("parsed_error.raw_record"), F.lit(1)).alias("event_type"),
        F.col("parsed_error.raw_record").alias("raw_record"),
        F.sha2(canonical_record_udf(F.col("parsed_error.raw_record")), 256).alias("record_match_hash"),
        F.col("raw_line"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_delta(parsed, RAW_ERRORS_TABLE, "cat_raw_errors_src", "error_record_key")


def parse_file(file_row) -> int:
    started = datetime.now(timezone.utc)
    try:
        if file_row.file_type in ("META_ACK", "META_INTEGRITY", "META_INGESTION"):
            written = parse_meta_file(file_row)
        elif file_row.file_type in ("SUBMISSION", "DELETE"):
            written = parse_submission_file(file_row)
        elif file_row.file_type in ("INGESTION_ERROR", "LINKAGE_ERROR"):
            written = parse_error_file(file_row)
        else:
            written = 0
        process_log(
            "01_parse_files",
            "SUCCESS",
            started,
            file_key=file_row.file_key,
            source_file_name=file_row.file_name,
            records_read=written,
            records_written=written,
            message=f"Parsed {file_row.file_type} from {file_row.landing_path}",
        )
        return written
    except Exception as exc:
        error = f"{exc}\n{traceback.format_exc()}"
        process_log(
            "01_parse_files",
            "FAILED",
            started,
            file_key=file_row.file_key,
            source_file_name=file_row.file_name,
            exception_class=exc.__class__.__name__,
            error_message=error[-4000:],
        )
        raise


ensure_parse_tables()
load_error_dictionary_once()
run_started = datetime.now(timezone.utc)
pending = files_pending_parse().collect()
total_written = 0
for file_to_parse in pending:
    total_written += parse_file(file_to_parse)

process_log(
    "01_parse_files_batch",
    "SUCCESS",
    run_started,
    records_read=len(pending),
    records_written=total_written,
    message=f"Parsed {len(pending)} landed files into CAT raw Delta tables.",
)
