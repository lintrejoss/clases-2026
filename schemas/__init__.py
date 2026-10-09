"""Módulo de esquemas Pydantic."""

from schemas.sensor import SensorBase, SensorResponse
from schemas.sensor_magnitud import SensorMagnitudBase, SensorMagnitudResponse
from schemas.medicion import (
    MQTTMeasurementDetail,
    MQTTPayloadSchema,
    MedicionResponse,
)

__all__ = [
    "SensorBase",
    "SensorResponse",
    "SensorMagnitudBase",
    "SensorMagnitudResponse",
    "MQTTMeasurementDetail",
    "MQTTPayloadSchema",
    "MedicionResponse",
]
