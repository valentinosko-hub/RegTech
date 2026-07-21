"""Request-scoped dependencies.

Phase 6 will read the Databricks-forwarded identity headers here instead of
falling back to the mock user. No other code needs to change — routers
depend on `get_current_user`, never on `backend.config` directly.
"""

from fastapi import Request

from backend.config import settings
from backend.models.notifications import CurrentUser


def get_current_user(request: Request) -> CurrentUser:
    email = request.headers.get("X-Forwarded-Email", settings.mock_user_email)
    name = request.headers.get("X-Forwarded-Preferred-Username", settings.mock_user_name)
    return CurrentUser(id=email, display_name=name, email=email, role="analyst")
