from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from crud import estudiante as crud_estudiante, medicion as crud_medicion
from database import get_db
from schemas.medicion import MedicionCreate, MedicionResponse, MedicionUpdate

router = APIRouter(prefix="/mediciones", tags=["Mediciones"])

@router.get("", response_model=List[MedicionResponse])
def listar_mediciones(
    estudiante_id: Optional[int] = Query(None, description="Filtrar por ID del estudiante"),
    db: Session = Depends(get_db),
):
    return crud_medicion.get_all(db, estudiante_id=estudiante_id)

@router.get("/{medicion_id}", response_model=MedicionResponse)
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    medicion = crud_medicion.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    return medicion

@router.post("", response_model=MedicionResponse, status_code=status.HTTP_201_CREATED)
def agregar_medicion(data: MedicionCreate, db: Session = Depends(get_db)):
    estudiante = crud_estudiante.get(db, data.estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=404, detail="El estudiante especificado no existe")
    return crud_medicion.create(db, data)

@router.put("/{medicion_id}", response_model=MedicionResponse)
def reemplazar_medicion(medicion_id: int, data: MedicionCreate, db: Session = Depends(get_db)):
    medicion = crud_medicion.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    estudiante = crud_estudiante.get(db, data.estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=404, detail="El estudiante especificado no existe")
    return crud_medicion.update(db, medicion, MedicionUpdate(**data.model_dump()))

@router.patch("/{medicion_id}", response_model=MedicionResponse)
def actualizar_medicion(medicion_id: int, data: MedicionUpdate, db: Session = Depends(get_db)):
    medicion = crud_medicion.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    if data.estudiante_id is not None:
        estudiante = crud_estudiante.get(db, data.estudiante_id)
        if estudiante is None:
            raise HTTPException(status_code=404, detail="El estudiante especificado no existe")
    return crud_medicion.update(db, medicion, data)

@router.delete("/{medicion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_medicion(medicion_id: int, db: Session = Depends(get_db)):
    medicion = crud_medicion.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    crud_medicion.delete(db, medicion)
