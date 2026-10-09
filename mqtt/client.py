"""Cliente y procesador de mensajes MQTT para adquisición y validación de datos IoT."""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from crud.sensor import get_sensor_by_codigo
from crud.sensor_magnitud import get_magnitudes_by_sensor_id
from crud.medicion import create_mediciones_bulk
from schemas.medicion import MQTTPayloadSchema

load_dotenv()

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("MQTTConsumer")

# Variables de entorno
BROKER = os.getenv("MQTT_BROKER", "emqx.coriotlab.co")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/AQ-004/data")
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))


def validar_y_procesar_payload(
    payload_data: Any, db: Session
) -> Tuple[bool, str, Optional[List[dict]]]:
    """Valida un payload MQTT mediante Pydantic y reglas de negocio ORM.

    Reglas aplicadas:
    1. Decodificación y parseo JSON válido.
    2. Validación estructural con Pydantic (tipos, campos, timestamp ISO 8601 UTC).
    3. Validación de negocio ORM:
       - Sensor existente en base de datos.
       - Sensor en estado activo (activo == True).
       - Cada magnitud reportada debe estar asociada al sensor en `sensor_magnitudes`.
       - La unidad debe coincidir exactamente con la unidad configurada para esa magnitud.
       - El valor debe encontrarse dentro del rango permitido [valor_minimo, valor_maximo].
    4. Atomicidad: Si cualquiera de las magnitudes falla, TODO el payload se rechaza.

    Retorna:
        Tuple[bool, str, Optional[List[dict]]]:
        - bool: True si es válido y procesable, False si fue rechazado.
        - str: Mensaje descriptivo del resultado o razón de rechazo.
        - Optional[List[dict]]: Lista de registros listos para insertar si es válido.
    """
    # 1. Validación de tipo/JSON
    if isinstance(payload_data, (str, bytes)):
        try:
            payload_dict = json.loads(payload_data)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            reason = f"Error de decodificación JSON: {err}"
            logger.warning("PAYLOAD RECHAZADO - %s", reason)
            return False, reason, None
    elif isinstance(payload_data, dict):
        payload_dict = payload_data
    else:
        reason = f"Tipo de payload inválido: {type(payload_data).__name__}"
        logger.warning("PAYLOAD RECHAZADO - %s", reason)
        return False, reason, None

    # 2. Validación de estructura con Pydantic
    try:
        validated_payload = MQTTPayloadSchema(**payload_dict)
    except ValidationError as val_err:
        errors_summary = "; ".join(
            f"{e['loc']}: {e['msg']}" for e in val_err.errors()
        )
        reason = f"Validación de estructura/Pydantic fallida: {errors_summary}"
        logger.warning("PAYLOAD RECHAZADO - %s", reason)
        return False, reason, None

    # 3. Validación ORM: Existencia y estado del sensor
    sensor_codigo = validated_payload.sensor_id
    sensor = get_sensor_by_codigo(db, codigo=sensor_codigo)
    if not sensor:
        reason = f"Sensor inexistente en base de datos: código '{sensor_codigo}'"
        logger.warning("PAYLOAD RECHAZADO - %s", reason)
        return False, reason, None

    if not sensor.activo:
        reason = f"Sensor inactivo: código '{sensor_codigo}'"
        logger.warning("PAYLOAD RECHAZADO - %s", reason)
        return False, reason, None

    # 4. Obtener magnitudes configuradas para este sensor
    magnitudes_configuradas = get_magnitudes_by_sensor_id(db, sensor_id=sensor.id)
    if not magnitudes_configuradas:
        reason = f"El sensor '{sensor_codigo}' no tiene magnitudes configuradas en la base de datos"
        logger.warning("PAYLOAD RECHAZADO - %s", reason)
        return False, reason, None

    magnitudes_map = {m.magnitud.lower(): m for m in magnitudes_configuradas}

    # 5. Validar todas las magnitudes del payload (Comprobación Atómica)
    records_to_insert: List[dict] = []
    ts_utc = validated_payload.timestamp
    if ts_utc.tzinfo is None:
        ts_utc = ts_utc.replace(tzinfo=timezone.utc)

    for mag_name, meas_detail in validated_payload.measurements.items():
        mag_key = mag_name.strip().lower()

        # a. ¿Existe la magnitud para este sensor?
        if mag_key not in magnitudes_map:
            reason = (
                f"Magnitud '{mag_name}' no configurada para el sensor '{sensor_codigo}'. "
                f"Magnitudes válidas: {list(magnitudes_map.keys())}"
            )
            logger.warning("PAYLOAD RECHAZADO - %s", reason)
            return False, reason, None

        mag_conf = magnitudes_map[mag_key]

        # b. ¿Coincide la unidad de medida?
        unit_recibida = meas_detail.unit.strip()
        unit_esperada = mag_conf.unidad.strip()
        if unit_recibida != unit_esperada:
            reason = (
                f"Unidad incorrecta para la magnitud '{mag_name}': "
                f"esperada '{unit_esperada}', recibida '{unit_recibida}'"
            )
            logger.warning("PAYLOAD RECHAZADO - %s", reason)
            return False, reason, None

        # c. ¿El valor está en el rango permitido [min, max]?
        valor_dec = Decimal(str(meas_detail.value))
        if valor_dec < mag_conf.valor_minimo or valor_dec > mag_conf.valor_maximo:
            reason = (
                f"Valor fuera de rango para '{mag_name}': valor={valor_dec} "
                f"fuera del rango [{mag_conf.valor_minimo}, {mag_conf.valor_maximo}]"
            )
            logger.warning("PAYLOAD RECHAZADO - %s", reason)
            return False, reason, None

        records_to_insert.append({
            "sensor_magnitud_id": mag_conf.id,
            "valor": valor_dec,
            "timestamp_utc": ts_utc,
            "magnitud": mag_conf.magnitud,
        })

    # Si todas las magnitudes pasaron la validación
    return True, f"Payload válido ({len(records_to_insert)} magnitudes verificadas)", records_to_insert


