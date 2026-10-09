"""Aplicación principal de FastAPI para el Taller 2 IoT."""

import logging
import threading
from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.sensor import router as sensor_router
from api.sensor_magnitud import router as sensor_magnitud_router
from api.medicion import router as medicion_router
from database.connection import get_db
from mqtt.client import create_mqtt_client

logger = logging.getLogger("App")

mqtt_client_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejador de ciclo de vida de la aplicación FastAPI.

    Inicia el cliente MQTT en segundo plano si la variable MQTT_AUTO_START está activa.
    """
    global mqtt_client_instance
    auto_start = os.getenv("MQTT_AUTO_START", "false").lower() in ("true", "1", "yes")

    if auto_start:
        try:
            broker = os.getenv("MQTT_BROKER", "emqx.coriotlab.co")
            port = int(os.getenv("MQTT_PORT", "1883"))
            keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
            mqtt_client_instance = create_mqtt_client()
            mqtt_client_instance.connect(broker, port, keepalive)
            mqtt_client_instance.loop_start()
            logger.info("Consumidor MQTT iniciado en segundo plano con la API.")
        except Exception as e:
            logger.error("No se pudo iniciar el consumidor MQTT automático: %s", e)

    yield

    if mqtt_client_instance is not None:
        try:
            mqtt_client_instance.loop_stop()
            mqtt_client_instance.disconnect()
            logger.info("Consumidor MQTT desconectado correctamente.")
        except Exception as e:
            logger.error("Error al desconectar consumidor MQTT: %s", e)


app = FastAPI(
    title="API de Adquisición, Validación y Consulta de Datos IoT",
    description=(
        "API REST para la adquisición de telemetría IoT mediante MQTT, "
        "validación multinivel con Pydantic y SQLAlchemy ORM, y persistencia en PostgreSQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers
app.include_router(sensor_router)
app.include_router(sensor_magnitud_router)
app.include_router(medicion_router)


@app.get("/", summary="Ruta raíz / información general")
def root():
    """Retorna información general sobre la API y su estado."""
    return {
        "status": "online",
        "service": "IoT Telemetry API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }


@app.get("/health/db", summary="Verificación de conexión con PostgreSQL")
def health_db(db: Session = Depends(get_db)):
    """Verifica que la conexión con el servidor de PostgreSQL esté funcionando correctamente."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "PostgreSQL connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
