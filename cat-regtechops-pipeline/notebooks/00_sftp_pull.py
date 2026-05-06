# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — SFTP Pull
# MAGIC
# MAGIC **Pipeline:** CAT RegTechOps — Hourly SFTP Ingestion
# MAGIC **Schedule:** Every hour
# MAGIC
# MAGIC Connects to the CAT SFTP server, detects NEW files only, downloads them to
# MAGIC the ABFSS landing zone, and registers each file in `bi_output_regtechops_cat_file_registry`.
# MAGIC
# MAGIC **Idempotent:** files already present in the registry are skipped regardless of
# MAGIC current status, so re-running the notebook is always safe.

# COMMAND ----------

# ── Cluster library requirement ─────────────────────────────────────────────
# Install on the cluster (or as a cluster-scoped init script):
#   pip install paramiko
# ─────────────────────────────────────────────────────────────────────────────

# COMMAND ----------

import hashlib
import io
import os
import re
import tempfile
import traceback
import uuid
from datetime import datetime, timezone

import paramiko
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType, LongType, StringType, StructField, StructType, TimestampType,
)

# COMMAND ----------

# ── Widgets ─────────────────────────────────────────────────────────────────
dbutils.widgets.text("secret_scope",  "regtech-ops",  "Databricks Secret Scope")
dbutils.widgets.text("sftp_user",     "93007",        "SFTP Username")
dbutils.widgets.text("run_id",        "",             "Pipeline Run ID (leave blank for auto)")

SECRET_SCOPE = dbutils.widgets.get("secret_scope")
SFTP_USER    = dbutils.widgets.get("sftp_user")
RUN_ID       = dbutils.widgets.get("run_id") or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

# COMMAND ----------

# ── Constants ────────────────────────────────────────────────────────────────
SFTP_HOST   = "transfer.s3.com"
SFTP_PORT   = 22
SFTP_DIR    = "/cat"

STORAGE_BASE   = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"
SFTP_LANDING   = f"{STORAGE_BASE}/sftp_landing"

SCHEMA            = "regtech_ops_stg"
REGISTRY_TABLE    = f"{SCHEMA}.bi_output_regtechops_cat_file_registry"
PROCESS_LOG_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_process_log"

REGISTRY_LOCATION    = f"{STORAGE_BASE}/bi_output_regtechops_cat_file_registry/"
PROCESS_LOG_LOCATION = f"{STORAGE_BASE}/bi_output_regtechops_cat_process_log/"

print(f"[00_sftp_pull] run_id={RUN_ID}")

# COMMAND ----------

# ── File-type detection (order matters — most specific first) ────────────────
FILE_TYPE_PATTERNS = [
    (r"\.ingestion\.error\.csv\.bz2$",  "INGESTION_ERROR"),
    (r"\.linkage\.error_[^.]+\.csv\.bz2$", "LINKAGE_ERROR"),
    (r"\.DEL\.csv\.bz2$",               "DELETE"),
    (r"\.ack\.csv$",                     "ACK"),
    (r"\.integrity\.csv$",               "INTEGRITY"),
    (r"\.ingestion\.csv$",               "INGESTION_META"),
    (r"\.csv\.bz2$",                     "SUBMISSION"),
]

def detect_file_type(filename: str) -> str:
    for pattern, ftype in FILE_TYPE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return ftype
    return "UNKNOWN"


def extract_trade_date(filename: str):
    """Extract YYYYMMDD from filename and return as date string."""
    m = re.search(r"_(\d{8})_", filename)
    return m.group(1) if m else None


def extract_submitter(filename: str):
    """Extract submitter (first token before first underscore)."""
    return filename.split("_")[0] if "_" in filename else None


def extract_reporter(filename: str):
    """Extract reporter (second token)."""
    parts = filename.split("_")
    return parts[1] if len(parts) > 1 else None


def file_id_from_path(sftp_path: str) -> str:
    return hashlib.sha256(sftp_path.encode()).hexdigest()[:32]

# COMMAND ----------

# ── Delta table initialisation ───────────────────────────────────────────────

def _ensure_registry():
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {REGISTRY_TABLE} (
            file_id                  STRING        NOT NULL,
            file_name                STRING        NOT NULL,
            file_path                STRING        NOT NULL,
            abfss_path               STRING,
            file_type                STRING,
            trade_date               DATE,
            submitter                STRING,
            reporter                 STRING,
            file_size_bytes          LONG,
            status                   STRING,
            retry_count              INT,
            error_message            STRING,
            discovered_ts            TIMESTAMP,
            processing_started_ts    TIMESTAMP,
            processing_completed_ts  TIMESTAMP,
            created_ts               TIMESTAMP,
            updated_ts               TIMESTAMP
        )
        USING DELTA
        LOCATION '{REGISTRY_LOCATION}'
    """)


def _ensure_process_log():
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {PROCESS_LOG_TABLE} (
            log_id       STRING,
            run_id       STRING,
            notebook     STRING,
            stage        STRING,
            status       STRING,
            message      STRING,
            file_name    STRING,
            records_in   LONG,
            records_out  LONG,
            duration_ms  LONG,
            created_ts   TIMESTAMP,
            updated_ts   TIMESTAMP
        )
        USING DELTA
        LOCATION '{PROCESS_LOG_LOCATION}'
    """)


