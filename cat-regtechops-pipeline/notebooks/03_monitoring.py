# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Monitoring & reconciliation checks
# MAGIC
# MAGIC Read-only SQL over `regtech_ops_stg.bi_output_regtechops_*` for hourly health: file lifecycle, ingestion volume, reject ratio, dictionary coverage, and recent failures.

# COMMAND ----------

def _init_widgets():
    dbutils.widgets.text("catalog", "hive_metastore")
    dbutils.widgets.text("schema", "regtech_ops_stg")
    dbutils.widgets.text("trade_date_filter", "")


_init_widgets()

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
TD = dbutils.widgets.get("trade_date_filter").strip()
FQN = lambda t: f"{CATALOG}.{SCHEMA}.{t}"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

td_clause = ""
if TD:
    safe_td = TD.replace("'", "''")
    td_clause = f"WHERE trade_date = CAST('{safe_td}' AS DATE)"

# COMMAND ----------

# MAGIC %md
# MAGIC ## File registry by status

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT registry_status, file_kind, COUNT(*) AS files
        FROM {FQN("bi_output_regtechops_cat_file_registry")}
        {td_clause}
        GROUP BY registry_status, file_kind
        ORDER BY registry_status, file_kind
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Submission vs rejection (trade status)

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT trade_date, status, COUNT(*) AS rows
        FROM {FQN("bi_output_regtechops_cat_trade_status")}
        {td_clause}
        GROUP BY trade_date, status
        ORDER BY trade_date DESC, status
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Error enrichment — dictionary hit rate

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT dictionary_hit, COUNT(*) AS err_rows
        FROM {FQN("bi_output_regtechops_cat_enriched_errors")}
        {td_clause}
        GROUP BY dictionary_hit
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Recent FAILED files

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT file_name, trade_date, file_kind, status_detail, updated_ts
        FROM {FQN("bi_output_regtechops_cat_file_registry")}
        WHERE registry_status = 'FAILED'
        ORDER BY updated_ts DESC
        LIMIT 50
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Meta feedback (canonical sample shape — INGESTION)

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT meta_subtype, stage, status, severity, error_code, error_count, total_records_count, referenced_file_name
        FROM {FQN("bi_output_regtechops_cat_meta_feedback")}
        WHERE meta_subtype = 'INGESTION'
        ORDER BY updated_ts DESC
        LIMIT 20
        """
    )
)
