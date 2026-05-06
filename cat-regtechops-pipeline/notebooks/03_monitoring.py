# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Monitoring & Reconciliation Dashboard
# MAGIC
# MAGIC **Pipeline:** CAT RegTechOps — Operations Dashboard
# MAGIC
# MAGIC Provides an operational view of the CAT SFTP pipeline:
# MAGIC
# MAGIC - **File Registry Summary** — counts per status and file type
# MAGIC - **Meta Feedback Summary** — stage completion and error rates
# MAGIC - **Reconciliation** — submission totals vs errors vs accepted
# MAGIC - **Error Breakdown** — top error codes with descriptions
# MAGIC - **Trade Status Summary** — ACCEPTED / REJECTED by trade date
# MAGIC - **Recent Pipeline Runs** — last 24 h process log
# MAGIC - **Late-Arriving Files** — files discovered after T+1

# COMMAND ----------

from datetime import datetime, timedelta, timezone

from pyspark.sql import functions as F

# COMMAND ----------

# ── Widgets ───────────────────────────────────────────────────────────────────
dbutils.widgets.text("lookback_hours", "24", "Lookback hours for recent runs")
dbutils.widgets.text("trade_date",     "",   "Filter to specific trade date (YYYY-MM-DD, blank=all)")

LOOKBACK_HOURS = int(dbutils.widgets.get("lookback_hours") or 24)
TRADE_DATE_FILTER = dbutils.widgets.get("trade_date").strip() or None

# COMMAND ----------

# ── Constants ─────────────────────────────────────────────────────────────────
SCHEMA = "regtech_ops_stg"

REGISTRY_TABLE     = f"{SCHEMA}.bi_output_regtechops_cat_file_registry"
META_TABLE         = f"{SCHEMA}.bi_output_regtechops_cat_meta_feedback"
SUBMISSIONS_TABLE  = f"{SCHEMA}.bi_output_regtechops_cat_raw_submissions"
ENRICHED_TABLE     = f"{SCHEMA}.bi_output_regtechops_cat_enriched_errors"
LINKAGE_TABLE      = f"{SCHEMA}.bi_output_regtechops_cat_linkage_errors"
ERROR_DICT_TABLE   = f"{SCHEMA}.bi_output_regtechops_cat_error_dictionary"
TRADE_STATUS_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_trade_status"
PROCESS_LOG_TABLE  = f"{SCHEMA}.bi_output_regtechops_cat_process_log"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 — File Registry Summary

# COMMAND ----------

print("=" * 70)
print("FILE REGISTRY — STATUS BREAKDOWN")
print("=" * 70)
spark.table(REGISTRY_TABLE) \
    .groupBy("file_type", "status") \
    .agg(F.count("*").alias("file_count")) \
    .orderBy("file_type", "status") \
    .display()

# COMMAND ----------

print("=" * 70)
print("FILE REGISTRY — FILES IN FAILED STATE (need attention)")
print("=" * 70)
spark.table(REGISTRY_TABLE) \
    .filter(F.col("status") == "FAILED") \
    .select("file_name", "file_type", "trade_date", "error_message",
            "discovered_ts", "processing_completed_ts") \
    .orderBy(F.col("discovered_ts").desc()) \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 — Meta Feedback Summary

# COMMAND ----------

print("=" * 70)
print("META FEEDBACK — STAGE COMPLETION STATUS")
print("=" * 70)
meta_df = spark.table(META_TABLE)
if TRADE_DATE_FILTER:
    meta_df = meta_df.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

meta_df.groupBy("stage", "status") \
    .agg(
        F.count("*").alias("file_count"),
        F.sum("total_records_count").alias("total_records"),
        F.sum("error_count").alias("total_errors"),
    ) \
    .orderBy("stage", "status") \
    .display()

# COMMAND ----------

