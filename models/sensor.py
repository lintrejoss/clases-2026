"""Modelo ORM para la tabla sensores."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from database.connection import Base


class Sensor(Base):
    """Representación de la tabla sensores en PostgreSQL."""

    __tablename__ = "sensores"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(30), nullable=False)
    ubicacion = Column(String(100), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_registro = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relación uno a muchos con sensor_magnitudes
    magnitudes = relationship(
        "SensorMagnitud",
        back_populates="sensor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
