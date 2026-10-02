from typing import Optional
from pydantic import BaseModel, ConfigDict

class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    correo: str
    programa: str
    grupo: str

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[str] = None
    programa: Optional[str] = None
    grupo: Optional[str] = None

class EstudianteResponse(EstudianteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
