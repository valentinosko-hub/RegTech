# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Parse Files
# MAGIC
# MAGIC **Pipeline:** CAT RegTechOps — Hourly File Parsing
# MAGIC
# MAGIC Reads files in `DOWNLOADED` status from the file registry and routes each to
# MAGIC the correct parser based on file type:
# MAGIC
# MAGIC | File type        | Target table                                    |
# MAGIC |------------------|-------------------------------------------------|
# MAGIC | ACK              | `bi_output_regtechops_cat_meta_feedback`        |
# MAGIC | INTEGRITY        | `bi_output_regtechops_cat_meta_feedback`        |
# MAGIC | INGESTION_META   | `bi_output_regtechops_cat_meta_feedback`        |
# MAGIC | SUBMISSION       | `bi_output_regtechops_cat_raw_submissions`      |
# MAGIC | INGESTION_ERROR  | `bi_output_regtechops_cat_enriched_errors`      |
# MAGIC | LINKAGE_ERROR    | `bi_output_regtechops_cat_linkage_errors`       |
# MAGIC | DELETE           | `bi_output_regtechops_cat_file_registry` (flag) |
# MAGIC
# MAGIC **Idempotent:** files with status `SUCCESS` are skipped. Re-running is always safe.
# MAGIC
# MAGIC > **Phase 2 note:** Full event-type-aware schema registry per event type is
# MAGIC > intentionally deferred. Submission files are stored as raw records only.

# COMMAND ----------

import bz2
import csv
import io
import re
import traceback
import uuid
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType, LongType, StringType, StructField, StructType, TimestampType,
)

# COMMAND ----------

# ── Widgets ──────────────────────────────────────────────────────────────────
dbutils.widgets.text("secret_scope", "regtech-ops", "Databricks Secret Scope")
dbutils.widgets.text("run_id",       "",            "Pipeline Run ID")

RUN_ID = dbutils.widgets.get("run_id") or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

# COMMAND ----------

# ── Constants ─────────────────────────────────────────────────────────────────
STORAGE_BASE   = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"
SFTP_LANDING   = f"{STORAGE_BASE}/sftp_landing"
SCHEMA         = "regtech_ops_stg"

REGISTRY_TABLE    = f"{SCHEMA}.bi_output_regtechops_cat_file_registry"
META_TABLE        = f"{SCHEMA}.bi_output_regtechops_cat_meta_feedback"
SUBMISSIONS_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_raw_submissions"
ENRICHED_TABLE    = f"{SCHEMA}.bi_output_regtechops_cat_enriched_errors"
LINKAGE_TABLE     = f"{SCHEMA}.bi_output_regtechops_cat_linkage_errors"
PROCESS_LOG_TABLE = f"{SCHEMA}.bi_output_regtechops_cat_process_log"

META_LOCATION        = f"{STORAGE_BASE}/bi_output_regtechops_cat_meta_feedback/"
SUBMISSIONS_LOCATION = f"{STORAGE_BASE}/bi_output_regtechops_cat_raw_submissions/"
ENRICHED_LOCATION    = f"{STORAGE_BASE}/bi_output_regtechops_cat_enriched_errors/"
LINKAGE_LOCATION     = f"{STORAGE_BASE}/bi_output_regtechops_cat_linkage_errors/"
PROCESS_LOG_LOCATION = f"{STORAGE_BASE}/bi_output_regtechops_cat_process_log/"

print(f"[01_parse_files] run_id={RUN_ID}")

# COMMAND ----------

# ── Table initialisation ──────────────────────────────────────────────────────

