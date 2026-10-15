# models/medicion.py
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base  # o como se llame tu declarative_base


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False, index=True)
    variable = Column(String(50), nullable=False)
    valor = Column(Numeric, nullable=False)
    unidad = Column(String(20), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), nullable=False)

    # Relación opcional con Estudiante
    estudiante = relationship("Estudiante", back_populates="mediciones")