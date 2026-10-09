"""Endpoints para la consulta de configuraciones de Magnitudes de Sensores."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from crud.sensor_magnitud import get_sensor_magnitud_by_id
from schemas.sensor_magnitud import SensorMagnitudResponse

router = APIRouter(tags=["Sensor Magnitudes"])


@router.get(
    "/sensor-magnitudes/{id}",
    response_model=SensorMagnitudResponse,
    summary="Consultar una configuración de magnitud por su ID",
)
def consultar_sensor_magnitud_por_id(id: int, db: Session = Depends(get_db)):
    """Consulta la configuración detallada (magnitud, unidad, rangos) de un registro de sensor_magnitud."""
    magnitud = get_sensor_magnitud_by_id(db, magnitud_id=id)
    if not magnitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración de magnitud con ID {id} no encontrada",
        )
    return magnitud
