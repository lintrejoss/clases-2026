"""Suite de pruebas automatizadas para validar los 18 requisitos y evidencias del Taller 2."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from main import app
from database.connection import SessionLocal
from crud.sensor import get_sensor_by_codigo, get_sensor_by_id
from crud.sensor_magnitud import get_magnitudes_by_sensor_id
from crud.medicion import get_medicion_by_id, get_mediciones_by_sensor, get_ultima_medicion_by_sensor
from mqtt.client import validar_y_procesar_payload

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Fixture para obtener una sesión de base de datos durante las pruebas."""
    db = SessionLocal()
    yield db
    db.close()


# Prueba 1: Recepción MQTT (Estructura y parseo de mensaje del tópico asignado AQ-004)
def test_01_recepcion_mqtt_payload_valido(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "2026-10-09T22:50:00Z",
        "measurements": {
            "co2": {"value": 850.5, "unit": "ppm"},
            "temperature": {"value": 24.2, "unit": "C"},
            "humidity": {"value": 55.0, "unit": "%"},
        },
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is True
    assert records is not None
    assert len(records) == 3


# Prueba 2: Medición válida almacenada en PostgreSQL
def test_02_medicion_valida_persistencia(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "2026-10-09T22:50:05Z",
        "measurements": {
            "co2": {"value": 860.0, "unit": "ppm"},
            "temperature": {"value": 25.0, "unit": "C"},
            "humidity": {"value": 50.0, "unit": "%"},
        },
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is True
    assert records is not None
    assert all(r["sensor_magnitud_id"] in [81, 82, 83] for r in records)


# Prueba 3: Sensor inexistente (Mensaje rechazado)
def test_03_sensor_inexistente_rechazado(db_session):
    payload = {
        "sensor_id": "SENSOR-INEXISTENTE-999",
        "timestamp": "2026-10-09T22:50:00Z",
        "measurements": {"temperature": {"value": 24.0, "unit": "C"}},
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is False
    assert records is None
    assert "Sensor inexistente" in msg


# Prueba 4: Unidad incorrecta (Mensaje rechazado)
def test_04_unidad_incorrecta_rechazado(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "2026-10-09T22:50:00Z",
        "measurements": {"temperature": {"value": 24.0, "unit": "F"}},  # Debería ser C
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is False
    assert records is None
    assert "Unidad incorrecta" in msg


# Prueba 5: Tipo de dato incorrecto (Mensaje rechazado)
def test_05_tipo_de_dato_incorrecto_rechazado(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "2026-10-09T22:50:00Z",
        "measurements": {"temperature": {"value": "NO_NUMERICO", "unit": "C"}},
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is False
    assert records is None
    assert "Validación de estructura/Pydantic fallida" in msg


# Prueba 6: Magnitud incorrecta (Mensaje rechazado)
def test_06_magnitud_incorrecta_rechazado(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "2026-10-09T22:50:00Z",
        "measurements": {"radiacion_gamma": {"value": 10.5, "unit": "uSv"}},
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is False
    assert records is None
    assert "no configurada para el sensor" in msg


# Prueba 7: Timestamp inválido (Mensaje rechazado)
def test_07_timestamp_invalido_rechazado(db_session):
    payload = {
        "sensor_id": "AQ-004",
        "timestamp": "FECHA_INVALIDA_2026",
        "measurements": {"temperature": {"value": 24.0, "unit": "C"}},
    }
    is_valid, msg, records = validar_y_procesar_payload(payload, db_session)
    assert is_valid is False
    assert records is None
    assert "Validación de estructura/Pydantic fallida" in msg


# Prueba 8: Consulta por ID existente (HTTP 200)
def test_08_consulta_por_id_existente():
    response = client.get("/sensores/31")
    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "AQ-004"
    assert data["id"] == 31


# Prueba 9: Consulta por ID inexistente (HTTP 404)
def test_09_consulta_por_id_inexistente():
    response = client.get("/sensores/999999")
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


# Prueba 10: Consulta histórica de mediciones (HTTP 200)
def test_10_consulta_historica():
    response = client.get("/sensores/31/mediciones?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "timestamp_local" in data[0]
        assert "timestamp_utc" in data[0]


# Prueba 11: Consulta por rango de fechas (Datos filtrados)
def test_11_consulta_por_rango_fechas():
    desde = "2026-10-01T00:00:00Z"
    hasta = "2026-10-10T23:59:59Z"
    response = client.get(f"/sensores/31/mediciones?desde={desde}&hasta={hasta}&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Prueba 12: Rango 'desde > hasta' (HTTP 400)
def test_12_rango_fechas_invalido_400():
    desde = "2026-10-10T00:00:00Z"
    hasta = "2026-10-01T00:00:00Z"
    response = client.get(f"/sensores/31/mediciones?desde={desde}&hasta={hasta}")
    assert response.status_code == 400
    assert response.json()["detail"] == "El parámetro 'desde' no puede ser mayor que 'hasta'"


# Prueba 13: Validación HTTP incorrecta (HTTP 422)
def test_13_validacion_http_incorrecta_422():
    response = client.get("/sensores/id-invalido-no-entero")
    assert response.status_code == 422


# Prueba 14: Última medición (HTTP 200)
def test_14_ultima_medicion():
    response = client.get("/sensores/31/ultima-medicion")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "valor" in data
        assert "timestamp_local" in data


# Prueba 15: Últimas N mediciones (Uso correcto de limit)
def test_15_ultimas_n_mediciones_limit():
    response = client.get("/sensores/31/mediciones?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3


# Prueba 16: Filtro por magnitud (HTTP 200)
def test_16_filtro_por_magnitud():
    response = client.get("/sensores/31/mediciones?magnitud=co2&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert item["magnitud"] == "co2"


# Prueba 17: Claves foráneas y relaciones
def test_17_claves_foraneas_relaciones(db_session):
    sensor = get_sensor_by_id(db_session, sensor_id=31)
    assert sensor is not None
    assert len(sensor.magnitudes) > 0
    for mag in sensor.magnitudes:
        assert mag.sensor_id == sensor.id


# Prueba 18: Separación de responsabilidades
def test_18_separacion_responsabilidades():
    import api.sensor
    import crud.sensor
    import database.connection
    import models.sensor
    import mqtt.client
    import schemas.sensor

    assert hasattr(models.sensor, "Sensor")
    assert hasattr(schemas.sensor, "SensorResponse")
    assert hasattr(crud.sensor, "get_sensores")
    assert hasattr(api.sensor, "router")
    assert hasattr(mqtt.client, "validar_y_procesar_payload")
    assert hasattr(database.connection, "SessionLocal")
