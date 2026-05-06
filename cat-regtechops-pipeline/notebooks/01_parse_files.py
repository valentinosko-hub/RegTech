# Databricks notebook source
import json
import uuid
from datetime import datetime
from typing import Dict, Optional

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
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
TABLE_META_FEEDBACK = "bi_output_regtechops_cat_meta_feedback"
TABLE_LINKAGE_ERRORS = "bi_output_regtechops_cat_linkage_errors"
TABLE_RAW_SUBMISSIONS = "bi_output_regtechops_cat_raw_submissions"
TABLE_PROCESS_LOG = "bi_output_regtechops_cat_process_log"

FILE_REGISTRY_TABLE = f"{SCHEMA}.{TABLE_FILE_REGISTRY}"
META_FEEDBACK_TABLE = f"{SCHEMA}.{TABLE_META_FEEDBACK}"
LINKAGE_ERRORS_TABLE = f"{SCHEMA}.{TABLE_LINKAGE_ERRORS}"
RAW_SUBMISSIONS_TABLE = f"{SCHEMA}.{TABLE_RAW_SUBMISSIONS}"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PROCESS_LOG}"

RUN_ID = str(uuid.uuid4())


# COMMAND ----------
def assert_required_tables() -> None:
    expected_tables = [
        TABLE_FILE_REGISTRY,
        TABLE_META_FEEDBACK,
        TABLE_LINKAGE_ERRORS,
        TABLE_RAW_SUBMISSIONS,
        TABLE_PROCESS_LOG,
    ]
    missing = [
        table_name
        for table_name in expected_tables
        if not spark.catalog.tableExists(f"{SCHEMA}.{table_name}")
    ]
    if missing:
        raise RuntimeError(
            "Missing required tables. Run sql/create_tables.sql before this notebook. "
            f"Missing: {', '.join(missing)}"
        )