def _ensure_tables():
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {META_TABLE} (
            meta_id                   STRING,
            source_file_name          STRING,
            version                   STRING,
            submitter                 STRING,
            reporter                  STRING,
            trade_date                DATE,
            submission_file_name      STRING,
            receipt_timestamp         TIMESTAMP,
            stage                     STRING,
            stage_complete_timestamp  TIMESTAMP,
            status                    STRING,
            severity                  STRING,
            cat_error_code            STRING,
            error_file_name           STRING,
            error_count               LONG,
            total_records_count       LONG,
            raw_line                  STRING,
            created_ts                TIMESTAMP,
            updated_ts                TIMESTAMP
        )
        USING DELTA
        LOCATION '{META_LOCATION}'
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {SUBMISSIONS_TABLE} (
            submission_id    STRING,
            source_file_name STRING,
            trade_date       DATE,
            submitter        STRING,
            reporter         STRING,
            line_number      LONG,
            raw_record       STRING,
            created_ts       TIMESTAMP,
            updated_ts       TIMESTAMP
        )
        USING DELTA
        LOCATION '{SUBMISSIONS_LOCATION}'
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {ENRICHED_TABLE} (
            error_record_id  STRING,
            source_file_name STRING,
            file_type        STRING,
            trade_date       DATE,
            submitter        STRING,
            reporter         STRING,
            error_code       STRING,
            action_type      STRING,
            error_roe_id     STRING,
            raw_record       STRING,
            event_type       STRING,
            error_description STRING,
            error_category   STRING,
            processing_stage STRING,
            created_ts       TIMESTAMP,
            updated_ts       TIMESTAMP
        )
        USING DELTA
        LOCATION '{ENRICHED_LOCATION}'
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {LINKAGE_TABLE} (
            linkage_error_id  STRING,
            source_file_name  STRING,
            trade_date        DATE,
            submitter         STRING,
            reporter          STRING,
            error_code        STRING,
            action_type       STRING,
            error_roe_id      STRING,
            raw_record        STRING,
            event_type        STRING,
            error_description STRING,
            error_category    STRING,
            processing_stage  STRING,
            created_ts        TIMESTAMP,
            updated_ts        TIMESTAMP
        )
        USING DELTA
        LOCATION '{LINKAGE_LOCATION}'
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

# ── Utility helpers ───────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)


def safe_get(lst: list, idx: int, default=None):
    """Return lst[idx] stripped, or default if out of bounds or blank."""
    try:
        v = lst[idx].strip()
        return v if v != "" else default
    except IndexError:
        return default


def parse_cat_timestamp(raw: str):
    """Parse CAT ISO-like timestamps: 20260428T010340.119000000"""
    if not raw:
        return None
    try:
        # Normalise nanosecond precision to microseconds
        raw = re.sub(r"(\.\d{6})\d+", r"\1", raw)
        return datetime.strptime(raw, "%Y%m%dT%H%M%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(raw, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def extract_trade_date_str(filename: str):
    m = re.search(r"_(\d{8})_", filename)
    return m.group(1) if m else None


def extract_submitter(filename: str):
    return filename.split("_")[0] if "_" in filename else None


def extract_reporter(filename: str):
    parts = filename.split("_")
    return parts[1] if len(parts) > 1 else None


def read_abfss_bytes(abfss_path: str) -> bytes:
    """Read a file from ABFSS as raw bytes via Hadoop FileSystem."""
    jvm = spark._jvm
    hadoop_fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        jvm.java.net.URI.create(abfss_path),
        spark.sparkContext._jsc.hadoopConfiguration(),
    )
    path = jvm.org.apache.hadoop.fs.Path(abfss_path)
    in_stream = hadoop_fs.open(path)
    # Read all bytes
    barray = jvm.org.apache.commons.io.IOUtils.toByteArray(in_stream)
    in_stream.close()
    return bytes(barray)

# COMMAND ----------

# ── Process logger ────────────────────────────────────────────────────────────