_ensure_registry()
_ensure_process_log()

# COMMAND ----------

# ── Process logger ────────────────────────────────────────────────────────────

def log_event(stage: str, status: str, message: str,
              file_name: str = None, records_in: int = 0,
              records_out: int = 0, duration_ms: int = 0):
    now = datetime.now(timezone.utc)
    row = [(str(uuid.uuid4()), RUN_ID, "00_sftp_pull", stage, status,
            message[:4096], file_name, int(records_in), int(records_out),
            int(duration_ms), now, now)]
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

# COMMAND ----------

# ── Registry helpers ──────────────────────────────────────────────────────────

def get_registered_file_ids() -> set:
    try:
        return {r.file_id for r in spark.table(REGISTRY_TABLE).select("file_id").collect()}
    except Exception:
        return set()


def upsert_registry_rows(rows: list):
    """Bulk-upsert a list of registry dicts into the file registry."""
    if not rows:
        return
    now = datetime.now(timezone.utc)
    schema = StructType([
        StructField("file_id",                  StringType()),
        StructField("file_name",                StringType()),
        StructField("file_path",                StringType()),
        StructField("abfss_path",               StringType()),
        StructField("file_type",                StringType()),
        StructField("trade_date_str",           StringType()),
        StructField("submitter",                StringType()),
        StructField("reporter",                 StringType()),
        StructField("file_size_bytes",          LongType()),
        StructField("status",                   StringType()),
        StructField("retry_count",              LongType()),
        StructField("error_message",            StringType()),
        StructField("discovered_ts",            TimestampType()),
        StructField("processing_started_ts",    TimestampType()),
        StructField("processing_completed_ts",  TimestampType()),
        StructField("created_ts",               TimestampType()),
        StructField("updated_ts",               TimestampType()),
    ])
    data = [(
        r["file_id"], r["file_name"], r["file_path"],
        r.get("abfss_path"), r["file_type"], r.get("trade_date_str"),
        r.get("submitter"), r.get("reporter"),
        r.get("file_size_bytes", 0), r["status"],
        r.get("retry_count", 0), r.get("error_message"),
        r.get("discovered_ts", now), r.get("processing_started_ts"),
        r.get("processing_completed_ts"),
        r.get("created_ts", now), now,
    ) for r in rows]

    updates_df = spark.createDataFrame(data, schema) \
        .withColumn("trade_date",
                    F.to_date(F.col("trade_date_str"), "yyyyMMdd").cast(DateType())) \
        .drop("trade_date_str")

    DeltaTable.forName(spark, REGISTRY_TABLE).alias("tgt") \
        .merge(updates_df.alias("src"), "tgt.file_id = src.file_id") \
        .whenMatchedUpdate(set={
            "abfss_path":              "src.abfss_path",
            "status":                  "src.status",
            "file_size_bytes":         "src.file_size_bytes",
            "retry_count":             "src.retry_count",
            "error_message":           "src.error_message",
            "processing_started_ts":   "src.processing_started_ts",
            "processing_completed_ts": "src.processing_completed_ts",
            "updated_ts":              "src.updated_ts",
        }) \
        .whenNotMatchedInsertAll() \
        .execute()

# COMMAND ----------

# ── SFTP connection ───────────────────────────────────────────────────────────

def get_sftp_client():
    ssh_key_str = dbutils.secrets.get(scope=SECRET_SCOPE, key="TR-S3-CAT-SSHKey")
    pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key_str))
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, pkey=pkey)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp, transport

# COMMAND ----------

# ── ABFSS writer ──────────────────────────────────────────────────────────────

def write_bytes_to_abfss(data: bytes, abfss_path: str):
    """Write raw bytes to ABFSS via Hadoop FileSystem API."""
    jvm       = spark._jvm
    hadoop_fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        jvm.java.net.URI.create(abfss_path),
        spark.sparkContext._jsc.hadoopConfiguration(),
    )
    out_path = jvm.org.apache.hadoop.fs.Path(abfss_path)
    out      = hadoop_fs.create(out_path, True)   # overwrite=True
    out.write(data)
    out.close()

# COMMAND ----------

# ── Main pull logic ───────────────────────────────────────────────────────────

