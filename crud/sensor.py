"""Operaciones de base de datos para la entidad Sensor."""

from typing import List, Optional
from sqlalchemy.orm import Session

from models.sensor import Sensor


def get_sensores(db: Session, skip: int = 0, limit: int = 100) -> List[Sensor]:
    """Obtiene el listado de todos los sensores."""
    return db.query(Sensor).offset(skip).limit(limit).all()


def get_sensor_by_id(db: Session, sensor_id: int) -> Optional[Sensor]:
    """Consulta un sensor por su identificador primario (id)."""
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def get_sensor_by_codigo(db: Session, codigo: str) -> Optional[Sensor]:
    """Consulta un sensor por su código único de catálogo (ej. AQ-004)."""
    return db.query(Sensor).filter(Sensor.codigo == codigo.strip()).first()
