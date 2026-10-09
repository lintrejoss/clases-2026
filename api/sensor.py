"""Endpoints para la gestión y consulta de Sensores."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from crud.sensor import get_sensores, get_sensor_by_id, get_sensor_by_codigo
from crud.sensor_magnitud import get_magnitudes_by_sensor_id
from schemas.sensor import SensorResponse
from schemas.sensor_magnitud import SensorMagnitudResponse

router = APIRouter(tags=["Sensores"])


@router.get("/sensores", response_model=List[SensorResponse], summary="Listar todos los sensores")
def listar_sensores(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db),
):
    """Retorna la lista de sensores configurados en el sistema."""
    return get_sensores(db, skip=skip, limit=limit)


@router.get(
    "/sensores/por-codigo/{codigo}",
    response_model=SensorResponse,
    summary="Consultar un sensor por su código único",
)
def consultar_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Consulta un sensor utilizando su código de catálogo (ej. AQ-004)."""
    sensor = get_sensor_by_codigo(db, codigo=codigo)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con código '{codigo}' no encontrado",
        )
    return sensor


@router.get(
    "/sensores/{id}",
    response_model=SensorResponse,
    summary="Consultar un sensor por su ID",
)
def consultar_sensor_por_id(id: int, db: Session = Depends(get_db)):
    """Consulta los detalles de un sensor mediante su identificador numérico primario."""
    sensor = get_sensor_by_id(db, sensor_id=id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {id} no encontrado",
        )
    return sensor


@router.get(
    "/sensores/{id}/magnitudes",
    response_model=List[SensorMagnitudResponse],
    summary="Listar las magnitudes configuradas de un sensor",
)
def listar_magnitudes_sensor(id: int, db: Session = Depends(get_db)):
    """Obtiene el listado de magnitudes, unidades y rangos permitidos para un sensor específico."""
    sensor = get_sensor_by_id(db, sensor_id=id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {id} no encontrado",
        )
    return get_magnitudes_by_sensor_id(db, sensor_id=id)
