"""Endpoints para la consulta histórica y reciente de Mediciones."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from crud.sensor import get_sensor_by_id
from crud.medicion import (
    get_medicion_by_id,
    get_mediciones_by_sensor,
    get_ultima_medicion_by_sensor,
)
from schemas.medicion import MedicionResponse

router = APIRouter(tags=["Mediciones"])


@router.get(
    "/mediciones/{id}",
    response_model=MedicionResponse,
    summary="Consultar una medición por su ID",
)
def consultar_medicion_por_id(id: int, db: Session = Depends(get_db)):
    """Consulta los datos de una medición específica por su ID, retornando timestamps en UTC y hora local de Colombia."""
    medicion = get_medicion_by_id(db, medicion_id=id)
    if not medicion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medición con ID {id} no encontrada",
        )
    return medicion


@router.get(
    "/sensores/{id}/mediciones",
    response_model=List[MedicionResponse],
    summary="Consultar el histórico de mediciones de un sensor con filtros combinados",
)
def consultar_historico_mediciones(
    id: int,
    desde: Optional[datetime] = Query(
        None, description="Fecha y hora inicial de búsqueda en formato ISO 8601"
    ),
    hasta: Optional[datetime] = Query(
        None, description="Fecha y hora final de búsqueda en formato ISO 8601"
    ),
    magnitud: Optional[str] = Query(
        None, description="Filtrar por magnitud específica (ej. temperature, co2, humidity)"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Número máximo de mediciones a retornar (últimas N mediciones)",
    ),
    db: Session = Depends(get_db),
):
    """Consulta el histórico de mediciones registradas para un sensor.

    Permite combinar filtros por rango de fechas (desde, hasta), por tipo de magnitud
    y limitar la cantidad de resultados devueltos (últimas N mediciones).
    """
    # Validar existencia del sensor
    sensor = get_sensor_by_id(db, sensor_id=id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {id} no encontrado",
        )

    # Validar coherencia del rango de fechas
    if desde is not None and hasta is not None:
        if desde > hasta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro 'desde' no puede ser mayor que 'hasta'",
            )

    return get_mediciones_by_sensor(
        db=db,
        sensor_id=id,
        desde=desde,
        hasta=hasta,
        magnitud=magnitud,
        limit=limit,
    )


@router.get(
    "/sensores/{id}/ultima-medicion",
    response_model=MedicionResponse,
    summary="Consultar la última medición registrada de un sensor",
)
def consultar_ultima_medicion(
    id: int,
    magnitud: Optional[str] = Query(
        None, description="Opcional: filtrar por magnitud específica"
    ),
    db: Session = Depends(get_db),
):
    """Retorna la medición más reciente capturada y almacenada para el sensor indicado."""
    # Validar existencia del sensor
    sensor = get_sensor_by_id(db, sensor_id=id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {id} no encontrado",
        )

    ultima = get_ultima_medicion_by_sensor(db, sensor_id=id, magnitud=magnitud)
    if not ultima:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay mediciones registradas para el sensor con ID {id}",
        )

    return ultima