def on_connect(client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties=None):
    """Callback ejecutado al conectar exitosamente con el broker MQTT."""
    if reason_code != 0:
        logger.error("Error al conectar con el broker MQTT. Código: %s", reason_code)
        return

    logger.info("Conectado exitosamente al broker MQTT %s:%s", BROKER, PORT)
    result, _ = client.subscribe(TOPIC)
    if result != mqtt.MQTT_ERR_SUCCESS:
        logger.error("No fue posible suscribirse a %s. Código: %s", TOPIC, result)
        return

    logger.info("Suscrito exitosamente al tópico: %s", TOPIC)
    logger.info("Esperando mensajes... Procesamiento continuo activo.")


def on_message(client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage):
    """Callback invocado ante la llegada de un nuevo mensaje MQTT."""
    payload_str = message.payload.decode("utf-8", errors="replace")
    logger.info("Mensaje recibido en [%s]: %s", message.topic, payload_str)

    db: Session = SessionLocal()
    try:
        is_valid, msg, records = validar_y_procesar_payload(payload_str, db)
        if is_valid and records:
            inserted = create_mediciones_bulk(db, records)
            logger.info(
                "EXITO: Se almacenaron %d registros de medición en PostgreSQL (IDs: %s)",
                len(inserted),
                [r.id for r in inserted],
            )
        else:
            logger.info("RESULTADO: Mensaje descartado -> %s", msg)
    except Exception as exc:
        db.rollback()
        logger.error("Error inesperado al procesar mensaje MQTT: %s", exc, exc_info=True)
    finally:
        db.close()


def create_mqtt_client() -> mqtt.Client:
    """Crea y configura el cliente MQTT con sus respectivos callbacks."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if USERNAME:
        client.username_pw_set(USERNAME, PASSWORD or "")

    client.on_connect = on_connect
    client.on_message = on_message
    return client


def start_mqtt_listener():
    """Inicia el bucle de escucha del cliente MQTT de forma bloqueante."""
    if not BROKER:
        raise RuntimeError("Falta configurar MQTT_BROKER en las variables de entorno.")

    client = create_mqtt_client()
    logger.info("Iniciando conexión a %s:%d...", BROKER, PORT)
    client.connect(BROKER, PORT, KEEPALIVE)
    client.loop_forever()


if __name__ == "__main__":
    try:
        start_mqtt_listener()
    except KeyboardInterrupt:
        logger.info("Consumidor MQTT detenido por el usuario.")
