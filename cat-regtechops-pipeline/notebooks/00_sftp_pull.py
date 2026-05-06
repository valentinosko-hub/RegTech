# Databricks notebook source
import hashlib
import io
import json
import os
import re
import stat
import traceback
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import paramiko
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


# COMMAND ----------
# Runtime parameters
dbutils.widgets.text("sftp_host", "transfer.s3.com")
dbutils.widgets.text("sftp_port", "22")
dbutils.widgets.text("sftp_username", "93007")
dbutils.widgets.text("sftp_remote_dir", "/cat")
dbutils.widgets.text("secret_scope", "regtech-ops")
dbutils.widgets.text("secret_key_name", "TR-S3-CAT-SSHKey")

SFTP_HOST = dbutils.widgets.get("sftp_host")
SFTP_PORT = int(dbutils.widgets.get("sftp_port"))
SFTP_USERNAME = dbutils.widgets.get("sftp_username")
SFTP_REMOTE_DIR = dbutils.widgets.get("sftp_remote_dir")
SECRET_SCOPE = dbutils.widgets.get("secret_scope")
SECRET_KEY_NAME = dbutils.widgets.get("secret_key_name")


# COMMAND ----------
# Global constants
SCHEMA = "regtech_ops_stg"
TABLE_FILE_REGISTRY = "bi_output_regtechops_cat_file_registry"
TABLE_PROCESS_LOG = "bi_output_regtechops_cat_process_log"
FILE_REGISTRY_TABLE = f"{SCHEMA}.{TABLE_FILE_REGISTRY}"
PROCESS_LOG_TABLE = f"{SCHEMA}.{TABLE_PROCESS_LOG}"

STORAGE_ROOT = "abfss://analysis@stgdpdlwe.dfs.core.windows.net/BI_OUTPUT/RegTechOps"
RAW_LANDING_BASE = f"{STORAGE_ROOT}/cat_landing/raw_sftp"
SOURCE_CONNECTION = "transfer.s3.com:/cat"
RUN_ID = str(uuid.uuid4())

KNOWN_TYPES = {
    "META_ACK",
    "META_INGESTION",
    "META_INTEGRITY",
    "SUBMISSION",
    "ERROR_INGESTION",
    "ERROR_LINKAGE",
    "DELETE",
}


