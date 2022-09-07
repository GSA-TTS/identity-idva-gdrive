"""
GDrive Microservice FastAPI Web App.
"""
import logging

import fastapi
import starlette_prometheus

from . import api, settings

logging.basicConfig(level=settings.LOG_LEVEL)

app = fastapi.FastAPI()

app.add_middleware(starlette_prometheus.PrometheusMiddleware)
app.add_route("/metrics/", starlette_prometheus.metrics)

app.include_router(api.router)
