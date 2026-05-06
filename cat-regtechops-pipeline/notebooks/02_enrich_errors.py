# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Error dictionary, enrichment, trade status
# MAGIC
# MAGIC 1. Loads Appendix E JSON into `bi_output_regtechops_cat_error_dictionary` **once** (table empty only).
# MAGIC 2. Enriches new rows in `bi_output_regtechops_cat_linkage_errors` into `bi_output_regtechops_cat_enriched_errors` via dictionary join (`UNKNOWN_ERROR_CODE` fallback).
# MAGIC 3. Rebuilds `bi_output_regtechops_cat_trade_status` as **submission minus errors** using `trim(raw_record)` equality (Phase 1).

# COMMAND ----------

import uuid
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F

# COMMAND ----------


def _utcnow():
    return datetime.now(timezone.utc)


def _init_widgets():
    dbutils.widgets.text("catalog", "hive_metastore")
    dbutils.widgets.text("schema", "regtech_ops_stg")
    dbutils.widgets.text(
        "error_dictionary_path",
        "dbfs:/FileStore/regtech/cat_error_dictionary_full_v4_1_0.json",
    )


_init_widgets()

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
DICT_PATH = dbutils.widgets.get("error_dictionary_path").strip()
FQN = lambda t: f"{CATALOG}.{SCHEMA}.{t}"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------


def _job_run_id():
    for k in ("spark.databricks.jobRunId", "spark.databricks.job.runId"):
        try:
            v = spark.conf.get(k, None)
            if v:
                return v
        except Exception:
            continue
    return None


JOB_RUN_ID = _job_run_id() or ("adhoc-enrich-" + str(uuid.uuid4()))

# COMMAND ----------


def _append_process_log(notebook: str, status: str, message):
    pid = str(uuid.uuid4())
    now = _utcnow()
    from pyspark.sql.types import (
        LongType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )

    msg = "NULL" if message is None else "'" + message.replace("'", "''") + "'"
    spark.sql(
        f"""
        INSERT INTO {FQN("bi_output_regtechops_cat_process_log")} (
          process_log_id, notebook_name, job_run_id, started_ts, ended_ts,
          status, message, files_discovered, files_processed, created_ts, updated_ts
        ) VALUES (
          '{pid}', '{notebook}', '{(JOB_RUN_ID or "").replace("'", "''")}',
          CAST('{now.isoformat()}' AS TIMESTAMP),
          CAST('{now.isoformat()}' AS TIMESTAMP),
          '{status}', {msg}, NULL, NULL,
          CAST('{now.isoformat()}' AS TIMESTAMP),
          CAST('{now.isoformat()}' AS TIMESTAMP)
        )
        """
    )


_append_process_log("02_enrich_errors", "RUNNING", None)

# COMMAND ----------


def _error_category_expr(stage_col):
    st = F.upper(F.trim(stage_col))
    return (
        F.when(st == F.lit("WARNING"), F.lit("Warning"))
        .when(st.contains("LINKAGE"), F.lit("Linkage"))
        .when(st.contains("INTEGRITY") | (st == F.lit("FILE_INTEGRITY")), F.lit("Integrity"))
        .when(
            st.contains("INGESTION")
            | (st == F.lit("DATA_INGESTION"))
            | (st == F.lit("FDID_VALIDATION")),
            F.lit("Ingestion"),
        )
        .otherwise(F.lit("Ingestion"))
    )