# COMMAND ----------
def assert_required_tables() -> None:
    expected_tables = [
        "bi_output_regtechops_cat_file_registry",
        "bi_output_regtechops_cat_process_log",
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
            "00_sftp_pull",
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
    log_schema = StructType(
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
    spark.createDataFrame(payload, schema=log_schema).write.mode("append").saveAsTable(
        PROCESS_LOG_TABLE
    )


def classify_file_type(file_name: str) -> str:
    lower_name = file_name.lower()
    if lower_name.endswith(".ack.csv"):
        return "META_ACK"
    if lower_name.endswith(".ingestion.csv"):
        return "META_INGESTION"
    if lower_name.endswith(".integrity.csv"):
        return "META_INTEGRITY"
    if lower_name.endswith(".ingestion.error.csv.bz2"):
        return "ERROR_INGESTION"
    if re.search(r"\.linkage\.error_.*\.csv\.bz2$", lower_name):
        return "ERROR_LINKAGE"
    if lower_name.endswith(".del.csv.bz2"):
        return "DELETE"
    if lower_name.endswith(".csv.bz2"):
        return "SUBMISSION"
    return "UNKNOWN"


def extract_trade_date(file_name: str) -> Optional[str]:
    match = re.search(r"_(\d{8})_", file_name)
    return match.group(1) if match else None


def build_fingerprint(file_name: str, file_size_bytes: int, modified_epoch: int) -> str:
    return hashlib.sha256(
        f"{file_name}|{file_size_bytes}|{modified_epoch}".encode("utf-8")
    ).hexdigest()


def parse_private_key(private_key: str):
    key_reader = io.StringIO(private_key)
    key_classes = [
        paramiko.Ed25519Key,
        paramiko.RSAKey,
        paramiko.ECDSAKey,
        paramiko.DSSKey,
    ]
    for key_class in key_classes:
        key_reader.seek(0)
        try:
            return key_class.from_private_key(key_reader)
        except Exception:
            continue
    raise ValueError("Unable to parse private key from Databricks secret.")


def sha256_file(local_path: str) -> str:
    digest = hashlib.sha256()
    with open(local_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_registry_status(
    file_registry_id: str,
    lifecycle_status: str,
    parse_status: Optional[str] = None,
    enrich_status: Optional[str] = None,
    landing_path: Optional[str] = None,
    checksum_sha256: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    set_clauses = [f"lifecycle_status = '{lifecycle_status}'", "updated_ts = current_timestamp()"]
    if parse_status is not None:
        set_clauses.append(f"parse_status = '{parse_status}'")
    if enrich_status is not None:
        set_clauses.append(f"enrich_status = '{enrich_status}'")
    if landing_path is not None:
        safe_path = landing_path.replace("'", "''")
        set_clauses.append(f"landing_path = '{safe_path}'")
    if checksum_sha256 is not None:
        set_clauses.append(f"checksum_sha256 = '{checksum_sha256}'")
    if error_message is not None:
        safe_error = error_message[:4000].replace("'", "''")
        set_clauses.append(f"error_message = '{safe_error}'")

    spark.sql(
        f"""
        UPDATE {FILE_REGISTRY_TABLE}
        SET {", ".join(set_clauses)}
        WHERE file_registry_id = '{file_registry_id}'
        """
    )


# COMMAND ----------
assert_required_tables()

private_key = dbutils.secrets.get(SECRET_SCOPE, SECRET_KEY_NAME)
pkey = parse_private_key(private_key)

transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
transport.connect(username=SFTP_USERNAME, pkey=pkey)
sftp = paramiko.SFTPClient.from_transport(transport)


# COMMAND ----------
registry_schema = StructType(
    [
        StructField("file_registry_id", StringType(), False),
        StructField("file_fingerprint", StringType(), False),
        StructField("file_name", StringType(), False),
        StructField("remote_path", StringType(), False),
        StructField("file_type", StringType(), False),
        StructField("trade_date", DateType(), True),
        StructField("trade_date_str", StringType(), True),
        StructField("discovered_ts", TimestampType(), False),
        StructField("remote_modified_ts", TimestampType(), False),
        StructField("file_size_bytes", LongType(), False),
        StructField("checksum_sha256", StringType(), True),
        StructField("landing_path", StringType(), True),
        StructField("lifecycle_status", StringType(), False),
        StructField("parse_status", StringType(), False),
        StructField("enrich_status", StringType(), False),
        StructField("retry_count", IntegerType(), False),
        StructField("source_connection", StringType(), False),
        StructField("error_message", StringType(), True),
        StructField("created_ts", TimestampType(), False),
        StructField("updated_ts", TimestampType(), False),
    ]
)

remote_entries = []
for attr in sftp.listdir_attr(SFTP_REMOTE_DIR):
    if not stat.S_ISREG(attr.st_mode):
        continue
    file_name = attr.filename
    file_type = classify_file_type(file_name)
    if file_type not in KNOWN_TYPES:
        continue

    trade_date_str = extract_trade_date(file_name)
    trade_date_value = (
        datetime.strptime(trade_date_str, "%Y%m%d").date() if trade_date_str else None
    )
    modified_ts = datetime.utcfromtimestamp(int(attr.st_mtime))
    file_fingerprint = build_fingerprint(file_name, int(attr.st_size), int(attr.st_mtime))
    remote_entries.append(
        (
            str(uuid.uuid4()),
            file_fingerprint,
            file_name,
            f"{SFTP_REMOTE_DIR.rstrip('/')}/{file_name}",
            file_type,
            trade_date_value,
            trade_date_str,
            datetime.utcnow(),
            modified_ts,
            int(attr.st_size),
            None,
            None,
            "DISCOVERED",
            "PENDING",
            "PENDING",
            0,
            SOURCE_CONNECTION,
            None,
            datetime.utcnow(),
            datetime.utcnow(),
        )
    )

if not remote_entries:
    write_process_log(
        status="SUCCESS",
        records_read=0,
        records_written=0,
        details={"message": "No files available on SFTP directory."},
    )
    sftp.close()
    transport.close()
    dbutils.notebook.exit("No files found.")

remote_df = spark.createDataFrame(remote_entries, schema=registry_schema)
processed_fingerprints_df = (
    spark.table(FILE_REGISTRY_TABLE)
    .filter(F.col("lifecycle_status") == F.lit("SUCCESS"))
    .select("file_fingerprint")
    .distinct()
)
new_files_df = remote_df.join(processed_fingerprints_df, on="file_fingerprint", how="left_anti")
new_files = new_files_df.collect()

if not new_files:
    write_process_log(
        status="SUCCESS",
        records_read=remote_df.count(),
        records_written=0,
        details={"message": "No new files after idempotency check."},
    )
    sftp.close()
    transport.close()
    dbutils.notebook.exit("No new files discovered.")

new_files_df.write.mode("append").saveAsTable(FILE_REGISTRY_TABLE)

successful_downloads = 0
failed_downloads = 0
for row in new_files:
    registry_id = row["file_registry_id"]
    fingerprint = row["file_fingerprint"]
    file_name = row["file_name"]
    remote_path = row["remote_path"]
    trade_date_folder = row["trade_date_str"] if row["trade_date_str"] else "unknown_trade_date"
    landing_path = f"{RAW_LANDING_BASE}/{trade_date_folder}/{fingerprint}/{file_name}"
    local_tmp_path = f"/tmp/cat_sftp_{registry_id}_{file_name}"

    try:
        update_registry_status(registry_id, "PROCESSING", parse_status="PENDING", enrich_status="PENDING")
        sftp.get(remote_path, local_tmp_path)
        checksum = sha256_file(local_tmp_path)
        dbutils.fs.mkdirs(landing_path.rsplit("/", 1)[0])
        dbutils.fs.cp(f"file:{local_tmp_path}", landing_path)
        os.remove(local_tmp_path)

        update_registry_status(
            file_registry_id=registry_id,
            lifecycle_status="SUCCESS",
            parse_status="PENDING",
            enrich_status="PENDING",
            landing_path=landing_path,
            checksum_sha256=checksum,
            error_message=None,
        )
        successful_downloads += 1
    except Exception as exc:
        failed_downloads += 1
        update_registry_status(
            file_registry_id=registry_id,
            lifecycle_status="FAILED",
            parse_status="PENDING",
            enrich_status="PENDING",
            error_message=f"{type(exc).__name__}: {str(exc)}",
        )
        if os.path.exists(local_tmp_path):
            os.remove(local_tmp_path)

sftp.close()
transport.close()

final_status = "SUCCESS" if failed_downloads == 0 else "FAILED"
write_process_log(
    status=final_status,
    records_read=len(remote_entries),
    records_written=successful_downloads,
    details={
        "new_files_detected": str(len(new_files)),
        "successful_downloads": str(successful_downloads),
        "failed_downloads": str(failed_downloads),
        "sftp_host": SFTP_HOST,
        "remote_dir": SFTP_REMOTE_DIR,
    },
    error_message=None if failed_downloads == 0 else "One or more SFTP file downloads failed.",
)

if failed_downloads > 0:
    raise RuntimeError(
        f"SFTP pull completed with failures. successful={successful_downloads}, failed={failed_downloads}"
    )

