"""Esquemas Pydantic para la entidad Sensor."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SensorBase(BaseModel):
    """Esquema base de Sensor."""

    codigo: str = Field(..., description="Código único del sensor (ej. AQ-004)")
    nombre: str = Field(..., description="Nombre descriptivo del sensor")
    categoria: str = Field(..., description="Categoría: AIRE, GAS, AGUA o AMBIENTE")
    ubicacion: str = Field(..., description="Ubicación física del sensor")
    activo: bool = Field(default=True, description="Estado de actividad del sensor")


class SensorResponse(SensorBase):
    """Esquema de respuesta para Sensor."""

    id: int = Field(..., description="Identificador único (PK)")
    fecha_registro: datetime = Field(..., description="Fecha y hora de registro")

    model_config = ConfigDict(from_attributes=True)
