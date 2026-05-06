# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Enrich Errors & Compute Trade Status
# MAGIC
# MAGIC **Pipeline:** CAT RegTechOps — Error Enrichment & Reconciliation
# MAGIC
# MAGIC ## What this notebook does
# MAGIC
# MAGIC 1. **Error dictionary bootstrap** — ensures `bi_output_regtechops_cat_error_dictionary`
# MAGIC    is populated from the canonical JSON.  Runs once; subsequent runs are no-ops.
# MAGIC
# MAGIC 2. **Error enrichment** — joins `bi_output_regtechops_cat_enriched_errors` and
# MAGIC    `bi_output_regtechops_cat_linkage_errors` to the dictionary to fill in
# MAGIC    `error_description`, `error_category`, and `processing_stage`.
# MAGIC    Missing codes are marked `UNKNOWN_ERROR_CODE` and do NOT fail the pipeline.
# MAGIC
# MAGIC 3. **Trade status** — upserts `bi_output_regtechops_cat_trade_status`:
# MAGIC    - Every errorROEID in an error file → REJECTED
# MAGIC    - Summary ACCEPTED row per submission file (total − error_count from meta)
# MAGIC
# MAGIC **Idempotent:** all writes use MERGE on natural keys.

# COMMAND ----------

import json
import uuid
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType, IntegerType, LongType, StringType, StructField,
    StructType, TimestampType,
)

# COMMAND ----------

# ── Widgets ───────────────────────────────────────────────────────────────────
dbutils.widgets.text("secret_scope",         "regtech-ops",   "Databricks Secret Scope")
dbutils.widgets.text("run_id",               "",              "Pipeline Run ID")
dbutils.widgets.text("error_dict_abfss_path",
    "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps/config/cat_error_dictionary_full_v4_1_0.json",
    "ABFSS path to error dictionary JSON")

RUN_ID          = dbutils.widgets.get("run_id") or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
ERROR_DICT_PATH = dbutils.widgets.get("error_dict_abfss_path")

# COMMAND ----------

# ── Constants ─────────────────────────────────────────────────────────────────
STORAGE_BASE = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"
SCHEMA       = "regtech_ops_stg"

ERROR_DICT_TABLE  = f"{SCHEMA}.bi_output_regtechops_cat_error_dictionary"
ENRICHED_TABLE    = f"{SCHEMA}.bi_output_regtechops_cat_enriched_errors"
LINKAGE_TABLE     = f"{SCHEMA}.bi_output_regtechops_cat_linkage_errors"
META_TABLE        = f"{SCHEMA}.bi_output_regtechops_cat_meta_feedback"
TRADE_STATUS_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_trade_status"
PROCESS_LOG_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_process_log"

ERROR_DICT_LOCATION    = f"{STORAGE_BASE}/bi_output_regtechops_cat_error_dictionary/"
TRADE_STATUS_LOCATION  = f"{STORAGE_BASE}/bi_output_regtechops_cat_trade_status/"
PROCESS_LOG_LOCATION   = f"{STORAGE_BASE}/bi_output_regtechops_cat_process_log/"

# Stage → human-readable category mapping (from CAT spec)
STAGE_TO_CATEGORY = {
    "DATA_INGESTION":         "Ingestion",
    "FDID_VALIDATION":        "Ingestion",
    "FILE_INTEGRITY":         "Integrity",
    "EXCHANGE_LINKAGE":       "Linkage",
    "EXCHANGE_NAMED_LINKAGE": "Linkage",
    "TRADE_LINKAGE":          "Linkage",
    "TRADE_NAMED_LINKAGE":    "Linkage",
    "INTRA_LINKAGE":          "Linkage",
    "INTERFIRM_SENDER":       "Linkage",
    "INTERFIRM_RECEIVER":     "Linkage",
    "WARNING":                "Warning",
}

print(f"[02_enrich_errors] run_id={RUN_ID}")

# COMMAND ----------

# ── Table initialisation ──────────────────────────────────────────────────────