print("=" * 70)
print("META FEEDBACK — FILES WITH INGESTION ERRORS")
print("=" * 70)
meta_df_filtered = spark.table(META_TABLE)
if TRADE_DATE_FILTER:
    meta_df_filtered = meta_df_filtered.filter(
        F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

meta_df_filtered \
    .filter((F.col("stage") == "INGESTION") & (F.col("status") == "Failure")) \
    .select("submission_file_name", "trade_date",
            "error_file_name", "error_count",
            "total_records_count",
            "stage_complete_timestamp") \
    .orderBy(F.col("stage_complete_timestamp").desc()) \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 — Reconciliation by Trade Date

# COMMAND ----------

print("=" * 70)
print("RECONCILIATION — SUBMISSION vs ERRORS vs ACCEPTED")
print("=" * 70)
meta_ing = spark.table(META_TABLE).filter(F.col("stage") == "INGESTION")
if TRADE_DATE_FILTER:
    meta_ing = meta_ing.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

recon_df = meta_ing.groupBy("trade_date", "submitter", "reporter") \
    .agg(
        F.sum("total_records_count").alias("total_submitted"),
        F.sum("error_count").alias("total_errors"),
    ) \
    .withColumn("total_accepted",
                F.col("total_submitted") - F.coalesce(F.col("total_errors"), F.lit(0))) \
    .withColumn("error_rate_pct",
                F.round(
                    F.col("total_errors") / F.col("total_submitted") * 100, 4
                )) \
    .orderBy(F.col("trade_date").desc())

recon_df.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 — Top Error Codes

# COMMAND ----------

print("=" * 70)
print("ERROR BREAKDOWN — TOP 25 ERROR CODES (INGESTION)")
print("=" * 70)
err_df = spark.table(ENRICHED_TABLE)
if TRADE_DATE_FILTER:
    err_df = err_df.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

err_df.groupBy("error_code", "error_description", "error_category", "processing_stage") \
    .agg(F.count("*").alias("occurrence_count")) \
    .orderBy(F.col("occurrence_count").desc()) \
    .limit(25) \
    .display()

# COMMAND ----------

print("=" * 70)
print("ERROR BREAKDOWN — TOP 25 ERROR CODES (LINKAGE)")
print("=" * 70)
lnk_df = spark.table(LINKAGE_TABLE)
if TRADE_DATE_FILTER:
    lnk_df = lnk_df.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

lnk_df.groupBy("error_code", "error_description", "error_category", "processing_stage") \
    .agg(F.count("*").alias("occurrence_count")) \
    .orderBy(F.col("occurrence_count").desc()) \
    .limit(25) \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 — Trade Status Summary

# COMMAND ----------

print("=" * 70)
print("TRADE STATUS — BY TRADE DATE")
print("=" * 70)
ts_df = spark.table(TRADE_STATUS_TABLE)
if TRADE_DATE_FILTER:
    ts_df = ts_df.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

ts_df.groupBy("trade_date", "submitter", "reporter", "status") \
    .agg(F.count("*").alias("record_count")) \
    .orderBy(F.col("trade_date").desc(), "status") \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6 — Error Category Distribution

# COMMAND ----------

print("=" * 70)
print("TRADE STATUS — REJECTION REASONS BY CATEGORY")
print("=" * 70)
ts_df2 = spark.table(TRADE_STATUS_TABLE).filter(F.col("status") == "REJECTED")
if TRADE_DATE_FILTER:
    ts_df2 = ts_df2.filter(F.col("trade_date").cast("string") == TRADE_DATE_FILTER)

ts_df2.groupBy("trade_date", "error_category", "error_code", "error_description") \
    .agg(F.count("*").alias("rejection_count")) \
    .orderBy(F.col("trade_date").desc(), F.col("rejection_count").desc()) \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7 — Recent Pipeline Runs (last N hours)

# COMMAND ----------

print("=" * 70)
print(f"PIPELINE LOG — LAST {LOOKBACK_HOURS} HOURS")
print("=" * 70)
cutoff_ts = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

spark.table(PROCESS_LOG_TABLE) \
    .filter(F.col("created_ts") >= F.lit(cutoff_ts)) \
    .orderBy(F.col("created_ts").desc()) \
    .select("run_id", "notebook", "stage", "status",
            "message", "file_name", "records_in", "records_out",
            "duration_ms", "created_ts") \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8 — Pipeline Health KPIs

# COMMAND ----------

print("=" * 70)
print("PIPELINE HEALTH — SUMMARY KPIs")
print("=" * 70)

registry = spark.table(REGISTRY_TABLE)
total_files     = registry.count()
success_files   = registry.filter(F.col("status") == "SUCCESS").count()
failed_files    = registry.filter(F.col("status") == "FAILED").count()
pending_files   = registry.filter(F.col("status").isin("DISCOVERED", "DOWNLOADED",
                                                         "PROCESSING")).count()

meta_ingestion  = spark.table(META_TABLE).filter(F.col("stage") == "INGESTION")
total_submitted = meta_ingestion.agg(F.sum("total_records_count")).collect()[0][0] or 0
total_errors    = meta_ingestion.agg(F.sum("error_count")).collect()[0][0] or 0
total_accepted  = total_submitted - total_errors
error_rate      = round(total_errors / total_submitted * 100, 4) if total_submitted > 0 else 0.0

dict_count      = spark.table(ERROR_DICT_TABLE).count()
unenriched_ing  = spark.table(ENRICHED_TABLE).filter(
                      F.col("error_description").isNull()).count()
unenriched_lnk  = spark.table(LINKAGE_TABLE).filter(
                      F.col("error_description").isNull()).count()

print(f"  Total files tracked   : {total_files:,}")
print(f"  SUCCESS               : {success_files:,}")
print(f"  FAILED                : {failed_files:,}")
print(f"  PENDING               : {pending_files:,}")
print(f"  ─────────────────────────────────────────")
print(f"  Total submitted records : {total_submitted:,}")
print(f"  Total rejected          : {total_errors:,}")
print(f"  Total accepted          : {total_accepted:,}")
print(f"  Error rate              : {error_rate:.4f}%")
print(f"  ─────────────────────────────────────────")
print(f"  Error dictionary codes  : {dict_count:,}")
print(f"  Unenriched (ingestion)  : {unenriched_ing:,}")
print(f"  Unenriched (linkage)    : {unenriched_lnk:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9 — Late-Arriving Files Detection
# MAGIC
# MAGIC Files where `discovered_ts > trade_date + 1 business day` may indicate
# MAGIC SFTP delivery delays or corrected resubmissions.

# COMMAND ----------

print("=" * 70)
print("LATE-ARRIVING FILES — discovered > T+1 business day")
print("=" * 70)
spark.table(REGISTRY_TABLE) \
    .filter(F.col("trade_date").isNotNull()) \
    .withColumn("expected_latest_ts",
                F.date_add(F.col("trade_date"), 3).cast("timestamp")) \
    .filter(F.col("discovered_ts") > F.col("expected_latest_ts")) \
    .select("file_name", "file_type", "trade_date",
            "discovered_ts", "expected_latest_ts", "status") \
    .orderBy(F.col("discovered_ts").desc()) \
    .display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10 — Error Dictionary Coverage Check

# COMMAND ----------

print("=" * 70)
print("ERROR DICTIONARY — UNKNOWN CODES FOUND IN PRODUCTION DATA")
print("=" * 70)
unk_ing = spark.table(ENRICHED_TABLE) \
    .filter(F.col("error_description") == "UNKNOWN_ERROR_CODE") \
    .select("error_code", F.lit("INGESTION").alias("source")) \
    .distinct()

unk_lnk = spark.table(LINKAGE_TABLE) \
    .filter(F.col("error_description") == "UNKNOWN_ERROR_CODE") \
    .select("error_code", F.lit("LINKAGE").alias("source")) \
    .distinct()

unknown_codes = unk_ing.union(unk_lnk)
n_unknown = unknown_codes.count()

if n_unknown == 0:
    print("  All error codes have dictionary entries. No unknown codes found.")
else:
    print(f"  WARNING: {n_unknown} unknown error code(s) found in production data.")
    unknown_codes.display()
