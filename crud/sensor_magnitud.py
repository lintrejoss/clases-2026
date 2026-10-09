"""Operaciones de base de datos para la entidad SensorMagnitud."""

from typing import List, Optional
from sqlalchemy.orm import Session

from models.sensor_magnitud import SensorMagnitud


def get_magnitudes_by_sensor_id(db: Session, sensor_id: int) -> List[SensorMagnitud]:
    """Obtiene todas las magnitudes configuradas para un sensor dado."""
    return db.query(SensorMagnitud).filter(SensorMagnitud.sensor_id == sensor_id).all()


def get_sensor_magnitud_by_id(db: Session, magnitud_id: int) -> Optional[SensorMagnitud]:
    """Consulta una configuración de magnitud por su identificador primario (id)."""
    return db.query(SensorMagnitud).filter(SensorMagnitud.id == magnitud_id).first()


def get_sensor_magnitud_by_sensor_and_name(
    db: Session, sensor_id: int, magnitud: str
) -> Optional[SensorMagnitud]:
    """Consulta la configuración de una magnitud específica de un sensor por nombre."""
    return (
        db.query(SensorMagnitud)
        .filter(
            SensorMagnitud.sensor_id == sensor_id,
            SensorMagnitud.magnitud.ilike(magnitud.strip()),
        )
        .first()
    )