def write_process_log(
    status: str,
    records_read: int,
    records_written: int,
    details: Dict[str, str],
    error_message: Optional[str] = None,
) -> None:
    now = datetime.utcnow()
    payload = [
        (
            str(uuid.uuid4()),
            "01_parse_files",
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


def merge_into_table(source_df: DataFrame, target_table: str, key_column: str) -> int:
    if source_df.rdd.isEmpty():
        return 0
    source_df.cache()
    write_count = source_df.count()
    target = DeltaTable.forName(spark, target_table)
    (
        target.alias("t")
        .merge(source_df.alias("s"), f"t.{key_column} = s.{key_column}")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    source_df.unpersist()
    return write_count


def update_parse_status(file_registry_id: str, parse_status: str, error_message: Optional[str]) -> None:
    sanitized_error = None if error_message is None else error_message[:4000].replace("'", "''")
    safe_error = "NULL" if sanitized_error is None else f"'{sanitized_error}'"
    spark.sql(
        f"""
        UPDATE {FILE_REGISTRY_TABLE}
        SET parse_status = '{parse_status}',
            updated_ts = current_timestamp(),
            error_message = {safe_error}
        WHERE file_registry_id = '{file_registry_id}'
        """
    )


def parse_meta_file(file_row) -> int:
    raw_df = (
        spark.read.text(file_row["landing_path"])
        .select(F.col("value").alias("raw_line"))
        .filter(F.length(F.trim(F.col("raw_line"))) > 0)
    )
    split_col = F.split(F.col("raw_line"), ",")

    parsed_df = raw_df.select(
        F.sha2(
            F.concat_ws("||", F.lit(file_row["file_registry_id"]), F.col("raw_line")),
            256,
        ).alias("feedback_id"),
        F.lit(file_row["file_registry_id"]).alias("file_registry_id"),
        F.lit(file_row["file_name"]).alias("source_file_name"),
        F.lit(file_row["file_type"]).alias("source_file_type"),
        F.lit(file_row["trade_date"]).cast("date").alias("trade_date"),
        split_col.getItem(0).alias("version"),
        split_col.getItem(1).alias("submitter"),
        split_col.getItem(2).alias("reporter"),
        split_col.getItem(3).alias("file_date"),
        split_col.getItem(5).alias("receipt_timestamp"),
        split_col.getItem(6).alias("stage"),
        split_col.getItem(7).alias("stage_complete_timestamp"),
        split_col.getItem(8).alias("status"),
        split_col.getItem(9).alias("severity"),
        split_col.getItem(10).alias("error_code"),
        split_col.getItem(11).cast("int").alias("error_count"),
        split_col.getItem(14).cast("bigint").alias("total_records_count"),
        F.col("raw_line"),
        F.current_timestamp().alias("ingest_ts"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_into_table(parsed_df, META_FEEDBACK_TABLE, "feedback_id")


def parse_submission_or_delete_file(file_row) -> int:
    raw_df = (
        spark.read.text(file_row["landing_path"])
        .select(F.col("value").alias("raw_record"))
        .filter(F.length(F.trim(F.col("raw_record"))) > 0)
    )

    parsed_df = raw_df.select(
        F.sha2(
            F.concat_ws("||", F.lit(file_row["file_registry_id"]), F.col("raw_record")),
            256,
        ).alias("submission_row_id"),
        F.lit(file_row["file_registry_id"]).alias("file_registry_id"),
        F.lit(file_row["file_name"]).alias("source_file_name"),
        F.lit(file_row["file_type"]).alias("source_file_type"),
        F.lit(file_row["trade_date"]).cast("date").alias("trade_date"),
        F.col("raw_record"),
        F.sha2(F.col("raw_record"), 256).alias("raw_record_hash"),
        F.element_at(F.split(F.col("raw_record"), ","), 2).alias("event_type"),
        F.current_timestamp().alias("ingest_ts"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_into_table(parsed_df, RAW_SUBMISSIONS_TABLE, "submission_row_id")


def parse_error_file(file_row) -> int:
    raw_df = (
        spark.read.text(file_row["landing_path"])
        .select(F.col("value").alias("raw_line"))
        .filter(F.length(F.trim(F.col("raw_line"))) > 0)
    )
    split_col = F.split(F.col("raw_line"), ",")
    raw_record_col = F.when(
        F.size(split_col) >= 4, F.array_join(F.slice(split_col, 4, 1000000), ",")
    ).otherwise(F.lit(""))

    parsed_df = raw_df.select(
        F.sha2(
            F.concat_ws("||", F.lit(file_row["file_registry_id"]), F.col("raw_line")),
            256,
        ).alias("error_row_id"),
        F.lit(file_row["file_registry_id"]).alias("file_registry_id"),
        F.lit(file_row["file_name"]).alias("source_file_name"),
        F.lit(file_row["file_type"]).alias("source_error_file_type"),
        F.lit(file_row["trade_date"]).cast("date").alias("trade_date"),
        split_col.getItem(0).alias("error_code"),
        split_col.getItem(1).alias("action_type"),
        split_col.getItem(2).alias("error_roe_id"),
        raw_record_col.alias("raw_record"),
        F.sha2(raw_record_col, 256).alias("raw_record_hash"),
        F.element_at(F.split(raw_record_col, ","), 2).alias("event_type"),
        F.current_timestamp().alias("ingest_ts"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    return merge_into_table(parsed_df, LINKAGE_ERRORS_TABLE, "error_row_id")


# COMMAND ----------
assert_required_tables()

pending_files = (
    spark.table(FILE_REGISTRY_TABLE)
    .filter(
        (F.col("lifecycle_status") == "SUCCESS")
        & (F.col("landing_path").isNotNull())
        & (
            F.col("parse_status").isNull()
            | F.col("parse_status").isin("PENDING", "FAILED")
        )
    )
    .select("file_registry_id", "file_name", "file_type", "trade_date", "landing_path")
    .collect()
)

if not pending_files:
    write_process_log(
        status="SUCCESS",
        records_read=0,
        records_written=0,
        details={"message": "No files pending parse stage."},
    )
    dbutils.notebook.exit("No files pending parse stage.")

records_read = 0
records_written = 0
failed_files = 0

for file_row in pending_files:
    try:
        file_type = file_row["file_type"]
        update_parse_status(file_row["file_registry_id"], "PROCESSING", None)

        if file_type in {"META_ACK", "META_INGESTION", "META_INTEGRITY"}:
            written = parse_meta_file(file_row)
        elif file_type in {"SUBMISSION", "DELETE"}:
            written = parse_submission_or_delete_file(file_row)
        elif file_type in {"ERROR_INGESTION", "ERROR_LINKAGE"}:
            written = parse_error_file(file_row)
        else:
            # Unknown file type should not fail the pipeline; mark parsed with zero output.
            written = 0

        update_parse_status(file_row["file_registry_id"], "SUCCESS", None)
        records_read += 1
        records_written += written
    except Exception as exc:
        failed_files += 1
        update_parse_status(
            file_row["file_registry_id"],
            "FAILED",
            f"{type(exc).__name__}: {str(exc)}",
        )

final_status = "SUCCESS" if failed_files == 0 else "FAILED"
write_process_log(
    status=final_status,
    records_read=records_read,
    records_written=records_written,
    details={
        "files_pending": str(len(pending_files)),
        "files_failed": str(failed_files),
    },
    error_message=None if failed_files == 0 else "One or more files failed during parse stage.",
)

if failed_files > 0:
    raise RuntimeError(f"Parse stage failed for {failed_files} files.")