def ensure_error_dictionary():
    cnt = spark.sql(
        f"SELECT COUNT(1) AS c FROM {FQN('bi_output_regtechops_cat_error_dictionary')}"
    ).collect()[0].c
    if int(cnt) > 0:
        return
    root = spark.read.option("multiLine", "true").json(DICT_PATH)
    dv = root.select("version").head()
    dict_version = dv.version if dv else "4.1.0"
    ex = root.select(F.explode(F.col("entries")).alias("e")).select(
        "e.code", "e.text", "e.stage", "e.severity"
    )
    out = ex.select(
        F.col("code").cast("int").alias("error_code"),
        F.col("text").alias("error_description"),
        _error_category_expr(F.col("stage")).alias("error_category"),
        F.col("stage").alias("processing_stage"),
        F.col("severity").alias("source_severity"),
        F.lit(dict_version).alias("dictionary_version"),
        F.current_timestamp().alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    out.write.format("delta").mode("append").saveAsTable(
        FQN("bi_output_regtechops_cat_error_dictionary")
    )


def enrich_new_errors():
    dict_df = spark.table(FQN("bi_output_regtechops_cat_error_dictionary")).select(
        F.col("error_code").cast("string").alias("d_ec"),
        F.col("error_description").alias("d_desc"),
        F.col("error_category").alias("d_cat"),
        F.col("processing_stage").alias("d_stage"),
    )
    le_df = spark.table(FQN("bi_output_regtechops_cat_linkage_errors"))
    ee_ids = (
        spark.table(FQN("bi_output_regtechops_cat_enriched_errors"))
        .select("error_row_id")
        .distinct()
    )
    new_only = le_df.join(ee_ids, on="error_row_id", how="left_anti")
    joined = new_only.join(
        dict_df,
        F.trim(F.col("error_code")) == F.trim(F.col("d_ec")),
        "left",
    )
    now = F.current_timestamp()
    out = joined.select(
        F.col("error_row_id").alias("enriched_error_id"),
        F.col("error_row_id"),
        F.col("file_registry_id"),
        F.col("trade_date"),
        F.col("error_file_type"),
        F.col("error_code"),
        F.col("action_type"),
        F.col("error_roe_id"),
        F.col("raw_record"),
        F.col("event_type"),
        F.coalesce(F.col("d_desc"), F.lit("UNKNOWN_ERROR_CODE")).alias("error_description"),
        F.coalesce(F.col("d_cat"), F.lit("Unknown")).alias("error_category"),
        F.coalesce(F.col("d_stage"), F.lit("UNKNOWN_STAGE")).alias("processing_stage"),
        F.col("d_ec").isNotNull().alias("dictionary_hit"),
        now.alias("created_ts"),
        now.alias("updated_ts"),
    )
    if out.take(1):
        dt = DeltaTable.forName(spark, FQN("bi_output_regtechops_cat_enriched_errors"))
        dt.alias("t").merge(
            out.alias("s"),
            "t.error_row_id = s.error_row_id",
        ).whenNotMatchedInsertAll().execute()


def rebuild_trade_status():
    subs = spark.table(FQN("bi_output_regtechops_cat_raw_submissions")).alias("s")
    enr = spark.table(FQN("bi_output_regtechops_cat_enriched_errors"))
    rej = enr.groupBy(F.trim(F.col("raw_record")).alias("raw_norm")).agg(
        F.min(F.trim(F.col("error_code"))).alias("error_code"),
        F.first("error_description", True).alias("error_description"),
    )
    base = subs.join(
        rej,
        F.trim(F.col("s.raw_record")) == F.col("raw_norm"),
        how="left",
    )
    st = base.select(
        F.col("s.raw_submission_id").alias("trade_status_id"),
        F.col("s.raw_submission_id").alias("raw_submission_id"),
        F.col("s.file_registry_id").alias("file_registry_id"),
        F.col("s.trade_date").alias("trade_date"),
        F.col("s.event_type").alias("event_type"),
        F.when(F.col("error_code").isNotNull(), F.lit("REJECTED"))
        .otherwise(F.lit("ACCEPTED"))
        .alias("status"),
        F.col("error_code").cast("string").alias("error_code"),
        F.col("error_description").alias("error_description"),
        F.col("s.created_ts").alias("created_ts"),
        F.current_timestamp().alias("updated_ts"),
    )
    dt = DeltaTable.forName(spark, FQN("bi_output_regtechops_cat_trade_status"))
    dt.alias("t").merge(
        st.alias("s"),
        "t.raw_submission_id = s.raw_submission_id",
    ).whenMatchedUpdate(
        set={
            "status": "s.status",
            "error_code": "s.error_code",
            "error_description": "s.error_description",
            "event_type": "s.event_type",
            "updated_ts": "s.updated_ts",
        }
    ).whenNotMatchedInsertAll().execute()


# COMMAND ----------


try:
    ensure_error_dictionary()
    enrich_new_errors()
    rebuild_trade_status()
    _append_process_log("02_enrich_errors", "SUCCESS", "Dictionary ensured; enrichment and trade status merged")
except Exception as e:  # noqa: BLE001
    _append_process_log("02_enrich_errors", "FAILED", repr(e))
    raise
