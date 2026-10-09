"""Esquemas Pydantic para la entidad SensorMagnitud."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class SensorMagnitudBase(BaseModel):
    """Esquema base de SensorMagnitud."""

    magnitud: str = Field(..., description="Nombre de la magnitud medida (ej. temperature, co2)")
    unidad: str = Field(..., description="Unidad de medida (ej. C, ppm, %)")
    valor_minimo: Decimal = Field(..., description="Valor mínimo admitido")
    valor_maximo: Decimal = Field(..., description="Valor máximo admitido")


class SensorMagnitudResponse(SensorMagnitudBase):
    """Esquema de respuesta para SensorMagnitud."""

    id: int = Field(..., description="Identificador único (PK)")
    sensor_id: int = Field(..., description="Identificador del sensor asociado (FK)")

    model_config = ConfigDict(from_attributes=True)
