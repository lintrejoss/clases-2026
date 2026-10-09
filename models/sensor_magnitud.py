"""Modelo ORM para la tabla sensor_magnitudes."""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from database.connection import Base


class SensorMagnitud(Base):
    """Representación de la tabla sensor_magnitudes en PostgreSQL."""

    __tablename__ = "sensor_magnitudes"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(
        Integer,
        ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    magnitud = Column(String(50), nullable=False)
    unidad = Column(String(20), nullable=False)
    valor_minimo = Column(Numeric(12, 4), nullable=False)
    valor_maximo = Column(Numeric(12, 4), nullable=False)

    # Relaciones
    sensor = relationship("Sensor", back_populates="magnitudes")
    mediciones = relationship(
        "Medicion",
        back_populates="sensor_magnitud",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
