# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — CAT SFTP pull (hourly)
# MAGIC
# MAGIC Discovers **new** remote objects under `/cat`, registers them idempotently, downloads to staging, and leaves rows in `DISCOVERED` for `01_parse_files`.
# MAGIC
# MAGIC **Secrets:** scope/key for `TR-S3-CAT-SSHKey` (PEM private key material). Optional secret key `CAT_SFTP_USERNAME` on the same scope.

# COMMAND ----------

# MAGIC %pip install paramiko --quiet

# COMMAND ----------

import hashlib
import io
import os
import re
import uuid
from datetime import datetime, timezone

import paramiko
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
    dbutils.widgets.text("secret_scope", "regtech-ops")
    dbutils.widgets.text("sftp_host", "transfer.s3.com")
    dbutils.widgets.text("sftp_remote_dir", "/cat")
    dbutils.widgets.text("sftp_username_secret_key", "CAT_SFTP_USERNAME")
    dbutils.widgets.text("ssh_private_key_secret_key", "TR-S3-CAT-SSHKey")
    dbutils.widgets.text("staging_dbfs_dir", "/dbfs/tmp/cat_regtechops_staging")
    dbutils.widgets.text("sftp_username_fallback", "")

_init_widgets()

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
SECRET_SCOPE = dbutils.widgets.get("secret_scope").strip()
SFTP_HOST = dbutils.widgets.get("sftp_host").strip()
SFTP_REMOTE_DIR = dbutils.widgets.get("sftp_remote_dir").strip().rstrip("/")
STAGING_DBFS = dbutils.widgets.get("staging_dbfs_dir").strip()
USERNAME_KEY = dbutils.widgets.get("sftp_username_secret_key").strip()
SSH_KEY_KEY = dbutils.widgets.get("ssh_private_key_secret_key").strip()

FQN = lambda t: f"{CATALOG}.{SCHEMA}.{t}"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

def trade_date_from_filename(name: str):
    m = re.search(r"_(\d{8})_", name)
    if not m:
        return None
    d = m.group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"

def classify_file_kind(name: str):
    n = name.lower()
    if n.endswith(".del.csv.bz2"):
        return "DELETE_SUBMISSION"
    if n.endswith(".ingestion.error.csv.bz2"):
        return "ERROR_INGESTION"
    if re.search(r"\.linkage\.error_.+\.csv\.bz2$", n):
        return "ERROR_LINKAGE"
    if n.endswith(".ack.csv"):
        return "META_ACK"
    if n.endswith(".integrity.csv"):
        return "META_INTEGRITY"
    if n.endswith(".ingestion.csv"):
        return "META_INGESTION"
    if n.endswith(".csv.bz2") and ".error." not in n:
        return "SUBMISSION"
    return None

# COMMAND ----------

def _load_ssh_key(pem: str):
    buf = io.StringIO(pem.strip())
    last_err = None
    for cls in (
        paramiko.RSAKey,
        paramiko.Ed25519Key,
        paramiko.ECDSAKey,
    ):
        try:
            buf.seek(0)
            return cls.from_private_key(buf)
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    raise RuntimeError(f"Could not parse SSH private key: {last_err}")

def _open_sftp():
    pem = dbutils.secrets.get(SECRET_SCOPE, SSH_KEY_KEY)
    key = _load_ssh_key(pem)
    try:
        username = dbutils.secrets.get(SECRET_SCOPE, USERNAME_KEY)
    except Exception:
        username = ""
    if not username:
        username = dbutils.widgets.get("sftp_username_fallback").strip()
    if not username:
        raise RuntimeError(
            f"SFTP username missing: add secret {SECRET_SCOPE}/{USERNAME_KEY} "
            "or set widget sftp_username_fallback for this job."
        )
    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=username, pkey=key)
    return paramiko.SFTPClient.from_transport(transport), transport

def _list_remote(sftp) -> list[dict]:
    out = []
    for attr in sftp.listdir_attr(SFTP_REMOTE_DIR):
        remote_path = f"{SFTP_REMOTE_DIR}/{attr.filename}"
        out.append(
            {
                "filename": attr.filename,
                "sftp_remote_path": remote_path,
                "remote_size_bytes": int(getattr(attr, "st_size", 0) or 0),
                "remote_mtime_epoch": int(attr.st_mtime),
            }
        )
    return out

# COMMAND ----------

def _job_run_id():
    for k in (
        "spark.databricks.jobRunId",
        "spark.databricks.job.runId",
        "spark.databricks.workflows.id",
    ):
        try:
            v = spark.conf.get(k, None)
            if v:
                return v
        except Exception:
            continue
    try:
        return (
            dbutils.notebook.entry_point.getDbutils()
            .notebook()
            .getContext()
            .tags()
            .apply("jobRunId")
        )
    except Exception:
        return None


JOB_RUN_ID = _job_run_id() or ("adhoc-" + str(uuid.uuid4()))

PROCESS_LOG_ID = str(uuid.uuid4())
_started = _utcnow()

