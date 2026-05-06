# Databricks notebook source
"""CAT SFTP discovery and landing.

Discovers new CAT files on transfer.s3.com:/cat, registers immutable file
versions, downloads only files not seen before, and lands them in external ADLS
storage for downstream parsing.
"""

from __future__ import annotations

import hashlib
import io
import os
import posixpath
import re
import stat
import tempfile
import traceback
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


SCHEMA = "regtech_ops_stg"
TABLE_PREFIX = "bi_output_regtechops_"
BASE_LOCATION = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"

REGISTRY_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_file_registry"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PREFIX}cat_process_log"


def widget_value(name: str, default: str) -> str:
    try:
        dbutils.widgets.text(name, default)
        value = dbutils.widgets.get(name)
        return value if value not in (None, "") else default
    except Exception:
        return default


SFTP_HOST = widget_value("sftp_host", "transfer.s3.com")
SFTP_DIRECTORY = widget_value("sftp_directory", "/cat")
SFTP_USERNAME = widget_value("sftp_username", "93007")
SECRET_SCOPE = widget_value("secret_scope", "regtech_ops_stg")
SSH_KEY_SECRET = widget_value("ssh_key_secret_key", "TR-S3-CAT-SSHKey")
LANDING_ROOT = widget_value("landing_root", f"{BASE_LOCATION}/_landing/cat")
MAX_FILES_PER_RUN = int(widget_value("max_files_per_run", "500"))


def sql_string(value: Optional[str]) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def current_run_id() -> Optional[str]:
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        run_id = context.currentRunId()
        return str(run_id.get()) if run_id.isDefined() else None
    except Exception:
        return None


RUN_ID = current_run_id()


def ensure_core_tables() -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {REGISTRY_TABLE} (
          file_key STRING NOT NULL,
          source_system STRING NOT NULL,
          connection_type STRING NOT NULL,
          sftp_host STRING NOT NULL,
          sftp_directory STRING NOT NULL,
          remote_path STRING NOT NULL,
          file_name STRING NOT NULL,
          file_type STRING NOT NULL,
          trade_date DATE,
          file_sequence STRING,
          submitter STRING,
          reporter STRING,
          file_size BIGINT,
          remote_modified_ts TIMESTAMP,
          landing_path STRING,
          content_hash STRING,
          status STRING NOT NULL,
          first_seen_ts TIMESTAMP NOT NULL,
          last_seen_ts TIMESTAMP NOT NULL,
          processing_started_ts TIMESTAMP,
          processed_ts TIMESTAMP,
          attempt_count BIGINT NOT NULL,
          error_message STRING,
          created_ts TIMESTAMP NOT NULL,
          updated_ts TIMESTAMP NOT NULL
        )
        USING DELTA
        LOCATION '{BASE_LOCATION}/bi_output_regtechops_cat_file_registry'
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
    rows = [
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
    spark.createDataFrame(rows, schema).write.format("delta").mode("append").saveAsTable(PROCESS_LOG_TABLE)


def classify_file(file_name: str) -> Optional[str]:
    lowered = file_name.lower()
    if lowered.endswith(".ingestion.error.csv.bz2"):
        return "INGESTION_ERROR"
    if re.search(r"\.linkage\.error_[^/]+\.csv\.bz2$", lowered):
        return "LINKAGE_ERROR"
    if lowered.endswith(".del.csv.bz2"):
        return "DELETE"
    if lowered.endswith(".csv.bz2"):
        return "SUBMISSION"
    if lowered.endswith(".ack.csv"):
        return "META_ACK"
    if lowered.endswith(".integrity.csv"):
        return "META_INTEGRITY"
    if lowered.endswith(".ingestion.csv"):
        return "META_INGESTION"
    return None


def parse_file_name(file_name: str) -> Dict[str, Optional[str]]:
    match = re.search(
        r"^(?P<submitter>[^_]+)_(?P<reporter>[^_]+)_(?P<trade_date>\d{8})_.*?_(?P<sequence>\d+)(?=\.|_)",
        file_name,
    )
    if not match:
        return {"submitter": None, "reporter": None, "trade_date": None, "file_sequence": None}
    trade_date = datetime.strptime(match.group("trade_date"), "%Y%m%d").date()
    return {
        "submitter": match.group("submitter"),
        "reporter": match.group("reporter"),
        "trade_date": trade_date,
        "file_sequence": match.group("sequence"),
    }


def file_key(remote_path: str, file_name: str, file_size: int, modified_epoch: int) -> str:
    payload = f"{remote_path}|{file_name}|{file_size}|{modified_epoch}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def private_key_from_secret(secret_value: str):
    import paramiko

    key_text = secret_value.replace("\\n", "\n").strip()
    key_errors: List[str] = []
    for key_class in (
        paramiko.RSAKey,
        paramiko.ECDSAKey,
        paramiko.Ed25519Key,
        paramiko.DSSKey,
    ):
        try:
            return key_class.from_private_key(io.StringIO(key_text))
        except Exception as exc:
            key_errors.append(f"{key_class.__name__}: {exc}")
    raise ValueError("SSH key secret could not be parsed as RSA, ECDSA, Ed25519, or DSS key: " + "; ".join(key_errors))


def open_sftp_client():
    import paramiko

    key_material = dbutils.secrets.get(scope=SECRET_SCOPE, key=SSH_KEY_SECRET)
    key = private_key_from_secret(key_material)
    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=SFTP_USERNAME, pkey=key)
    return transport, paramiko.SFTPClient.from_transport(transport)