def log_event(stage: str, status: str, message: str,
              file_name: str = None, records_in: int = 0,
              records_out: int = 0, duration_ms: int = 0):
    ts = now_utc()
    row = [(str(uuid.uuid4()), RUN_ID, "01_parse_files", stage, status,
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

# COMMAND ----------

# ── Registry status updater ───────────────────────────────────────────────────

def update_registry_status(file_id: str, status: str, error_message: str = None):
    ts = now_utc()
    updates = {"status": f"'{status}'", "updated_ts": f"'{ts.isoformat()}'"}
    if status in ("SUCCESS", "FAILED"):
        updates["processing_completed_ts"] = f"'{ts.isoformat()}'"
    if error_message:
        escaped = error_message.replace("'", "''")[:4096]
        updates["error_message"] = f"'{escaped}'"
    set_clause = ", ".join(f"{k} = {v}" for k, v in updates.items())
    spark.sql(f"""
        UPDATE {REGISTRY_TABLE}
        SET {set_clause}
        WHERE file_id = '{file_id}'
    """)

# COMMAND ----------

# ── META FILE PARSER ──────────────────────────────────────────────────────────
# Positional CSV, no header.  Layout verified against real sample files:
#  [0]  version
#  [1]  submitter
#  [2]  reporter
#  [3]  file_date (trade date YYYYMMDD referencing the submission)
#  [4]  submission_file_name
#  [5]  receipt_timestamp
#  [6]  stage
#  [7]  stage_complete_timestamp
#  [8]  status
#  [9]  severity
#  [10] cat_error_code
#  [11] error_file_name  (present on Failure rows)
#  [12] error_count
#  [16] total_records_count  (index verified from real ingestion.csv samples)

def parse_meta_file(file_name: str, raw_text: str) -> list:
    """Parse a single-line positional meta CSV into a dict."""
    reader = csv.reader(io.StringIO(raw_text))
    rows   = []
    ts     = now_utc()
    for raw_row in reader:
        if not raw_row or all(v.strip() == "" for v in raw_row):
            continue
        row_dict = {
            "meta_id":                  str(uuid.uuid4()),
            "source_file_name":         file_name,
            "version":                  safe_get(raw_row, 0),
            "submitter":                safe_get(raw_row, 1),
            "reporter":                 safe_get(raw_row, 2),
            "trade_date_str":           safe_get(raw_row, 3),
            "submission_file_name":     safe_get(raw_row, 4),
            "receipt_timestamp":        parse_cat_timestamp(safe_get(raw_row, 5)),
            "stage":                    safe_get(raw_row, 6),
            "stage_complete_timestamp": parse_cat_timestamp(safe_get(raw_row, 7)),
            "status":                   safe_get(raw_row, 8),
            "severity":                 safe_get(raw_row, 9),
            "cat_error_code":           safe_get(raw_row, 10),
            "error_file_name":          safe_get(raw_row, 11),
            "error_count":              int(safe_get(raw_row, 12) or 0),
            "total_records_count":      int(safe_get(raw_row, 16) or 0),
            "raw_line":                 ",".join(raw_row),
            "created_ts":               ts,
            "updated_ts":               ts,
        }
        rows.append(row_dict)
    return rows


META_SCHEMA = StructType([
    StructField("meta_id",                  StringType()),
    StructField("source_file_name",         StringType()),
    StructField("version",                  StringType()),
    StructField("submitter",                StringType()),
    StructField("reporter",                 StringType()),
    StructField("trade_date_str",           StringType()),
    StructField("submission_file_name",     StringType()),
    StructField("receipt_timestamp",        TimestampType()),
    StructField("stage",                    StringType()),
    StructField("stage_complete_timestamp", TimestampType()),
    StructField("status",                   StringType()),
    StructField("severity",                 StringType()),
    StructField("cat_error_code",           StringType()),
    StructField("error_file_name",          StringType()),
    StructField("error_count",              LongType()),
    StructField("total_records_count",      LongType()),
    StructField("raw_line",                 StringType()),
    StructField("created_ts",               TimestampType()),
    StructField("updated_ts",               TimestampType()),
])


def write_meta_rows(rows: list):
    if not rows:
        return
    data = [(
        r["meta_id"], r["source_file_name"], r["version"],
        r["submitter"], r["reporter"], r["trade_date_str"],
        r["submission_file_name"], r["receipt_timestamp"],
        r["stage"], r["stage_complete_timestamp"],
        r["status"], r["severity"], r["cat_error_code"],
        r["error_file_name"], r["error_count"], r["total_records_count"],
        r["raw_line"], r["created_ts"], r["updated_ts"],
    ) for r in rows]

    df = spark.createDataFrame(data, META_SCHEMA) \
        .withColumn("trade_date", F.to_date(F.col("trade_date_str"), "yyyyMMdd").cast(DateType())) \
        .drop("trade_date_str")

    # Dedup: skip if this exact source_file_name + stage row already exists
    existing = spark.table(META_TABLE).select("source_file_name", "stage")
    df = df.join(existing, ["source_file_name", "stage"], "left_anti")

    df.write.format("delta").mode("append").saveAsTable(META_TABLE)

# COMMAND ----------

# ── SUBMISSION PARSER ─────────────────────────────────────────────────────────
# Stores every line of the .csv.bz2 as raw_record.
# Full event-type-aware schema registry deferred to Phase 2.

SUBMISSIONS_SCHEMA = StructType([
    StructField("submission_id",    StringType()),
    StructField("source_file_name", StringType()),
    StructField("trade_date_str",   StringType()),
    StructField("submitter",        StringType()),
    StructField("reporter",         StringType()),
    StructField("line_number",      LongType()),
    StructField("raw_record",       StringType()),
    StructField("created_ts",       TimestampType()),
    StructField("updated_ts",       TimestampType()),
])


def parse_and_write_submission(file_name: str, raw_bytes: bytes):
    """Decompress bz2, store each line as raw record.  Header row kept as-is."""
    ts = now_utc()
    decompressed = bz2.decompress(raw_bytes).decode("utf-8", errors="replace")
    lines = decompressed.splitlines()

    data = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        data.append((
            str(uuid.uuid4()), file_name,
            extract_trade_date_str(file_name),
            extract_submitter(file_name),
            extract_reporter(file_name),
            i + 1, line, ts, ts,
        ))

    if not data:
        return 0

    df = spark.createDataFrame(data, SUBMISSIONS_SCHEMA) \
        .withColumn("trade_date", F.to_date(F.col("trade_date_str"), "yyyyMMdd").cast(DateType())) \
        .drop("trade_date_str")

    # Idempotency: skip if file already ingested
    if spark.table(SUBMISSIONS_TABLE).filter(
            F.col("source_file_name") == file_name).count() > 0:
        print(f"[01] Skipping already-ingested submission: {file_name}")
        return 0

    df.write.format("delta").mode("append").saveAsTable(SUBMISSIONS_TABLE)
    return len(data)

# COMMAND ----------

# ── ERROR FILE PARSER ─────────────────────────────────────────────────────────
# Layout: error_code, action_type, errorROEID, <original record ...>
# Only first 3 columns are parsed; remainder stored as raw_record.
# event_type = raw_record.split(',')[1]  (actionType in the original CAT record)

ERROR_RECORD_SCHEMA = StructType([
    StructField("record_id",        StringType()),
    StructField("source_file_name", StringType()),
    StructField("file_type",        StringType()),
    StructField("trade_date_str",   StringType()),
    StructField("submitter",        StringType()),
    StructField("reporter",         StringType()),
    StructField("error_code",       StringType()),
    StructField("action_type",      StringType()),
    StructField("error_roe_id",     StringType()),
    StructField("raw_record",       StringType()),
    StructField("event_type",       StringType()),
    # enrichment columns are populated by notebook 02
    StructField("error_description", StringType()),
    StructField("error_category",   StringType()),
    StructField("processing_stage", StringType()),
    StructField("created_ts",       TimestampType()),
    StructField("updated_ts",       TimestampType()),
])


def parse_error_file(file_name: str, file_type: str, raw_bytes: bytes) -> list:
    """
    Parse an error file (.csv.bz2).  First 3 cols are structured;
    everything from col[3] onward is stored as raw_record.
    event_type = split(raw_record, ',')[1] — the actionType field
    of the original CAT record.
    """
    ts           = now_utc()
    decompressed = bz2.decompress(raw_bytes).decode("utf-8", errors="replace")
    reader       = csv.reader(io.StringIO(decompressed))
    rows         = []

    for cols in reader:
        if not cols or all(c.strip() == "" for c in cols):
            continue
        error_code  = safe_get(cols, 0)
        action_type = safe_get(cols, 1)
        roe_id      = safe_get(cols, 2)
        raw_record  = ",".join(c for c in cols[3:]) if len(cols) > 3 else None

        event_type = None
        if raw_record:
            parts = raw_record.split(",")
            event_type = parts[1].strip() if len(parts) > 1 else None

        rows.append((
            str(uuid.uuid4()), file_name, file_type,
            extract_trade_date_str(file_name),
            extract_submitter(file_name),
            extract_reporter(file_name),
            error_code, action_type, roe_id,
            raw_record, event_type,
            None, None, None,   # enrichment — populated in notebook 02
            ts, ts,
        ))
    return rows


def write_error_records(rows: list, target_table: str,
                        id_col: str, location: str):
    """Write parsed error records; idempotent via source_file_name dedup."""
    if not rows:
        return 0

    src_file = rows[0][1]
    if spark.table(target_table).filter(
            F.col("source_file_name") == src_file).count() > 0:
        print(f"[01] Skipping already-ingested error file: {src_file}")
        return 0

    df = spark.createDataFrame(rows, ERROR_RECORD_SCHEMA) \
        .withColumn("trade_date", F.to_date(F.col("trade_date_str"), "yyyyMMdd").cast(DateType())) \
        .drop("trade_date_str") \
        .withColumnRenamed("record_id", id_col)

    df.write.format("delta").mode("append").saveAsTable(target_table)
    return len(rows)

# COMMAND ----------

# ── DELETE FILE HANDLER ───────────────────────────────────────────────────────

def handle_delete_file(file_name: str, raw_bytes: bytes):
    """
    DEL files signal that previously submitted records should be deleted.
    In Phase 1: log the file, store raw content in submissions table with
    a 'DELETE_MARKER' prefix so downstream processes can identify them.
    Full deletion reconciliation is a Phase 2 concern.
    """
    ts = now_utc()
    decompressed = bz2.decompress(raw_bytes).decode("utf-8", errors="replace")
    lines = decompressed.splitlines()

    data = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        data.append((
            str(uuid.uuid4()), file_name,
            extract_trade_date_str(file_name),
            extract_submitter(file_name),
            extract_reporter(file_name),
            i + 1, f"DELETE_MARKER|{line}", ts, ts,
        ))

    if data:
        df = spark.createDataFrame(data, SUBMISSIONS_SCHEMA) \
            .withColumn("trade_date", F.to_date(F.col("trade_date_str"), "yyyyMMdd").cast(DateType())) \
            .drop("trade_date_str")
        df.write.format("delta").mode("append").saveAsTable(SUBMISSIONS_TABLE)

    return len(data)

# COMMAND ----------

# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_parse_files():
    parse_start = now_utc()

    # Files eligible for parsing: DOWNLOADED or lingering PROCESSING (retries)
    pending_df = spark.table(REGISTRY_TABLE).filter(
        F.col("status").isin("DOWNLOADED", "PROCESSING")
    )
    pending = pending_df.collect()
    print(f"[01] Files to parse: {len(pending)}")

    if not pending:
        log_event("PARSE", "NO_PENDING_FILES", "No files awaiting parse")
        return 0

    parsed_count = 0
    for row in pending:
        file_id    = row.file_id
        file_name  = row.file_name
        file_type  = row.file_type
        abfss_path = row.abfss_path

        if not abfss_path:
            update_registry_status(file_id, "FAILED", "abfss_path is NULL — file not downloaded")
            continue

        t0 = now_utc()
        update_registry_status(file_id, "PROCESSING")

        try:
            raw_bytes = read_abfss_bytes(abfss_path)

            # ── Route by file type ────────────────────────────────────────────
            if file_type in ("ACK", "INTEGRITY", "INGESTION_META"):
                raw_text   = raw_bytes.decode("utf-8", errors="replace")
                meta_rows  = parse_meta_file(file_name, raw_text)
                write_meta_rows(meta_rows)
                n_out = len(meta_rows)

            elif file_type == "SUBMISSION":
                n_out = parse_and_write_submission(file_name, raw_bytes)

            elif file_type == "INGESTION_ERROR":
                error_rows = parse_error_file(file_name, file_type, raw_bytes)
                n_out = write_error_records(
                    error_rows, ENRICHED_TABLE, "error_record_id", ENRICHED_LOCATION)

            elif file_type == "LINKAGE_ERROR":
                error_rows = parse_error_file(file_name, file_type, raw_bytes)
                n_out = write_error_records(
                    error_rows, LINKAGE_TABLE, "linkage_error_id", LINKAGE_LOCATION)

            elif file_type == "DELETE":
                n_out = handle_delete_file(file_name, raw_bytes)

            else:
                log_event("PARSE_SKIP", "WARN", f"Unknown file_type: {file_type}", file_name=file_name)
                update_registry_status(file_id, "SUCCESS")
                continue

            duration_ms = int((now_utc() - t0).total_seconds() * 1000)
            update_registry_status(file_id, "SUCCESS")
            log_event("PARSE_FILE", "SUCCESS", f"type={file_type}, records_out={n_out}",
                      file_name=file_name, records_in=1, records_out=n_out,
                      duration_ms=duration_ms)
            print(f"[01] ✓ {file_name}  type={file_type}  records={n_out}")
            parsed_count += 1

        except Exception as exc:
            err_msg = traceback.format_exc()
            update_registry_status(file_id, "FAILED", str(exc)[:4096])
            log_event("PARSE_FILE", "FAILED", err_msg[:4096], file_name=file_name)
            print(f"[01] ✗ {file_name}  ERROR: {exc}")

    duration_ms = int((now_utc() - parse_start).total_seconds() * 1000)
    log_event("PARSE", "COMPLETED", f"Parsed {parsed_count}/{len(pending)} files",
              records_in=len(pending), records_out=parsed_count, duration_ms=duration_ms)
    return parsed_count


parsed_count = run_parse_files()
dbutils.jobs.taskValues.set(key="parsed_count", value=parsed_count)