def _ensure_tables():
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {ERROR_DICT_TABLE} (
            error_code        STRING NOT NULL,
            error_description STRING,
            error_category    STRING,
            processing_stage  STRING,
            severity          STRING,
            source_version    STRING,
            created_ts        TIMESTAMP,
            updated_ts        TIMESTAMP
        )
        USING DELTA
        LOCATION '{ERROR_DICT_LOCATION}'
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {TRADE_STATUS_TABLE} (
            status_id        STRING,
            source_file_name STRING,
            trade_date       DATE,
            submitter        STRING,
            reporter         STRING,
            error_roe_id     STRING,
            event_type       STRING,
            status           STRING,
            error_code       STRING,
            error_description STRING,
            error_category   STRING,
            processing_stage STRING,
            created_ts       TIMESTAMP,
            updated_ts       TIMESTAMP
        )
        USING DELTA
        LOCATION '{TRADE_STATUS_LOCATION}'
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {PROCESS_LOG_TABLE} (
            log_id      STRING,
            run_id      STRING,
            notebook    STRING,
            stage       STRING,
            status      STRING,
            message     STRING,
            file_name   STRING,
            records_in  LONG,
            records_out LONG,
            duration_ms LONG,
            created_ts  TIMESTAMP,
            updated_ts  TIMESTAMP
        )
        USING DELTA
        LOCATION '{PROCESS_LOG_LOCATION}'
    """)


_ensure_tables()

# COMMAND ----------

# ── Utility ───────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)


def log_event(stage: str, status: str, message: str,
              file_name: str = None, records_in: int = 0,
              records_out: int = 0, duration_ms: int = 0):
    ts = now_utc()
    row = [(str(uuid.uuid4()), RUN_ID, "02_enrich_errors", stage, status,
            message[:4096], file_name, int(records_in), int(records_out),
            int(duration_ms), ts, ts)]
    schema = StructType([
        StructField("log_id",       StringType()),
        StructField("run_id",       StringType()),
        StructField("notebook",     StringType()),
        StructField("stage",        StringType()),
        StructField("status",       StringType()),
        StructField("message",      StringType()),
        StructField("file_name",    StringType()),
        StructField("records_in",   LongType()),
        StructField("records_out",  LongType()),
        StructField("duration_ms",  LongType()),
        StructField("created_ts",   TimestampType()),
        StructField("updated_ts",   TimestampType()),
    ])
    spark.createDataFrame(row, schema).write \
        .format("delta").mode("append") \
        .option("mergeSchema", "true") \
        .saveAsTable(PROCESS_LOG_TABLE)


def read_abfss_text(abfss_path: str) -> str:
    jvm = spark._jvm
    hadoop_fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        jvm.java.net.URI.create(abfss_path),
        spark.sparkContext._jsc.hadoopConfiguration(),
    )
    in_stream = hadoop_fs.open(jvm.org.apache.hadoop.fs.Path(abfss_path))
    text = jvm.org.apache.commons.io.IOUtils.toString(in_stream, "UTF-8")
    in_stream.close()
    return str(text)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Bootstrap Error Dictionary
# MAGIC
# MAGIC Loads `cat_error_dictionary_full_v4_1_0.json` into Delta.
# MAGIC Idempotent: only inserts codes not already present.

# COMMAND ----------

def bootstrap_error_dictionary():
    """
    Load the CAT error dictionary JSON into the Delta table.
    Safe to call on every pipeline run; only new codes are inserted.
    """
    t0 = now_utc()
    try:
        raw_json = read_abfss_text(ERROR_DICT_PATH)
    except Exception as exc:
        log_event("DICT_LOAD", "FAILED", f"Cannot read dictionary JSON: {exc}")
        raise RuntimeError(f"Error dictionary not accessible at {ERROR_DICT_PATH}: {exc}")

    d = json.loads(raw_json)
    entries    = d.get("entries", [])
    version    = d.get("version", "unknown")
    ts         = now_utc()

    rows = []
    for entry in entries:
        code     = str(entry.get("code", ""))
        stage    = entry.get("stage", "")
        severity = entry.get("severity", "ERROR")
        category = STAGE_TO_CATEGORY.get(stage, stage)
        rows.append((
            code,
            entry.get("text", ""),
            category,
            stage,
            severity,
            version,
            ts, ts,
        ))

    schema = StructType([
        StructField("error_code",        StringType()),
        StructField("error_description", StringType()),
        StructField("error_category",    StringType()),
        StructField("processing_stage",  StringType()),
        StructField("severity",          StringType()),
        StructField("source_version",    StringType()),
        StructField("created_ts",        TimestampType()),
        StructField("updated_ts",        TimestampType()),
    ])
    new_df = spark.createDataFrame(rows, schema)

    # Idempotent: only insert codes not already in the table
    existing_codes = {r.error_code for r in spark.table(ERROR_DICT_TABLE)
                      .select("error_code").collect()}
    net_new = new_df.filter(~F.col("error_code").isin(existing_codes))
    n_new   = net_new.count()

    if n_new > 0:
        net_new.write.format("delta").mode("append").saveAsTable(ERROR_DICT_TABLE)
        print(f"[02] Error dictionary: inserted {n_new} new codes (total in source: {len(entries)})")
    else:
        print(f"[02] Error dictionary: already up to date ({len(entries)} codes, version={version})")

    duration_ms = int((now_utc() - t0).total_seconds() * 1000)
    log_event("DICT_LOAD", "SUCCESS",
              f"version={version}, total={len(entries)}, new_codes={n_new}",
              records_out=n_new, duration_ms=duration_ms)


bootstrap_error_dictionary()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Enrich Unenriched Error Records
# MAGIC
# MAGIC Finds rows in enriched_errors / linkage_errors where `error_description IS NULL`
# MAGIC and joins them to the dictionary.  Missing codes → `UNKNOWN_ERROR_CODE`.

# COMMAND ----------

def enrich_table(error_table: str, id_col: str):
    """
    Update error_description, error_category, processing_stage
    for all rows where error_description IS NULL.
    """
    t0 = now_utc()

    unenriched = spark.table(error_table).filter(F.col("error_description").isNull())
    n_pending  = unenriched.count()
    if n_pending == 0:
        print(f"[02] {error_table}: no unenriched rows")
        return 0

    dict_df = spark.table(ERROR_DICT_TABLE).select(
        F.col("error_code").alias("dict_code"),
        "error_description", "error_category", "processing_stage",
    )

    enriched = unenriched.join(dict_df,
                               unenriched["error_code"] == dict_df["dict_code"],
                               "left") \
        .withColumn("error_description",
                    F.coalesce(F.col("error_description"), F.lit("UNKNOWN_ERROR_CODE"))) \
        .withColumn("error_category",
                    F.coalesce(F.col("error_category"),    F.lit("UNKNOWN"))) \
        .withColumn("processing_stage",
                    F.coalesce(F.col("processing_stage"),  F.lit("UNKNOWN"))) \
        .withColumn("updated_ts", F.lit(now_utc()).cast(TimestampType())) \
        .drop("dict_code")

    DeltaTable.forName(spark, error_table).alias("tgt") \
        .merge(
            enriched.alias("src"),
            f"tgt.{id_col} = src.{id_col}"
        ) \
        .whenMatchedUpdate(set={
            "error_description": "src.error_description",
            "error_category":    "src.error_category",
            "processing_stage":  "src.processing_stage",
            "updated_ts":        "src.updated_ts",
        }) \
        .execute()

    duration_ms = int((now_utc() - t0).total_seconds() * 1000)
    log_event("ENRICH_ERRORS", "SUCCESS",
              f"table={error_table}, rows_enriched={n_pending}",
              records_in=n_pending, records_out=n_pending, duration_ms=duration_ms)
    print(f"[02] Enriched {n_pending} rows in {error_table}")
    return n_pending


enrich_table(ENRICHED_TABLE, "error_record_id")
enrich_table(LINKAGE_TABLE,  "linkage_error_id")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Compute Trade Status
# MAGIC
# MAGIC ### REJECTED records
# MAGIC Every `errorROEID` present in an error file becomes a REJECTED row.
# MAGIC Keyed on `(source_file_name, error_roe_id)` for idempotency.
# MAGIC
# MAGIC ### ACCEPTED summary
# MAGIC Derived from `bi_output_regtechops_cat_meta_feedback` (INGESTION stage rows):
# MAGIC `accepted_count = total_records_count − error_count`
# MAGIC Stored as a single summary row per submission file with status=ACCEPTED,
# MAGIC `error_roe_id = NULL`.
# MAGIC
# MAGIC > **Phase 2** will replace the ACCEPTED summary with individual record-level
# MAGIC > ACCEPTED rows derived from full submission-file parsing.

# COMMAND ----------

def compute_trade_status():
    t0 = now_utc()
    ts = now_utc()

    # ── REJECTED rows from INGESTION errors ──────────────────────────────────
    rejected_ingestion = spark.table(ENRICHED_TABLE).select(
        F.col("error_record_id").alias("status_id"),
        F.col("source_file_name"),
        F.col("trade_date"),
        F.col("submitter"),
        F.col("reporter"),
        F.col("error_roe_id"),
        F.col("event_type"),
        F.lit("REJECTED").alias("status"),
        F.col("error_code"),
        F.col("error_description"),
        F.col("error_category"),
        F.col("processing_stage"),
        F.lit(ts).cast(TimestampType()).alias("created_ts"),
        F.lit(ts).cast(TimestampType()).alias("updated_ts"),
    )

    # ── REJECTED rows from LINKAGE errors ────────────────────────────────────
    rejected_linkage = spark.table(LINKAGE_TABLE).select(
        F.col("linkage_error_id").alias("status_id"),
        F.col("source_file_name"),
        F.col("trade_date"),
        F.col("submitter"),
        F.col("reporter"),
        F.col("error_roe_id"),
        F.col("event_type"),
        F.lit("REJECTED").alias("status"),
        F.col("error_code"),
        F.col("error_description"),
        F.col("error_category"),
        F.col("processing_stage"),
        F.lit(ts).cast(TimestampType()).alias("created_ts"),
        F.lit(ts).cast(TimestampType()).alias("updated_ts"),
    )

    all_rejected = rejected_ingestion.union(rejected_linkage)
    n_rejected   = all_rejected.count()

    # ── ACCEPTED summary rows (one per submission file, Phase 1 only) ─────────
    # Uses INGESTION_META rows to compute accepted = total - error_count
    meta_ingestion = spark.table(META_TABLE) \
        .filter((F.col("stage") == "INGESTION") & (F.col("total_records_count") > 0)) \
        .select(
            F.col("submission_file_name").alias("source_file_name"),
            F.col("trade_date"),
            F.col("submitter"),
            F.col("reporter"),
            F.col("total_records_count"),
            F.col("error_count"),
        )

    accepted_summary = meta_ingestion \
        .withColumn("accepted_count",
                    F.col("total_records_count") - F.coalesce(F.col("error_count"), F.lit(0))) \
        .filter(F.col("accepted_count") > 0) \
        .select(
            F.expr("uuid()").alias("status_id"),
            F.col("source_file_name"),
            F.col("trade_date"),
            F.col("submitter"),
            F.col("reporter"),
            F.lit(None).cast(StringType()).alias("error_roe_id"),
            F.lit("SUMMARY").alias("event_type"),
            F.lit("ACCEPTED").alias("status"),
            F.lit(None).cast(StringType()).alias("error_code"),
            F.concat(
                F.lit("Accepted: "),
                F.col("accepted_count").cast(StringType()),
                F.lit(" of "),
                F.col("total_records_count").cast(StringType()),
                F.lit(" records"),
            ).alias("error_description"),
            F.lit(None).cast(StringType()).alias("error_category"),
            F.lit(None).cast(StringType()).alias("processing_stage"),
            F.lit(ts).cast(TimestampType()).alias("created_ts"),
            F.lit(ts).cast(TimestampType()).alias("updated_ts"),
        )

    n_accepted = accepted_summary.count()

    # ── Upsert REJECTED records ───────────────────────────────────────────────
    if n_rejected > 0:
        DeltaTable.forName(spark, TRADE_STATUS_TABLE).alias("tgt") \
            .merge(
                all_rejected.alias("src"),
                "tgt.source_file_name = src.source_file_name "
                "AND tgt.error_roe_id = src.error_roe_id "
                "AND tgt.status = 'REJECTED'"
            ) \
            .whenNotMatchedInsertAll() \
            .execute()

    # ── Upsert ACCEPTED summary rows ──────────────────────────────────────────
    if n_accepted > 0:
        DeltaTable.forName(spark, TRADE_STATUS_TABLE).alias("tgt") \
            .merge(
                accepted_summary.alias("src"),
                "tgt.source_file_name = src.source_file_name "
                "AND tgt.status = 'ACCEPTED'"
            ) \
            .whenMatchedUpdate(set={
                "error_description": "src.error_description",
                "updated_ts":        "src.updated_ts",
            }) \
            .whenNotMatchedInsertAll() \
            .execute()

    duration_ms = int((now_utc() - t0).total_seconds() * 1000)
    log_event("TRADE_STATUS", "SUCCESS",
              f"rejected={n_rejected}, accepted_summaries={n_accepted}",
              records_in=n_rejected + n_accepted,
              records_out=n_rejected + n_accepted,
              duration_ms=duration_ms)
    print(f"[02] Trade status: REJECTED={n_rejected}, ACCEPTED_SUMMARIES={n_accepted}")
    return n_rejected + n_accepted


total_status_rows = compute_trade_status()
dbutils.jobs.taskValues.set(key="trade_status_rows", value=total_status_rows)