def discover_files(sftp) -> List[Dict[str, object]]:
    discovered: List[Dict[str, object]] = []
    now = datetime.now(timezone.utc)
    for attrs in sftp.listdir_attr(SFTP_DIRECTORY):
        if stat.S_ISDIR(attrs.st_mode):
            continue
        name = attrs.filename
        file_type = classify_file(name)
        if file_type is None:
            continue
        remote_path = posixpath.join(SFTP_DIRECTORY, name)
        parsed = parse_file_name(name)
        modified_ts = datetime.fromtimestamp(attrs.st_mtime, tz=timezone.utc)
        discovered.append(
            {
                "file_key": file_key(remote_path, name, attrs.st_size, attrs.st_mtime),
                "source_system": "CAT",
                "connection_type": "SFTP",
                "sftp_host": SFTP_HOST,
                "sftp_directory": SFTP_DIRECTORY,
                "remote_path": remote_path,
                "file_name": name,
                "file_type": file_type,
                "trade_date": parsed["trade_date"],
                "file_sequence": parsed["file_sequence"],
                "submitter": parsed["submitter"],
                "reporter": parsed["reporter"],
                "file_size": int(attrs.st_size),
                "remote_modified_ts": modified_ts,
                "landing_path": None,
                "content_hash": None,
                "status": "DISCOVERED",
                "first_seen_ts": now,
                "last_seen_ts": now,
                "processing_started_ts": None,
                "processed_ts": None,
                "attempt_count": 0,
                "error_message": None,
                "created_ts": now,
                "updated_ts": now,
            }
        )
    return discovered


