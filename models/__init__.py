"""Módulo de modelos ORM."""

from models.sensor import Sensor
from models.sensor_magnitud import SensorMagnitud
from models.medicion import Medicion

__all__ = ["Sensor", "SensorMagnitud", "Medicion"]
