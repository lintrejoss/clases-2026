"""Módulo CRUD."""

from crud.sensor import get_sensores, get_sensor_by_id, get_sensor_by_codigo
from crud.sensor_magnitud import (
    get_magnitudes_by_sensor_id,
    get_sensor_magnitud_by_id,
    get_sensor_magnitud_by_sensor_and_name,
)
from crud.medicion import (
    get_medicion_by_id,
    get_mediciones_by_sensor,
    get_ultima_medicion_by_sensor,
    create_mediciones_bulk,
)

__all__ = [
    "get_sensores",
    "get_sensor_by_id",
    "get_sensor_by_codigo",
    "get_magnitudes_by_sensor_id",
    "get_sensor_magnitud_by_id",
    "get_sensor_magnitud_by_sensor_and_name",
    "get_medicion_by_id",
    "get_mediciones_by_sensor",
    "get_ultima_medicion_by_sensor",
    "create_mediciones_bulk",
]