plog_rows = [
    (
        PROCESS_LOG_ID,
        "00_sftp_pull",
        JOB_RUN_ID,
        _started,
        None,
        "RUNNING",
        None,
        None,
        None,
        _started,
        _started,
    )
]
plog_schema = StructType(
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
spark.createDataFrame(plog_rows, plog_schema).write.mode("append").saveAsTable(
    FQN("bi_output_regtechops_cat_process_log")
)

# COMMAND ----------

os.makedirs(STAGING_DBFS, exist_ok=True)

sftp = None
transport = None
discovered = 0
downloaded = 0
err_msg = None

try:
    sftp, transport = _open_sftp()
    remote_files = _list_remote(sftp)
    for rf in remote_files:
        fn = rf["filename"]
        fk = classify_file_kind(fn)
        if fk is None:
            continue
        td = trade_date_from_filename(fn)
        if not td:
            continue
        remote_path = rf["sftp_remote_path"]
        size_b = rf["remote_size_bytes"]
        mtime_e = rf["remote_mtime_epoch"]
        exists = spark.sql(
            f"""
            SELECT file_registry_id, registry_status, local_staging_path
            FROM {FQN("bi_output_regtechops_cat_file_registry")}
            WHERE sftp_remote_path = '{remote_path.replace("'", "''")}'
            """
        ).collect()

        if exists:
            row = exists[0]
            file_registry_id = row.file_registry_id
            if row.registry_status == "SUCCESS" and row.local_staging_path:
                continue
        else:
            file_registry_id = str(uuid.uuid4())

        local_name = hashlib.sha256(remote_path.encode()).hexdigest() + "_" + fn
        local_fs_path = os.path.join(STAGING_DBFS, local_name)

        if not exists:
            now = _utcnow()
            spark.sql(
                f"""
                INSERT INTO {FQN("bi_output_regtechops_cat_file_registry")}
                SELECT
                  '{file_registry_id}' AS file_registry_id,
                  '{remote_path.replace("'", "''")}' AS sftp_remote_path,
                  '{fn.replace("'", "''")}' AS file_name,
                  CAST('{td}' AS DATE) AS trade_date,
                  '{fk}' AS file_kind,
                  CAST({size_b} AS BIGINT) AS remote_size_bytes,
                  CAST({mtime_e} AS BIGINT) AS remote_mtime_epoch,
                  CAST(NULL AS STRING) AS local_staging_path,
                  CAST(NULL AS STRING) AS file_checksum_sha256,
                  'DISCOVERED' AS registry_status,
                  CAST('Registered from SFTP listing' AS STRING) AS status_detail,
                  '{JOB_RUN_ID.replace("'", "''")}' AS last_job_run_id,
                  CAST('{now.isoformat()}' AS TIMESTAMP) AS created_ts,
                  CAST('{now.isoformat()}' AS TIMESTAMP) AS updated_ts
                """
            )
            discovered += 1

        disk_ok = os.path.isfile(local_fs_path) and (
            size_b == 0 or os.path.getsize(local_fs_path) == size_b
        )
        if disk_ok:
            now = _utcnow()
            spark.sql(
                f"""
                UPDATE {FQN("bi_output_regtechops_cat_file_registry")}
                SET local_staging_path = '{local_fs_path.replace("'", "''")}',
                    registry_status = 'DISCOVERED',
                    status_detail = 'Download skipped (already on disk)',
                    last_job_run_id = '{JOB_RUN_ID.replace("'", "''")}',
                    updated_ts = CAST('{now.isoformat()}' AS TIMESTAMP)
                WHERE file_registry_id = '{file_registry_id}'
                """
            )
            downloaded += 1
            continue

        tmp_path = local_fs_path + ".partial"
        sftp.get(remote_path, tmp_path)
        os.replace(tmp_path, local_fs_path)
        h = hashlib.sha256()
        with open(local_fs_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        digest = h.hexdigest()
        now = _utcnow()
        spark.sql(
            f"""
            UPDATE {FQN("bi_output_regtechops_cat_file_registry")}
            SET local_staging_path = '{local_fs_path.replace("'", "''")}',
                file_checksum_sha256 = '{digest}',
                registry_status = 'DISCOVERED',
                status_detail = 'Downloaded to staging',
                last_job_run_id = '{JOB_RUN_ID.replace("'", "''")}',
                updated_ts = CAST('{now.isoformat()}' AS TIMESTAMP)
            WHERE file_registry_id = '{file_registry_id}'
            """
        )
        downloaded += 1

except Exception as e:  # noqa: BLE001
    err_msg = repr(e)
    raise
finally:
    if sftp:
        try:
            sftp.close()
        except Exception:
            pass
    if transport:
        try:
            transport.close()
        except Exception:
            pass
    _ended = _utcnow()
    status = "SUCCESS" if not err_msg else "FAILED"
    spark.sql(
        f"""
        UPDATE {FQN("bi_output_regtechops_cat_process_log")}
        SET ended_ts = CAST('{_ended.isoformat()}' AS TIMESTAMP),
            status = '{status}',
            message = {("NULL" if not err_msg else "'" + err_msg.replace("'", "''") + "'")},
            files_discovered = {discovered},
            files_processed = {downloaded},
            updated_ts = CAST('{_ended.isoformat()}' AS TIMESTAMP)
        WHERE process_log_id = '{PROCESS_LOG_ID}'
        """
    )
