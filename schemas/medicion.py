"""Esquemas Pydantic para la entidad Medicion y validación de payloads MQTT."""

from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from database.connection import COLOMBIA_TZ


# --- Esquemas para Validación de Mensajes MQTT ---


class MQTTMeasurementDetail(BaseModel):
    """Estructura de cada magnitud dentro del mensaje MQTT."""

    value: float = Field(..., description="Valor numérico de la medición")
    unit: str = Field(..., min_length=1, description="Unidad de medida (ej. C, ppm, %)")

    @field_validator("unit")
    @classmethod
    def clean_unit(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("La unidad no puede estar vacía.")
        return v_clean


class MQTTPayloadSchema(BaseModel):
    """Validación estructural y tipado del mensaje recibido por MQTT."""

    sensor_id: str = Field(..., min_length=1, description="Código del sensor (ej. AQ-004)")
    timestamp: datetime = Field(..., description="Fecha y hora de la medición en formato ISO 8601 (UTC)")
    measurements: Dict[str, MQTTMeasurementDetail] = Field(
        ..., min_length=1, description="Diccionario de magnitudes y sus valores"
    )

    @field_validator("sensor_id")
    @classmethod
    def clean_sensor_id(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("El sensor_id no puede estar vacío.")
        return v_clean

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            # Si no viene con tz, asumimos UTC
            v = v.replace(tzinfo=timezone.utc)
        return v


# --- Esquemas de Respuesta HTTP para FastAPI ---


class MedicionResponse(BaseModel):
    """Esquema de respuesta para mediciones consultadas en la API."""

    id: int = Field(..., description="Identificador único de la medición (PK)")
    sensor_magnitud_id: int = Field(..., description="Identificador de la magnitud del sensor (FK)")
    magnitud: Optional[str] = Field(None, description="Nombre de la magnitud medida (ej. co2)")
    unidad: Optional[str] = Field(None, description="Unidad de medida (ej. ppm)")
    valor: float = Field(..., description="Valor registrado")
    timestamp_utc: datetime = Field(..., description="Fecha y hora en UTC")
    timestamp_local: datetime = Field(..., description="Fecha y hora en hora local de Colombia (UTC-5)")
    fecha_recepcion: Optional[datetime] = Field(None, description="Fecha y hora de almacenamiento en el sistema")

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def process_orm_or_dict(cls, data):
        if hasattr(data, "__dict__"):
            # Objeto ORM Medicion
            ts_utc = data.timestamp_utc
            if ts_utc is not None and ts_utc.tzinfo is None:
                ts_utc = ts_utc.replace(tzinfo=timezone.utc)
            ts_local = ts_utc.astimezone(COLOMBIA_TZ) if ts_utc else None

            mag = None
            uni = None
            if getattr(data, "sensor_magnitud", None):
                mag = data.sensor_magnitud.magnitud
                uni = data.sensor_magnitud.unidad

            return {
                "id": data.id,
                "sensor_magnitud_id": data.sensor_magnitud_id,
                "magnitud": mag,
                "unidad": uni,
                "valor": float(data.valor),
                "timestamp_utc": ts_utc,
                "timestamp_local": ts_local,
                "fecha_recepcion": getattr(data, "fecha_recepcion", None),
            }
        elif isinstance(data, dict):
            if "timestamp_local" not in data and "timestamp_utc" in data:
                ts_utc = data["timestamp_utc"]
                if isinstance(ts_utc, datetime):
                    if ts_utc.tzinfo is None:
                        ts_utc = ts_utc.replace(tzinfo=timezone.utc)
                    data["timestamp_local"] = ts_utc.astimezone(COLOMBIA_TZ)
        return data
