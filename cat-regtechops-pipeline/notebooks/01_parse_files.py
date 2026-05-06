# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Parse CAT files (idempotent)
# MAGIC
# MAGIC Picks up `DISCOVERED` registry rows with a local path, sets `PROCESSING`, parses payloads into Delta targets **without overwriting** prior facts (merge keys), then sets `SUCCESS` / `FAILED`.

# COMMAND ----------

import bz2
import hashlib
import uuid
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# COMMAND ----------


def _utcnow():
    return datetime.now(timezone.utc)


def _init_widgets():
    dbutils.widgets.text("catalog", "hive_metastore")
    dbutils.widgets.text("schema", "regtech_ops_stg")


_init_widgets()

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
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


JOB_RUN_ID = _job_run_id() or ("adhoc-parse-" + str(uuid.uuid4()))

# COMMAND ----------


def meta_subtype_from_kind(file_kind: str) -> str:
    return {
        "META_ACK": "ACK",
        "META_INTEGRITY": "INTEGRITY",
        "META_INGESTION": "INGESTION",
    }.get(file_kind, "UNKNOWN")


def parse_meta_line(line: str) -> dict:
    line = line.strip()
    parts = line.split(",")
    def g(i: int) -> str:
        return parts[i].strip() if i < len(parts) else ""

    total = g(14)
    if not total and parts:
        tail = parts[-1].strip()
        if tail.isdigit():
            total = tail
    return {
        "version": g(0),
        "submitter": g(1),
        "reporter": g(2),
        "file_date": g(3),
        "referenced_file_name": g(4),
        "receipt_timestamp": g(5),
        "stage": g(6),
        "stage_complete_timestamp": g(7),
        "status": g(8),
        "severity": g(9),
        "error_code": g(10),
        "error_count": g(11),
        "total_records_count": total,
    }


def parse_error_line(line: str):
    line = line.strip()
    if not line:
        return None
    parts = line.split(",", 3)
    error_code = parts[0].strip()
    action_type = parts[1].strip() if len(parts) > 1 else ""
    error_roe_id = parts[2].strip() if len(parts) > 2 else ""
    raw_record = parts[3].strip() if len(parts) > 3 else ""
    rp = raw_record.split(",")
    event_type = rp[1].strip() if len(rp) > 1 else None
    return {
        "error_code": error_code,
        "action_type": action_type,
        "error_roe_id": error_roe_id,
        "raw_record": raw_record,
        "event_type": event_type,
    }


def stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="replace"))
        h.update(b"\x1e")
    return h.hexdigest()


# COMMAND ----------


def _append_process_log_row(
    notebook: str,
    status: str,
    message,
    discovered,
    processed,
):
    pid = str(uuid.uuid4())
    now = _utcnow()
    row = [
        (
            pid,
            notebook,
            JOB_RUN_ID,
            now,
            now,
            status,
            message,
            discovered,
            processed,
            now,
            now,
        )
    ]
    sch = StructType(
        [
            StructField("process_log_id", StringType(), False),
            StructField("notebook_name", StringType(), False),
            StructField("job_run_id", StringType(), True),
            StructField("started_ts", TimestampType(), False),
            StructField("ended_ts", TimestampType(), True),
            StructField("status", StringType(), False),
            StructField("message", StringType(), True),
            StructField("files_discovered", LongType(), True),
            StructField("files_processed", LongType(), True),
            StructField("created_ts", TimestampType(), False),
            StructField("updated_ts", TimestampType(), False),
        ]
    )
    spark.createDataFrame(row, sch).write.mode("append").saveAsTable(
        FQN("bi_output_regtechops_cat_process_log")
    )


_append_process_log_row("01_parse_files", "RUNNING", None, None, None)

# COMMAND ----------


def _merge_delta(table_short: str, sdf):
    fq = FQN(table_short)
    dt = DeltaTable.forName(spark, fq)
    keys = {
        "bi_output_regtechops_cat_raw_submissions": "raw_submission_id",
        "bi_output_regtechops_cat_meta_feedback": "meta_feedback_id",
        "bi_output_regtechops_cat_linkage_errors": "error_row_id",
    }
    k = keys[table_short]
    dt.alias("t").merge(sdf.alias("s"), f"t.{k} = s.{k}").whenNotMatchedInsertAll().execute()


def _update_registry(fr_id: str, status: str, detail: str | None):
    now = _utcnow().isoformat()
    d = (detail or "").replace("'", "''")
    spark.sql(
        f"""
        UPDATE {FQN("bi_output_regtechops_cat_file_registry")}
        SET registry_status = '{status}',
            status_detail = '{d}',
            last_job_run_id = '{JOB_RUN_ID.replace("'", "''")}',
            updated_ts = CAST('{now}' AS TIMESTAMP)
        WHERE file_registry_id = '{fr_id}'
        """
    )


