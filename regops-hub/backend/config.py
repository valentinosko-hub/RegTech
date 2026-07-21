"""Application configuration, read from environment variables.

In Phase 1 only REGOPS_DATA_MODE and CURRENT_USER_* matter. LAKEBASE_* and
DATABRICKS_* are read here so Phase 2/3 services can pick them up without any
router or model changes.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_mode: str = os.environ.get("REGOPS_DATA_MODE", "mock")
    lakebase_connection_string: str | None = os.environ.get("LAKEBASE_CONNECTION_STRING")
    databricks_sql_warehouse_id: str | None = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID")
    databricks_catalog: str = os.environ.get("DATABRICKS_CATALOG", "regtech_ops")
    databricks_schema: str = os.environ.get("DATABRICKS_SCHEMA", "operational")

    # Mocked "current user" identity for Phase 1. In Phase 6 this is replaced
    # by reading the Databricks-forwarded identity headers on each request.
    mock_user_email: str = os.environ.get("REGOPS_MOCK_USER_EMAIL", "j.harrow@etoro.com")
    mock_user_name: str = os.environ.get("REGOPS_MOCK_USER_NAME", "Jess Harrow")


settings = Settings()
