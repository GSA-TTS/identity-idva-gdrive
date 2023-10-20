"""
GDrive Microservice FastAPI Web App.
"""
import logging

import fastapi
import starlette_prometheus

from . import api, export_api, settings
from gdrive.database import database, models, api as db_api

logging.basicConfig(level=settings.LOG_LEVEL)

models.Base.metadata.create_all(bind=database.engine)

app = fastapi.FastAPI()

app.add_middleware(starlette_prometheus.PrometheusMiddleware)
app.add_route("/metrics/", starlette_prometheus.metrics)

app.include_router(api.router)
app.include_router(export_api.router)
app.include_router(db_api.router)