def _process_one_row(row) -> str:
    fr_id = row.file_registry_id
    path = row.local_staging_path
    fk = row.file_kind
    td = str(row.trade_date)
    now = _utcnow()

    try:
        if fk in ("META_ACK", "META_INTEGRITY", "META_INGESTION"):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            rows_out = []
            msub = meta_subtype_from_kind(fk)
            for raw_line in content.splitlines():
                if not raw_line.strip():
                    continue
                m = parse_meta_line(raw_line)
                mid = stable_id(fr_id, msub, raw_line)
                rows_out.append(
                    (
                        mid,
                        fr_id,
                        td,
                        msub,
                        m["version"],
                        m["submitter"],
                        m["reporter"],
                        m["file_date"],
                        m["referenced_file_name"],
                        m["receipt_timestamp"],
                        m["stage"],
                        m["stage_complete_timestamp"],
                        m["status"],
                        m["severity"],
                        m["error_code"],
                        m["error_count"],
                        m["total_records_count"],
                        raw_line,
                        now,
                        now,
                    )
                )
            if rows_out:
                cols = [
                    "meta_feedback_id",
                    "file_registry_id",
                    "trade_date",
                    "meta_subtype",
                    "version",
                    "submitter",
                    "reporter",
                    "file_date",
                    "referenced_file_name",
                    "receipt_timestamp",
                    "stage",
                    "stage_complete_timestamp",
                    "status",
                    "severity",
                    "error_code",
                    "error_count",
                    "total_records_count",
                    "raw_meta_line",
                    "created_ts",
                    "updated_ts",
                ]
                sdf = spark.createDataFrame(rows_out, cols)
                sdf = sdf.withColumn("trade_date", F.to_date("trade_date"))
                _merge_delta("bi_output_regtechops_cat_meta_feedback", sdf)

        elif fk in ("SUBMISSION", "DELETE_SUBMISSION"):
            rows_out = []
            opener = bz2.open if path.endswith(".bz2") else open  # noqa: SIM115
            mode = "rt" if path.endswith(".bz2") else "r"
            enc = "utf-8"
            with opener(path, mode, encoding=enc, errors="replace") as fh:  # type: ignore[arg-type]
                for ln, line in enumerate(fh, start=1):
                    rec = line.rstrip("\n\r")
                    if not rec:
                        continue
                    rp = rec.split(",")
                    ev = rp[1].strip() if len(rp) > 1 else None
                    rid = stable_id(fr_id, str(ln), rec)
                    rows_out.append(
                        (rid, fr_id, td, ln, rec, ev, now, now)
                    )
            if rows_out:
                cols = [
                    "raw_submission_id",
                    "file_registry_id",
                    "trade_date",
                    "line_number",
                    "raw_record",
                    "event_type",
                    "created_ts",
                    "updated_ts",
                ]
                sdf = spark.createDataFrame(rows_out, cols)
                sdf = sdf.withColumn("trade_date", F.to_date("trade_date"))
                _merge_delta("bi_output_regtechops_cat_raw_submissions", sdf)

        elif fk in ("ERROR_INGESTION", "ERROR_LINKAGE"):
            eft = "INGESTION" if fk == "ERROR_INGESTION" else "LINKAGE"
            rows_out = []
            with bz2.open(path, "rt", encoding="utf-8", errors="replace") as fh:
                for ln, line in enumerate(fh, start=1):
                    parsed = parse_error_line(line)
                    if not parsed:
                        continue
                    eid = stable_id(fr_id, str(ln), line)
                    rows_out.append(
                        (
                            eid,
                            fr_id,
                            td,
                            eft,
                            parsed["error_code"],
                            parsed["action_type"],
                            parsed["error_roe_id"],
                            parsed["raw_record"],
                            parsed["event_type"],
                            ln,
                            now,
                            now,
                        )
                    )
            if rows_out:
                cols = [
                    "error_row_id",
                    "file_registry_id",
                    "trade_date",
                    "error_file_type",
                    "error_code",
                    "action_type",
                    "error_roe_id",
                    "raw_record",
                    "event_type",
                    "source_line_number",
                    "created_ts",
                    "updated_ts",
                ]
                sdf = spark.createDataFrame(rows_out, cols)
                sdf = sdf.withColumn("trade_date", F.to_date("trade_date"))
                _merge_delta("bi_output_regtechops_cat_linkage_errors", sdf)

        else:
            raise RuntimeError(f"Unsupported file_kind={fk}")

        _update_registry(fr_id, "SUCCESS", "Parsed successfully")
        return "SUCCESS"
    except Exception as e:  # noqa: BLE001
        _update_registry(fr_id, "FAILED", repr(e))
        raise


# COMMAND ----------


files_df = spark.sql(
    f"""
    SELECT file_registry_id, local_staging_path, file_kind, trade_date, file_name
    FROM {FQN("bi_output_regtechops_cat_file_registry")}
    WHERE registry_status = 'DISCOVERED'
      AND local_staging_path IS NOT NULL
    ORDER BY trade_date, file_name
    """
)

files_rows = files_df.collect()
processed = 0
errors = []
for row in files_rows:
    fr_id = row.file_registry_id
    spark.sql(
        f"""
        UPDATE {FQN("bi_output_regtechops_cat_file_registry")}
        SET registry_status = 'PROCESSING',
            status_detail = 'Parsing started',
            last_job_run_id = '{JOB_RUN_ID.replace("'", "''")}',
            updated_ts = CAST('{_utcnow().isoformat()}' AS TIMESTAMP)
        WHERE file_registry_id = '{fr_id}'
        """
    )
    try:
        _process_one_row(row)
        processed += 1
    except Exception as e:  # noqa: BLE001
        errors.append((row.file_name, repr(e)))

# COMMAND ----------


fin_msg = None if not errors else "; ".join(f"{a}: {b}" for a, b in errors[:20])
_append_process_log_row(
    "01_parse_files",
    "SUCCESS" if not errors else "FAILED",
    fin_msg,
    len(files_rows),
    processed,
)

if errors:
    raise RuntimeError(f"One or more files failed: {fin_msg}")
