"""
GDrive Microservice FastAPI Web App.
"""
import fastapi
import starlette_prometheus

from . import api, export_api, analytics_api, archive_api, settings

app = fastapi.FastAPI()

app.add_middleware(starlette_prometheus.PrometheusMiddleware)
app.add_route("/metrics/", starlette_prometheus.metrics)

app.include_router(api.router)
app.include_router(export_api.router)
app.include_router(analytics_api.router)
app.include_router(archive_api.router)
