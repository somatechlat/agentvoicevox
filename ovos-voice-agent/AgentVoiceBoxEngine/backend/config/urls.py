"""
URL configuration for AgentVoiceBox Platform.

Routes:
- /api/v2/         - Django Ninja REST API
- /api/v2/docs     - OpenAPI documentation
- /api/v2/admin/*  - Admin-only endpoints (SYSADMIN role)
- /health/         - Health check endpoints
- /metrics         - Prometheus metrics
- /admin/          - Django admin (development only)
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.core.api import api

urlpatterns = [
    # Django Ninja API (all REST endpoints)
    path("api/v2/", api.urls),
    # Health check endpoints
    path("health/", include("apps.core.urls.health")),
]

# Prometheus metrics (if installed)
try:
    urlpatterns += [
        path("", include("django_prometheus.urls")),
    ]
except ImportError:
    pass

# Django admin (only in development)
if settings.DEBUG:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

    # Debug toolbar (if installed)
    try:
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