def upsert_discovered_files(discovered: List[Dict[str, object]]) -> List[Dict[str, object]]:
    if not discovered:
        return []
    existing_rows = {
        row.file_key: row
        for row in spark.table(REGISTRY_TABLE)
        .where(F.col("file_key").isin([row["file_key"] for row in discovered]))
        .select("file_key", "status")
        .collect()
    }
    schema = spark.table(REGISTRY_TABLE).schema
    spark.createDataFrame(discovered, schema).createOrReplaceTempView("cat_discovered_files")
    spark.sql(
        f"""
        MERGE INTO {REGISTRY_TABLE} AS target
        USING cat_discovered_files AS source
        ON target.file_key = source.file_key
        WHEN MATCHED THEN UPDATE SET
          target.last_seen_ts = source.last_seen_ts,
          target.updated_ts = source.updated_ts
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    return [
        row
        for row in discovered
        if row["file_key"] not in existing_rows or existing_rows[row["file_key"]].status == "FAILED"
    ]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_registry_processing(file_key_value: str, status: str, error_message: Optional[str] = None) -> None:
    spark.sql(
        f"""
        UPDATE {REGISTRY_TABLE}
        SET status = {sql_string(status)},
            processing_started_ts = current_timestamp(),
            attempt_count = attempt_count + 1,
            error_message = {sql_string(error_message)},
            updated_ts = current_timestamp()
        WHERE file_key = {sql_string(file_key_value)}
        """
    )


def update_registry_success(file_key_value: str, landing_path: str, content_hash: str) -> None:
    spark.sql(
        f"""
        UPDATE {REGISTRY_TABLE}
        SET status = 'SUCCESS',
            landing_path = {sql_string(landing_path)},
            content_hash = {sql_string(content_hash)},
            processed_ts = current_timestamp(),
            error_message = NULL,
            updated_ts = current_timestamp()
        WHERE file_key = {sql_string(file_key_value)}
        """
    )


def update_registry_failure(file_key_value: str, error_message: str) -> None:
    spark.sql(
        f"""
        UPDATE {REGISTRY_TABLE}
        SET status = 'FAILED',
            processed_ts = current_timestamp(),
            error_message = {sql_string(error_message[-4000:])},
            updated_ts = current_timestamp()
        WHERE file_key = {sql_string(file_key_value)}
        """
    )


def download_file(sftp, row: Dict[str, object]) -> None:
    started = datetime.now(timezone.utc)
    update_registry_processing(str(row["file_key"]), "PROCESSING")
    try:
        trade_date = row["trade_date"] or "unknown_trade_date"
        landing_dir = f"{LANDING_ROOT}/{row['file_type']}/{trade_date}/{row['file_key']}"
        landing_path = f"{landing_dir}/{row['file_name']}"
        dbutils.fs.mkdirs(landing_dir)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            local_path = tmp.name
        try:
            sftp.get(str(row["remote_path"]), local_path)
            digest = sha256_file(local_path)
            dbutils.fs.cp(f"file:{local_path}", landing_path, True)
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)
        update_registry_success(str(row["file_key"]), landing_path, digest)
        process_log(
            "00_sftp_pull",
            "SUCCESS",
            started,
            file_key=str(row["file_key"]),
            source_file_name=str(row["file_name"]),
            records_read=1,
            records_written=1,
            message=f"Landed {row['remote_path']} to {landing_path}",
        )
    except Exception as exc:
        error = f"{exc}\n{traceback.format_exc()}"
        update_registry_failure(str(row["file_key"]), error)
        process_log(
            "00_sftp_pull",
            "FAILED",
            started,
            file_key=str(row["file_key"]),
            source_file_name=str(row["file_name"]),
            records_read=1,
            records_written=0,
            exception_class=exc.__class__.__name__,
            error_message=error[-4000:],
        )
        raise


ensure_core_tables()
run_started = datetime.now(timezone.utc)
transport = None
sftp = None
try:
    transport, sftp = open_sftp_client()
    discovered_files = discover_files(sftp)
    new_files = upsert_discovered_files(discovered_files)
    files_to_download = new_files[:MAX_FILES_PER_RUN]
    failures = []
    for discovered_file in files_to_download:
        try:
            download_file(sftp, discovered_file)
        except Exception as exc:
            failures.append(f"{discovered_file['file_name']}: {exc}")
    if failures:
        raise RuntimeError("One or more CAT files failed to land: " + "; ".join(failures))
    process_log(
        "00_sftp_pull",
        "SUCCESS",
        run_started,
        records_read=len(discovered_files),
        records_written=len(files_to_download),
        message=f"Discovered {len(discovered_files)} CAT files; landed {len(files_to_download)} new file versions.",
    )
except Exception as exc:
    error = f"{exc}\n{traceback.format_exc()}"
    process_log(
        "00_sftp_pull",
        "FAILED",
        run_started,
        exception_class=exc.__class__.__name__,
        error_message=error[-4000:],
    )
    raise
finally:
    if sftp is not None:
        sftp.close()
    if transport is not None:
        transport.close()