def run_sftp_pull():
    pull_start = datetime.now(timezone.utc)
    log_event("SFTP_PULL", "STARTED", f"Connecting to {SFTP_HOST}{SFTP_DIR}")

    # ── 1. Get already-registered file IDs ───────────────────────────────────
    registered_ids = get_registered_file_ids()
    print(f"[00] Already registered: {len(registered_ids)} files")

    # ── 2. List remote files ──────────────────────────────────────────────────
    sftp, transport = get_sftp_client()
    try:
        remote_entries = sftp.listdir_attr(SFTP_DIR)
    except Exception as exc:
        log_event("SFTP_LIST", "FAILED", str(exc))
        raise

    print(f"[00] Remote files found: {len(remote_entries)}")

    # ── 3. Filter to new files ────────────────────────────────────────────────
    new_entries = []
    for attr in remote_entries:
        fname   = attr.filename
        fpath   = f"{SFTP_DIR}/{fname}"
        file_id = file_id_from_path(fpath)
        if file_id not in registered_ids:
            new_entries.append((attr, fname, fpath, file_id))

    print(f"[00] New files to process: {len(new_entries)}")
    if not new_entries:
        log_event("SFTP_PULL", "NO_NEW_FILES", "No new files discovered")
        transport.close()
        return 0

    # ── 4. Register all new files as DISCOVERED ───────────────────────────────
    now = datetime.now(timezone.utc)
    discovered_rows = []
    for attr, fname, fpath, file_id in new_entries:
        trade_date_str = extract_trade_date(fname)
        ftype          = detect_file_type(fname)
        discovered_rows.append({
            "file_id":         file_id,
            "file_name":       fname,
            "file_path":       fpath,
            "file_type":       ftype,
            "trade_date_str":  trade_date_str,
            "submitter":       extract_submitter(fname),
            "reporter":        extract_reporter(fname),
            "file_size_bytes": attr.st_size or 0,
            "status":          "DISCOVERED",
            "retry_count":     0,
            "discovered_ts":   now,
            "created_ts":      now,
        })
    upsert_registry_rows(discovered_rows)
    print(f"[00] Registered {len(discovered_rows)} files as DISCOVERED")

    # ── 5. Download each file to ABFSS ────────────────────────────────────────
    download_results = []
    for attr, fname, fpath, file_id in new_entries:
        trade_date_str = extract_trade_date(fname) or "unknown"
        abfss_path     = f"{SFTP_LANDING}/{trade_date_str}/{fname}"
        dl_start       = datetime.now(timezone.utc)

        # Mark as PROCESSING
        upsert_registry_rows([{
            "file_id":               file_id,
            "file_name":             fname,
            "file_path":             fpath,
            "file_type":             detect_file_type(fname),
            "trade_date_str":        trade_date_str,
            "submitter":             extract_submitter(fname),
            "reporter":              extract_reporter(fname),
            "file_size_bytes":       attr.st_size or 0,
            "status":                "PROCESSING",
            "retry_count":           0,
            "discovered_ts":         dl_start,
            "processing_started_ts": dl_start,
        }])

        try:
            buf = io.BytesIO()
            sftp.getfo(fpath, buf)
            raw_bytes = buf.getvalue()
            write_bytes_to_abfss(raw_bytes, abfss_path)
            dl_ms = int((datetime.now(timezone.utc) - dl_start).total_seconds() * 1000)

            download_results.append({
                "file_id":               file_id,
                "file_name":             fname,
                "file_path":             fpath,
                "file_type":             detect_file_type(fname),
                "trade_date_str":        trade_date_str,
                "submitter":             extract_submitter(fname),
                "reporter":              extract_reporter(fname),
                "file_size_bytes":       len(raw_bytes),
                "abfss_path":            abfss_path,
                "status":                "DOWNLOADED",
                "retry_count":           0,
                "discovered_ts":         dl_start,
                "processing_started_ts": dl_start,
                "processing_completed_ts": datetime.now(timezone.utc),
            })
            log_event("FILE_DOWNLOAD", "SUCCESS", f"Downloaded {fname} ({len(raw_bytes)} bytes)",
                      file_name=fname, records_out=1, duration_ms=dl_ms)
            print(f"[00] ✓ {fname}  ({len(raw_bytes):,} bytes)  → {abfss_path}")

        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {exc}"
            download_results.append({
                "file_id":               file_id,
                "file_name":             fname,
                "file_path":             fpath,
                "file_type":             detect_file_type(fname),
                "trade_date_str":        trade_date_str,
                "submitter":             extract_submitter(fname),
                "reporter":              extract_reporter(fname),
                "file_size_bytes":       0,
                "status":                "FAILED",
                "retry_count":           1,
                "error_message":         err_msg,
                "discovered_ts":         dl_start,
                "processing_started_ts": dl_start,
                "processing_completed_ts": datetime.now(timezone.utc),
            })
            log_event("FILE_DOWNLOAD", "FAILED", err_msg, file_name=fname)
            print(f"[00] ✗ {fname}  ERROR: {err_msg}")

    transport.close()
    upsert_registry_rows(download_results)

    success_count = sum(1 for r in download_results if r["status"] == "DOWNLOADED")
    failed_count  = sum(1 for r in download_results if r["status"] == "FAILED")
    duration_ms   = int((datetime.now(timezone.utc) - pull_start).total_seconds() * 1000)

    log_event("SFTP_PULL", "COMPLETED",
              f"Downloaded={success_count}, Failed={failed_count}",
              records_in=len(new_entries), records_out=success_count,
              duration_ms=duration_ms)
    print(f"[00] Pull complete — success={success_count}, failed={failed_count}")
    return success_count


new_file_count = run_sftp_pull()
dbutils.jobs.taskValues.set(key="new_file_count", value=new_file_count)
