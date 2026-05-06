# Databricks notebook source
import json
import uuid
from datetime import datetime
from typing import Dict, Optional

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


# COMMAND ----------
# Runtime parameters
dbutils.widgets.text(
    "error_dictionary_json_path",
    "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/reference/cat_error_dictionary_full_v4_1_0.json",
)
ERROR_DICTIONARY_JSON_PATH = dbutils.widgets.get("error_dictionary_json_path")


# COMMAND ----------
SCHEMA = "regtech_ops_stg"
TABLE_FILE_REGISTRY = "bi_output_regtechops_cat_file_registry"
TABLE_ERROR_DICTIONARY = "bi_output_regtechops_cat_error_dictionary"
TABLE_LINKAGE_ERRORS = "bi_output_regtechops_cat_linkage_errors"
TABLE_ENRICHED_ERRORS = "bi_output_regtechops_cat_enriched_errors"
TABLE_RAW_SUBMISSIONS = "bi_output_regtechops_cat_raw_submissions"
TABLE_TRADE_STATUS = "bi_output_regtechops_cat_trade_status"
TABLE_PROCESS_LOG = "bi_output_regtechops_cat_process_log"

FILE_REGISTRY_TABLE = f"{SCHEMA}.{TABLE_FILE_REGISTRY}"
ERROR_DICTIONARY_TABLE = f"{SCHEMA}.{TABLE_ERROR_DICTIONARY}"
LINKAGE_ERRORS_TABLE = f"{SCHEMA}.{TABLE_LINKAGE_ERRORS}"
ENRICHED_ERRORS_TABLE = f"{SCHEMA}.{TABLE_ENRICHED_ERRORS}"
RAW_SUBMISSIONS_TABLE = f"{SCHEMA}.{TABLE_RAW_SUBMISSIONS}"
TRADE_STATUS_TABLE = f"{SCHEMA}.{TABLE_TRADE_STATUS}"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PROCESS_LOG}"

RUN_ID = str(uuid.uuid4())


