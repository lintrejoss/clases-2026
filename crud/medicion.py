from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.medicion import Medicion
from schemas.medicion import MedicionCreate, MedicionUpdate

def get_all(db: Session, estudiante_id: Optional[int] = None) -> List[Medicion]:
    stmt = select(Medicion).order_by(Medicion.id)
    if estudiante_id is not None:
        stmt = stmt.where(Medicion.estudiante_id == estudiante_id)
    return list(db.scalars(stmt).all())

def get(db: Session, medicion_id: int) -> Optional[Medicion]:
    return db.get(Medicion, medicion_id)

def create(db: Session, data: MedicionCreate) -> Medicion:
    medicion = Medicion(**data.model_dump())
    db.add(medicion)
    db.commit()
    db.refresh(medicion)
    return medicion

def update(db: Session, medicion: Medicion, data: MedicionUpdate) -> Medicion:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(medicion, field, value)
    db.commit()
    db.refresh(medicion)
    return medicion

def delete(db: Session, medicion: Medicion) -> None:
    db.delete(medicion)
    db.commit()
