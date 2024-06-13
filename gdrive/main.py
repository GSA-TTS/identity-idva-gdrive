"""
GDrive Microservice FastAPI Web App.
"""

import fastapi
import starlette_prometheus
import logging

from . import api, export_api, analytics_api, debug_api, settings


log = logging.getLogger()
log.addHandler(logging.FileHandler("errors.log"))

app = fastapi.FastAPI()

app.add_middleware(starlette_prometheus.PrometheusMiddleware)
app.add_route("/metrics/", starlette_prometheus.metrics)

app.include_router(api.router)
app.include_router(export_api.router)
app.include_router(analytics_api.router)
app.include_router(debug_api.router)
