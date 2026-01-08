"""
Health check views.

Provides liveness and readiness probes for container orchestration.
"""

from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def liveness_check(request) -> JsonResponse:
    """
    Liveness probe endpoint.

    Returns 200 if the application is running.
    Used by Kubernetes to determine if the container should be restarted.
    """
    return JsonResponse(
        {
            "status": "ok",
            "service": "agentvoicebox-backend",
        }
    )


def readiness_check(request) -> JsonResponse:
    """
    Readiness probe endpoint.

    Checks connectivity to:
    - PostgreSQL database
    - Redis cache
    - Temporal server (if configured)

    Returns 200 if all dependencies are healthy, 503 otherwise.
    Used by Kubernetes to determine if the container should receive traffic.
    """
    checks: dict[str, dict[str, Any]] = {}
    all_healthy = True

    # Check PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = {"status": "healthy", "type": "postgresql"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Redis
    try:
        cache.set("health_check", "ok", timeout=5)
        result = cache.get("health_check")
        if result == "ok":
            checks["cache"] = {"status": "healthy", "type": "redis"}
        else:
            checks["cache"] = {
                "status": "unhealthy",
                "error": "Cache read/write failed",
            }
            all_healthy = False
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Temporal (optional)
    temporal_config = getattr(settings, "TEMPORAL", {})
    if temporal_config.get("HOST"):
        try:
            # Simple TCP check for Temporal
            import socket

            host, port = temporal_config["HOST"].split(":")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                checks["temporal"] = {
                    "status": "healthy",
                    "host": temporal_config["HOST"],
                }
            else:
                checks["temporal"] = {
                    "status": "unhealthy",
                    "error": "Connection refused",
                }
                all_healthy = False
        except Exception as e:
            checks["temporal"] = {"status": "unhealthy", "error": str(e)}
            all_healthy = False

    status_code = 200 if all_healthy else 503
    return JsonResponse(
        {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        },
        status=status_code,
    )
