"""Módulo de API y rutas."""

from api.sensor import router as sensor_router
from api.sensor_magnitud import router as sensor_magnitud_router
from api.medicion import router as medicion_router

__all__ = ["sensor_router", "sensor_magnitud_router", "medicion_router"]
