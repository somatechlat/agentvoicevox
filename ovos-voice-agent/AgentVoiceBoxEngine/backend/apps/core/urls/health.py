"""
Health check URL patterns.

Endpoints:
- /health/         - Liveness probe (always returns 200 if app is running)
- /health/ready/   - Readiness probe (checks DB, Redis, Temporal)
"""

from django.urls import path

from apps.core.views.health import liveness_check, readiness_check

urlpatterns = [
    path("", liveness_check, name="health-liveness"),
    path("ready/", readiness_check, name="health-readiness"),
]
