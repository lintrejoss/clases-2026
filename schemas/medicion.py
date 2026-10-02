from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MedicionBase(BaseModel):
    estudiante_id: int
    variable: str
    valor: Decimal
    unidad: str
    fecha_hora: datetime

class MedicionCreate(MedicionBase):
    pass

class MedicionUpdate(BaseModel):
    estudiante_id: Optional[int] = None
    variable: Optional[str] = None
    valor: Optional[Decimal] = None
    unidad: Optional[str] = None
    fecha_hora: Optional[datetime] = None

class MedicionResponse(MedicionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
