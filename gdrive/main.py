"""
GDrive Microservice FastAPI Web App.
"""
import fastapi
import starlette_prometheus

from gdrive import api, export_api, analytics_api, settings
from gdrive.database import database_api

app = fastapi.FastAPI()

app.add_middleware(starlette_prometheus.PrometheusMiddleware)
app.add_route("/metrics/", starlette_prometheus.metrics)

app.include_router(api.router)
app.include_router(export_api.router)
app.include_router(analytics_api.router)
app.include_router(database_api.router)
