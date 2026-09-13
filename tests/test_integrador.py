"""
Pruebas automatizadas para el cliente integrador de datos meteorológicos.
Cubre transformaciones, conversiones de unidades, validaciones, casos límite y cliente HTTP con mocks.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch
import requests

from integrador import (
    fahrenheit_a_celsius,
    ms_a_kmh,
    normalizar_fecha_iso,
    normalizar_proveedor_a,
    normalizar_proveedor_b,
    validar_registro_institucional,
    ClienteAPI,
    PipelineIntegracion
)


# ===========================================================================
# 1. Transformaciones Correctas
# ===========================================================================
def test_transformacion_proveedor_a_correcta():
    """Prueba la transformación completa y correcta de un registro JSON del Proveedor A."""
    record_raw = {
        "provider_record_id": "A-0001",
        "station": {
            "code": "STA-01",
            "city_name": "Medellin",
            "country_code": "CO"
        },
        "location": {
            "lat": 6.242282,
            "lon": -75.595933
        },
        "measurements": {
            "temperature_f": 68.0,
            "relative_humidity": 75.5,
            "wind_speed_ms": 5.0
        },
        "observed_at": "2026-09-01T00:00:00-05:00",
        "source": "weather_provider_a"
    }

    norm, traza_id, error = normalizar_proveedor_a(record_raw, 1)

    assert error is None
    assert traza_id == "A-0001"
    assert norm is not None
    assert norm["ciudad"] == "Medellin"
    assert norm["pais"] == "CO"
    assert norm["latitud"] == 6.242282
    assert norm["longitud"] == -75.595933
    assert norm["temperatura_c"] == 20.0  # (68 - 32) * 5 / 9 = 20.0
    assert norm["humedad"] == 75.5
    assert norm["viento_kmh"] == 18.0  # 5.0 * 3.6 = 18.0
    assert norm["fecha_hora"] == "2026-09-01T00:00:00-05:00"
    assert norm["origen"] == "proveedor_a"


def test_transformacion_proveedor_b_correcta():
    """Prueba la transformación completa y correcta de una fila CSV del Proveedor B."""
    row_raw = {
        "record_code": "B-0001",
        "municipality": "Bogota",
        "country": "CO",
        "latitude_deg": "4.674047",
        "longitude_deg": "-74.092287",
        "temp_celsius": "18.5",
        "humidity_pct": "60.0",
        "wind_kmh": "12.4",
        "measurement_time": "01/09/2026 06:00",
        "origin_code": "PB"
    }

    norm, traza_id, error = normalizar_proveedor_b(row_raw, 1)

    assert error is None
    assert traza_id == "B-0001"
    assert norm is not None
    assert norm["ciudad"] == "Bogota"
    assert norm["pais"] == "CO"
    assert norm["latitud"] == 4.674047
    assert norm["longitud"] == -74.092287
    assert norm["temperatura_c"] == 18.5
    assert norm["humedad"] == 60.0
    assert norm["viento_kmh"] == 12.4
    assert norm["fecha_hora"] == "2026-09-01T06:00:00-05:00"
    assert norm["origen"] == "proveedor_b"


# ===========================================================================
# 2. Conversión de Unidades
# ===========================================================================
def test_conversion_unidades():
    """Prueba las conversiones de temperatura (°F a °C) y velocidad de viento (m/s a km/h)."""
    # 32 °F = 0 °C (punto de congelación)
    assert fahrenheit_a_celsius(32.0) == 0.0
    # 212 °F = 100 °C (punto de ebullición)
    assert fahrenheit_a_celsius(212.0) == 100.0
    # -40 °F = -40 °C (punto de coincidencia)
    assert fahrenheit_a_celsius(-40.0) == -40.0
    # 66.1 °F = 18.94 °C
    assert fahrenheit_a_celsius(66.1) == 18.94

    # 0 m/s = 0 km/h
    assert ms_a_kmh(0.0) == 0.0
    # 10 m/s = 36.0 km/h
    assert ms_a_kmh(10.0) == 36.0
    # 8.47 m/s = 30.49 km/h
    assert ms_a_kmh(8.47) == 30.49


# ===========================================================================
# 3. Registro Válido
# ===========================================================================
def test_registro_valido():
    """Prueba que un registro conforme con todas las reglas de negocio sea aceptado localmente."""
    registro = {
        "ciudad": "Cali",
        "pais": "CO",
        "latitud": 3.458315,
        "longitud": -76.521803,
        "temperatura_c": 25.24,
        "humedad": 89.2,
        "viento_kmh": 15.84,
        "fecha_hora": "2026-09-01T07:30:00",
        "origen": "proveedor_b"
    }

    es_valido, errores = validar_registro_institucional(registro)
    assert es_valido is True
    assert len(errores) == 0


# ===========================================================================
# 4. Registros Inválidos (Rechazados Localmente)
# ===========================================================================
@pytest.mark.parametrize("campo_modificado,valor_invalido,error_esperado", [
    ("humedad", 108.4, "humedad fuera de rango"),
    ("humedad", -5.0, "humedad fuera de rango"),
    ("latitud", 95.245, "latitud fuera de rango"),
    ("latitud", -91.0, "latitud fuera de rango"),
    ("longitud", 188.45, "longitud fuera de rango"),
    ("longitud", -190.75, "longitud fuera de rango"),
    ("viento_kmh", -2.4, "viento_kmh no puede ser negativo"),
    ("ciudad", "", "ciudad no puede estar vacía"),
    ("pais", "   ", "pais no puede estar vacío"),
    ("origen", "otro_proveedor", "origen no permitido")
])
def test_registro_invalido_rechazado_local(campo_modificado, valor_invalido, error_esperado):
    """Prueba que incumplimientos de reglas de negocio resulten en rechazo local."""
    base = {
        "ciudad": "Medellin",
        "pais": "CO",
        "latitud": 6.24,
        "longitud": -75.59,
        "temperatura_c": 22.0,
        "humedad": 50.0,
        "viento_kmh": 10.0,
        "fecha_hora": "2026-09-01T12:00:00",
        "origen": "proveedor_a"
    }
    base[campo_modificado] = valor_invalido

    es_valido, errores = validar_registro_institucional(base)
    assert es_valido is False
    assert any(error_esperado in err for err in errores)


# ===========================================================================
# 5. Casos Límite
# ===========================================================================
def test_caso_limite_fronteras_numericas():
    """Prueba los valores exactos en los límites de los rangos permitidos."""
    # Límites superiores e inferiores exactos
    registro_limite = {
        "ciudad": "Polo Norte",
        "pais": "AQ",
        "latitud": 90.0,
        "longitud": 180.0,
        "temperatura_c": -89.2,
        "humedad": 100.0,
        "viento_kmh": 0.0,
        "fecha_hora": "2026-09-01T00:00:00Z",
        "origen": "proveedor_a"
    }
    es_valido, errores = validar_registro_institucional(registro_limite)
    assert es_valido is True
    assert len(errores) == 0

    registro_limite_inferior = {
        "ciudad": "Polo Sur",
        "pais": "AQ",
        "latitud": -90.0,
        "longitud": -180.0,
        "temperatura_c": 0.0,
        "humedad": 0.0,
        "viento_kmh": 0.0,
        "fecha_hora": "2026-09-01T00:00:00",
        "origen": "proveedor_b"
    }
    es_valido, errores = validar_registro_institucional(registro_limite_inferior)
    assert es_valido is True
    assert len(errores) == 0


def test_error_normalizacion_datos_corruptos():
    """Prueba que datos malformados generen errores de normalización controlados sin excepciones no atrapadas."""
    # Proveedor A con temperatura "N/A"
    raw_corrupto_a = {
        "provider_record_id": "A-0082",
        "station": {"city_name": "Cali", "country_code": "CO"},
        "location": {"lat": 3.4, "lon": -76.5},
        "measurements": {"temperature_f": "N/A", "relative_humidity": 80.0, "wind_speed_ms": 2.0},
        "observed_at": "2026-09-01T00:00:00"
    }
    norm_a, traza_a, err_a = normalizar_proveedor_a(raw_corrupto_a, 82)
    assert norm_a is None
    assert traza_a == "A-0082"
    assert "Error de conversión/tipos" in err_a

    # Proveedor B con fecha inválida "31/13/2026 28:75"
    raw_corrupto_b = {
        "record_code": "B-0171",
        "municipality": "Cartagena",
        "country": "CO",
        "latitude_deg": "10.4",
        "longitude_deg": "-75.5",
        "temp_celsius": "28.0",
        "humidity_pct": "70.0",
        "wind_kmh": "15.0",
        "measurement_time": "31/13/2026 28:75",
        "origin_code": "PB"
    }
    norm_b, traza_b, err_b = normalizar_proveedor_b(raw_corrupto_b, 171)
    assert norm_b is None
    assert traza_b == "B-0171"
    assert "Error de conversión/tipos" in err_b


# ===========================================================================
# 6. Cliente HTTP, Manejo de Códigos y Reintentos
# ===========================================================================
def test_cliente_api_201_exitoso():
    """Prueba que una respuesta 201 retorne ACEPTADO_API."""
    cliente = ClienteAPI("http://fake-api.local", "test-team")
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 123, "mensaje": "Medición registrada"}

    with patch.object(cliente.session, "post", return_value=mock_resp) as mock_post:
        payload = {"ciudad": "Bogota", "pais": "CO", "temperatura_c": 20.0}
        estado, status, resp, msg = cliente.registrar_medicion(payload)

        assert estado == "ACEPTADO_API"
        assert status == 201
        assert resp["id"] == 123
        assert mock_post.call_count == 1


def test_cliente_api_4xx_rechazo_sin_reintento():
    """Prueba que errores 400/422 retornen RECHAZADO_API inmediatamente sin reintentar."""
    cliente = ClienteAPI("http://fake-api.local", "test-team")
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.json.return_value = {"error": "Validación de servidor falló"}

    with patch.object(cliente.session, "post", return_value=mock_resp) as mock_post:
        payload = {"ciudad": "Bogota"}
        estado, status, resp, msg = cliente.registrar_medicion(payload)

        assert estado == "RECHAZADO_API"
        assert status == 422
        assert mock_post.call_count == 1  # 4xx nunca se reintenta


def test_cliente_api_reintentos_5xx_y_exito():
    """Prueba que un 503 inicial sea reintentado y se recupere en el segundo intento."""
    cliente = ClienteAPI("http://fake-api.local", "test-team", max_retries=3)
    resp_503 = MagicMock()
    resp_503.status_code = 503
    resp_503.json.side_effect = ValueError("No JSON")
    resp_503.text = "Service Unavailable"

    resp_201 = MagicMock()
    resp_201.status_code = 201
    resp_201.json.return_value = {"status": "ok"}

    with patch.object(cliente.session, "post", side_effect=[resp_503, resp_201]) as mock_post:
        with patch("time.sleep", return_value=None):
            estado, status, resp, msg = cliente.registrar_medicion({"ciudad": "Cali"})

            assert estado == "ACEPTADO_API"
            assert status == 201
            assert mock_post.call_count == 2


def test_cliente_api_error_comunicacion_tras_agotar_reintentos():
    """Prueba que si 500 o fallas de red persisten tras 3 intentos, retorne ERROR_COMUNICACION."""
    cliente = ClienteAPI("http://fake-api.local", "test-team", max_retries=3)

    with patch.object(cliente.session, "post", side_effect=requests.exceptions.ConnectionError("Refused")) as mock_post:
        with patch("time.sleep", return_value=None):
            estado, status, resp, msg = cliente.registrar_medicion({"ciudad": "Cali"})

            assert estado == "ERROR_COMUNICACION"
            assert mock_post.call_count == 3
            assert "Agotados 3 intentos" in msg