# COMMAND ----------
def assert_required_tables() -> None:
    expected_tables = [
        TABLE_FILE_REGISTRY,
        TABLE_ERROR_DICTIONARY,
        TABLE_LINKAGE_ERRORS,
        TABLE_ENRICHED_ERRORS,
        TABLE_RAW_SUBMISSIONS,
        TABLE_TRADE_STATUS,
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
            "02_enrich_errors",
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


def update_enrich_status(file_registry_id: str, enrich_status: str, error_message: Optional[str]) -> None:
    sanitized_error = None if error_message is None else error_message[:4000].replace("'", "''")
    safe_error = "NULL" if sanitized_error is None else f"'{sanitized_error}'"
    spark.sql(
        f"""
        UPDATE {FILE_REGISTRY_TABLE}
        SET enrich_status = '{enrich_status}',
            updated_ts = current_timestamp(),
            error_message = {safe_error}
        WHERE file_registry_id = '{file_registry_id}'
        """
    )


def load_error_dictionary_if_needed(dictionary_path: str) -> int:
    existing_count = spark.table(ERROR_DICTIONARY_TABLE).count()
    if existing_count > 0:
        return 0

    raw_dict_df = spark.read.option("multiline", "true").json(dictionary_path)
    exploded_df = raw_dict_df.select(
        F.col("source_file").alias("source_file"),
        F.col("version").alias("source_version"),
        F.explode(F.col("entries")).alias("entry"),
    )

    normalized_df = exploded_df.select(
        F.col("entry.code").cast("string").alias("error_code"),
        F.col("entry.text").alias("error_description"),
        F.when(F.upper(F.col("entry.stage")).contains("INTEGRITY"), F.lit("Integrity"))
        .when(F.upper(F.col("entry.stage")).contains("INGESTION"), F.lit("Ingestion"))
        .when(F.upper(F.col("entry.stage")).contains("LINKAGE"), F.lit("Linkage"))
        .when(F.upper(F.col("entry.severity")).contains("WARN"), F.lit("Warning"))
        .otherwise(F.lit("Ingestion"))
        .alias("error_category"),
        F.col("entry.stage").alias("processing_stage"),
        F.col("source_version"),
        F.col("source_file"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )

    # Preserve deterministic one-to-one enrichment key by choosing one record per error_code.
    dedupe_window = Window.partitionBy("error_code").orderBy(
        F.col("processing_stage").asc(),
        F.col("error_category").asc(),
        F.col("error_description").asc(),
    )
    dictionary_df = (
        normalized_df.withColumn("dedupe_rank", F.row_number().over(dedupe_window))
        .filter(F.col("dedupe_rank") == 1)
        .drop("dedupe_rank")
    )

    dictionary_df.write.mode("append").saveAsTable(ERROR_DICTIONARY_TABLE)
    return dictionary_df.count()


def build_incremental_enriched_errors() -> DataFrame:
    errors_df = spark.table(LINKAGE_ERRORS_TABLE)
    dict_df = spark.table(ERROR_DICTIONARY_TABLE).select(
        "error_code",
        "error_description",
        "error_category",
        "processing_stage",
    )
    existing_ids_df = spark.table(ENRICHED_ERRORS_TABLE).select("error_row_id").distinct()

    return (
        errors_df.alias("e")
        .join(existing_ids_df.alias("x"), F.col("e.error_row_id") == F.col("x.error_row_id"), "left_anti")
        .join(dict_df.alias("d"), F.col("e.error_code") == F.col("d.error_code"), "left")
        .select(
            F.sha2(F.concat_ws("||", F.lit("enriched"), F.col("e.error_row_id")), 256).alias(
                "enriched_error_id"
            ),
            F.col("e.error_row_id"),
            F.col("e.file_registry_id"),
            F.col("e.source_file_name"),
            F.col("e.trade_date"),
            F.col("e.event_type"),
            F.col("e.error_code"),
            F.col("e.action_type"),
            F.col("e.error_roe_id"),
            F.col("e.raw_record"),
            F.col("e.raw_record_hash"),
            F.coalesce(F.col("d.error_description"), F.lit("UNKNOWN_ERROR_CODE")).alias(
                "error_description"
            ),
            F.coalesce(F.col("d.error_category"), F.lit("UNKNOWN")).alias("error_category"),
            F.coalesce(F.col("d.processing_stage"), F.lit("UNKNOWN")).alias("processing_stage"),
            F.current_timestamp().alias("created_ts"),
            F.current_timestamp().alias("updated_ts"),
        )
    )


def build_incremental_trade_status() -> DataFrame:
    submissions_df = spark.table(RAW_SUBMISSIONS_TABLE).alias("s")
    existing_trade_status_df = spark.table(TRADE_STATUS_TABLE).select("submission_row_id").distinct().alias("x")
    enriched_errors_df = spark.table(ENRICHED_ERRORS_TABLE).alias("e")

    error_by_submission_window = Window.partitionBy("s.submission_row_id").orderBy(
        F.col("e.updated_ts").desc_nulls_last(),
        F.col("e.error_code").asc_nulls_last(),
    )

    joined_df = (
        submissions_df.join(
            existing_trade_status_df,
            F.col("s.submission_row_id") == F.col("x.submission_row_id"),
            "left_anti",
        )
        .join(
            enriched_errors_df,
            (F.col("s.raw_record_hash") == F.col("e.raw_record_hash"))
            & (F.col("s.trade_date") == F.col("e.trade_date")),
            "left",
        )
        .withColumn("error_rank", F.row_number().over(error_by_submission_window))
        .filter((F.col("error_rank") == 1) | F.col("e.error_code").isNull())
    )

    return joined_df.select(
        F.sha2(F.concat_ws("||", F.lit("trade_status"), F.col("s.submission_row_id")), 256).alias(
            "trade_status_id"
        ),
        F.col("s.submission_row_id"),
        F.col("s.file_registry_id"),
        F.col("s.source_file_name"),
        F.col("s.trade_date"),
        F.col("s.event_type"),
        F.col("s.raw_record_hash"),
        F.when(F.col("e.error_code").isNotNull(), F.lit("REJECTED"))
        .otherwise(F.lit("ACCEPTED"))
        .alias("status"),
        F.col("e.error_code").alias("error_code"),
        F.when(F.col("e.error_code").isNotNull(), F.col("e.error_description"))
        .otherwise(F.lit(None))
        .alias("error_description"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )


# COMMAND ----------
assert_required_tables()

pending_enrich_files = (
    spark.table(FILE_REGISTRY_TABLE)
    .filter(
        (F.col("lifecycle_status") == "SUCCESS")
        & (F.col("parse_status") == "SUCCESS")
        & (F.col("enrich_status").isNull() | F.col("enrich_status").isin("PENDING", "FAILED"))
    )
    .select("file_registry_id")
    .collect()
)

if not pending_enrich_files:
    write_process_log(
        status="SUCCESS",
        records_read=0,
        records_written=0,
        details={"message": "No files pending enrich stage."},
    )
    dbutils.notebook.exit("No files pending enrich stage.")

for pending in pending_enrich_files:
    update_enrich_status(pending["file_registry_id"], "PROCESSING", None)

dictionary_loaded = 0
enriched_written = 0
trade_status_written = 0

failed = False
failure_message = None

try:
    dictionary_loaded = load_error_dictionary_if_needed(ERROR_DICTIONARY_JSON_PATH)
    enriched_df = build_incremental_enriched_errors()
    enriched_written = merge_into_table(enriched_df, ENRICHED_ERRORS_TABLE, "enriched_error_id")

    trade_status_df = build_incremental_trade_status()
    trade_status_written = merge_into_table(trade_status_df, TRADE_STATUS_TABLE, "trade_status_id")

    for pending in pending_enrich_files:
        update_enrich_status(pending["file_registry_id"], "SUCCESS", None)
except Exception as exc:
    failed = True
    failure_message = f"{type(exc).__name__}: {str(exc)}"
    for pending in pending_enrich_files:
        update_enrich_status(pending["file_registry_id"], "FAILED", failure_message)

write_process_log(
    status="FAILED" if failed else "SUCCESS",
    records_read=len(pending_enrich_files),
    records_written=enriched_written + trade_status_written,
    details={
        "dictionary_loaded_rows": str(dictionary_loaded),
        "enriched_errors_written": str(enriched_written),
        "trade_status_written": str(trade_status_written),
        "pending_files": str(len(pending_enrich_files)),
    },
    error_message=failure_message,
)

if failed:
    raise RuntimeError(f"Enrichment stage failed: {failure_message}")
