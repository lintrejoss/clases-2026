"""Operaciones de base de datos para la entidad Medicion."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from models.medicion import Medicion
from models.sensor_magnitud import SensorMagnitud


def get_medicion_by_id(db: Session, medicion_id: int) -> Optional[Medicion]:
    """Consulta una medición por su identificador primario (id)."""
    return (
        db.query(Medicion)
        .options(joinedload(Medicion.sensor_magnitud))
        .filter(Medicion.id == medicion_id)
        .first()
    )


def get_mediciones_by_sensor(
    db: Session,
    sensor_id: int,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    magnitud: Optional[str] = None,
    limit: Optional[int] = 100,
) -> List[Medicion]:
    """Consulta el histórico de mediciones de un sensor con filtros combinados."""
    query = (
        db.query(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .options(joinedload(Medicion.sensor_magnitud))
        .filter(SensorMagnitud.sensor_id == sensor_id)
    )

    if magnitud:
        query = query.filter(SensorMagnitud.magnitud.ilike(magnitud.strip()))

    if desde:
        query = query.filter(Medicion.timestamp_utc >= desde)

    if hasta:
        query = query.filter(Medicion.timestamp_utc <= hasta)

    query = query.order_by(Medicion.timestamp_utc.desc())

    if limit is not None and limit > 0:
        query = query.limit(limit)

    return query.all()


def get_ultima_medicion_by_sensor(
    db: Session, sensor_id: int, magnitud: Optional[str] = None
) -> Optional[Medicion]:
    """Obtiene la medición más reciente de un sensor (o de una magnitud específica del sensor)."""
    query = (
        db.query(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .options(joinedload(Medicion.sensor_magnitud))
        .filter(SensorMagnitud.sensor_id == sensor_id)
    )

    if magnitud:
        query = query.filter(SensorMagnitud.magnitud.ilike(magnitud.strip()))

    return query.order_by(Medicion.timestamp_utc.desc()).first()


def create_mediciones_bulk(db: Session, items: List[dict]) -> List[Medicion]:
    """Inserta de manera atómica múltiples mediciones provenientes de un mismo payload."""
    db_items = [
        Medicion(
            sensor_magnitud_id=item["sensor_magnitud_id"],
            valor=item["valor"],
            timestamp_utc=item["timestamp_utc"],
        )
        for item in items
    ]
    db.add_all(db_items)
    db.commit()
    for item in db_items:
        db.refresh(item)
    return db_items
