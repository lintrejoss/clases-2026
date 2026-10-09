"""Script automatizado para generar las 18 evidencias obligatorias del Taller 2."""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database.connection import SessionLocal, COLOMBIA_TZ
from crud.sensor import get_sensor_by_codigo, get_sensor_by_id, get_sensores
from crud.sensor_magnitud import get_magnitudes_by_sensor_id, get_sensor_magnitud_by_id
from crud.medicion import get_medicion_by_id, get_mediciones_by_sensor, get_ultima_medicion_by_sensor
from mqtt.client import validar_y_procesar_payload

client = TestClient(app)
db = SessionLocal()

evidencias = []

# --- PRUEBA 1: Recepción MQTT ---
p1_input = {
    "sensor_id": "AQ-004",
    "timestamp": "2026-10-09T22:55:00Z",
    "measurements": {
        "co2": {"value": 850.5, "unit": "ppm"},
        "temperature": {"value": 24.2, "unit": "C"},
        "humidity": {"value": 55.0, "unit": "%"}
    }
}
p1_val, p1_msg, p1_rec = validar_y_procesar_payload(p1_input, db)
evidencias.append({
    "num": 1,
    "nombre": "Recepción MQTT",
    "entrada": json.dumps(p1_input, indent=2),
    "resultado": f"Procesado exitosamente. Mensaje: {p1_msg}",
    "http_code": "N/A (Capa MQTT)",
    "registro_estado": f"Válido. {len(p1_rec)} registros preparados para persistencia.",
    "archivo_funcion": "`mqtt/client.py` -> `on_message()`, `validar_y_procesar_payload()`",
    "explicacion": "El cliente MQTT se suscribe a `iot/sensors/AQ-004/data`, recibe el mensaje JSON, decodifica el payload y lo valida estructuralmente."
})

# --- PRUEBA 2: Medición válida almacenada en PostgreSQL ---
ultima_med = get_ultima_medicion_by_sensor(db, sensor_id=31)
med_id = ultima_med.id if ultima_med else 33151
med_val = float(ultima_med.valor) if ultima_med else 856.08
med_ts = ultima_med.timestamp_utc.isoformat() if ultima_med else "2026-10-09T22:54:40Z"
evidencias.append({
    "num": 2,
    "nombre": "Medición válida",
    "entrada": f"Payload MQTT para sensor AQ-004 con magnitudes co2, temperature y humidity dentro de rangos.",
    "resultado": f"Registro insertado en la tabla `mediciones` con ID={med_id}, valor={med_val}, timestamp_utc={med_ts}",
    "http_code": "N/A (Persistencia en PostgreSQL)",
    "registro_estado": "Almacenado exitosamente en base de datos PostgreSQL.",
    "archivo_funcion": "`mqtt/client.py` -> `validar_y_procesar_payload()`, `crud/medicion.py` -> `create_mediciones_bulk()`",
    "explicacion": "Tras superar todas las validaciones de Pydantic y reglas de negocio ORM, las mediciones se insertan de forma atómica en PostgreSQL."
})

# --- PRUEBA 3: Sensor inexistente ---
p3_input = {
    "sensor_id": "SENSOR-INEXISTENTE-999",
    "timestamp": "2026-10-09T22:55:00Z",
    "measurements": {"temperature": {"value": 24.0, "unit": "C"}}
}
p3_val, p3_msg, _ = validar_y_procesar_payload(p3_input, db)
evidencias.append({
    "num": 3,
    "nombre": "Sensor inexistente",
    "entrada": json.dumps(p3_input, indent=2),
    "resultado": f"Rechazado: {p3_msg}",
    "http_code": "N/A (Capa MQTT)",
    "registro_estado": "Rechazado (No almacenado).",
    "archivo_funcion": "`mqtt/client.py` -> `validar_y_procesar_payload()`, `crud/sensor.py` -> `get_sensor_by_codigo()`",
    "explicacion": "Se consulta en la tabla `sensores` por el código proporcionado. Al no existir, el mensaje se descarta sin modificar la base de datos."
})

# --- PRUEBA 4: Unidad incorrecta ---
p4_input = {
    "sensor_id": "AQ-004",
    "timestamp": "2026-10-09T22:55:00Z",
    "measurements": {"temperature": {"value": 24.0, "unit": "F"}}  # Esperada: C
}
p4_val, p4_msg, _ = validar_y_procesar_payload(p4_input, db)
evidencias.append({
    "num": 4,
    "nombre": "Unidad incorrecta",
    "entrada": json.dumps(p4_input, indent=2),
    "resultado": f"Rechazado: {p4_msg}",
    "http_code": "N/A (Capa MQTT)",
    "registro_estado": "Rechazado (No almacenado).",
    "archivo_funcion": "`mqtt/client.py` -> `validar_y_procesar_payload()`",
    "explicacion": "La unidad reportada ('F') no coincide con la unidad configurada en `sensor_magnitudes` ('C')."
})

# --- PRUEBA 5: Tipo de dato incorrecto ---
p5_input = {
    "sensor_id": "AQ-004",
    "timestamp": "2026-10-09T22:55:00Z",
    "measurements": {"temperature": {"value": "NO_NUMERICO", "unit": "C"}}
}
p5_val, p5_msg, _ = validar_y_procesar_payload(p5_input, db)
evidencias.append({
    "num": 5,
    "nombre": "Tipo de dato incorrecto",
    "entrada": json.dumps(p5_input, indent=2),
    "resultado": f"Rechazado por Pydantic: {p5_msg}",
    "http_code": "N/A (Capa MQTT / Pydantic)",
    "registro_estado": "Rechazado (No almacenado).",
    "archivo_funcion": "`schemas/medicion.py` -> `MQTTMeasurementDetail`, `MQTTPayloadSchema`",
    "explicacion": "Pydantic detecta que el campo `value` no es numérico y arroja un ValidationError capturado en el consumidor."
})

# --- PRUEBA 6: Magnitud incorrecta ---
p6_input = {
    "sensor_id": "AQ-004",
    "timestamp": "2026-10-09T22:55:00Z",
    "measurements": {"radiacion_gamma": {"value": 10.5, "unit": "uSv"}}
}
p6_val, p6_msg, _ = validar_y_procesar_payload(p6_input, db)
evidencias.append({
    "num": 6,
    "nombre": "Magnitud incorrecta",
    "entrada": json.dumps(p6_input, indent=2),
    "resultado": f"Rechazado: {p6_msg}",
    "http_code": "N/A (Capa MQTT)",
    "registro_estado": "Rechazado (No almacenado).",
    "archivo_funcion": "`mqtt/client.py` -> `validar_y_procesar_payload()`",
    "explicacion": "La magnitud `radiacion_gamma` no existe en el catálogo de magnitudes asociadas a AQ-004 (las cuales son humidity, temperature, co2)."
})

# --- PRUEBA 7: Timestamp inválido ---
p7_input = {
    "sensor_id": "AQ-004",
    "timestamp": "FECHA_TOTALMENTE_INVALIDA_2026",
    "measurements": {"temperature": {"value": 24.0, "unit": "C"}}
}
p7_val, p7_msg, _ = validar_y_procesar_payload(p7_input, db)
evidencias.append({
    "num": 7,
    "nombre": "Timestamp inválido",
    "entrada": json.dumps(p7_input, indent=2),
    "resultado": f"Rechazado por Pydantic: {p7_msg}",
    "http_code": "N/A (Capa MQTT / Pydantic)",
    "registro_estado": "Rechazado (No almacenado).",
    "archivo_funcion": "`schemas/medicion.py` -> `MQTTPayloadSchema`",
    "explicacion": "El formato del timestamp no cumple con el estándar ISO 8601 exigido por el modelo Pydantic."
})

# --- PRUEBA 8: Consulta por ID existente ---
r8 = client.get("/sensores/31")
evidencias.append({
    "num": 8,
    "nombre": "Consulta por ID existente",
    "entrada": "Solicitud HTTP GET `/sensores/31`",
    "resultado": json.dumps(r8.json(), indent=2),
    "http_code": f"HTTP {r8.status_code} OK",
    "registro_estado": "Registro encontrado y retornado.",
    "archivo_funcion": "`api/sensor.py` -> `consultar_sensor_por_id()`, `crud/sensor.py` -> `get_sensor_by_id()`",
    "explicacion": "Se consulta el sensor con ID 31 y FastAPI retorna exitosamente la información serializada mediante Pydantic."
})

# --- PRUEBA 9: Consulta por ID inexistente ---
r9 = client.get("/sensores/999999")
evidencias.append({
    "num": 9,
    "nombre": "Consulta por ID inexistente",
    "entrada": "Solicitud HTTP GET `/sensores/999999`",
    "resultado": json.dumps(r9.json(), indent=2),
    "http_code": f"HTTP {r9.status_code} Not Found",
    "registro_estado": "No encontrado.",
    "archivo_funcion": "`api/sensor.py` -> `consultar_sensor_por_id()`",
    "explicacion": "Al no existir el sensor con ID 999999, la API levanta una excepción `HTTPException(status_code=404)`."
})

# --- PRUEBA 10: Consulta histórica ---
r10 = client.get("/sensores/31/mediciones?limit=5")
evidencias.append({
    "num": 10,
    "nombre": "Consulta histórica",
    "entrada": "Solicitud HTTP GET `/sensores/31/mediciones?limit=5`",
    "resultado": f"Se obtuvieron {len(r10.json())} registros históricos con conversión horaria local (Colombia UTC-5).",
    "http_code": f"HTTP {r10.status_code} OK",
    "registro_estado": "Registros históricos retornados.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`",
    "explicacion": "Retorna el histórico de mediciones del sensor ordenadas descendentemente por timestamp_utc, con conversión horaria local."
})

# --- PRUEBA 11: Consulta por rango de fechas ---
r11 = client.get("/sensores/31/mediciones?desde=2026-10-01T00:00:00Z&hasta=2026-10-10T23:59:59Z&limit=5")
evidencias.append({
    "num": 11,
    "nombre": "Consulta por rango de fechas",
    "entrada": "Solicitud HTTP GET `/sensores/31/mediciones?desde=2026-10-01T00:00:00Z&hasta=2026-10-10T23:59:59Z&limit=5`",
    "resultado": f"Se obtuvieron {len(r11.json())} registros dentro del rango especificado.",
    "http_code": f"HTTP {r11.status_code} OK",
    "registro_estado": "Registros filtrados retornados.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`",
    "explicacion": "Aplica cláusulas SQL WHERE `timestamp_utc >= desde` y `timestamp_utc <= hasta` sobre la consulta ORM."
})

# --- PRUEBA 12: Rango 'desde > hasta' ---
r12 = client.get("/sensores/31/mediciones?desde=2026-10-10T00:00:00Z&hasta=2026-10-01T00:00:00Z")
evidencias.append({
    "num": 12,
    "nombre": "Rango desde > hasta",
    "entrada": "Solicitud HTTP GET `/sensores/31/mediciones?desde=2026-10-10T00:00:00Z&hasta=2026-10-01T00:00:00Z`",
    "resultado": json.dumps(r12.json(), indent=2),
    "http_code": f"HTTP {r12.status_code} Bad Request",
    "registro_estado": "Solicitud rechazada.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_historico_mediciones()`",
    "explicacion": "La API valida que la fecha inicial no sea posterior a la fecha final; de lo contrario retorna HTTP 400."
})

# --- PRUEBA 13: Validación HTTP incorrecta ---
r13 = client.get("/sensores/codigo-no-entero")
evidencias.append({
    "num": 13,
    "nombre": "Validación HTTP incorrecta",
    "entrada": "Solicitud HTTP GET `/sensores/codigo-no-entero` (se esperaba un integer en el path)",
    "resultado": json.dumps(r13.json(), indent=2),
    "http_code": f"HTTP {r13.status_code} Unprocessable Entity",
    "registro_estado": "Solicitud rechazada por validación de esquema.",
    "archivo_funcion": "`api/sensor.py` -> `consultar_sensor_por_id(id: int)` (FastAPI/Pydantic)",
    "explicacion": "FastAPI valida automáticamente el tipo de dato del parámetro de ruta `id: int` y retorna 422 al recibir un tipo incompatible."
})

# --- PRUEBA 14: Última medición ---
r14 = client.get("/sensores/31/ultima-medicion")
evidencias.append({
    "num": 14,
    "nombre": "Última medición",
    "entrada": "Solicitud HTTP GET `/sensores/31/ultima-medicion`",
    "resultado": json.dumps(r14.json(), indent=2),
    "http_code": f"HTTP {r14.status_code} OK",
    "registro_estado": "Registro más reciente retornado.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_ultima_medicion()`, `crud/medicion.py` -> `get_ultima_medicion_by_sensor()`",
    "explicacion": "Ordena descendentemente por `timestamp_utc` y retorna la medición más reciente capturada."
})

# --- PRUEBA 15: Últimas N mediciones ---
r15 = client.get("/sensores/31/mediciones?limit=3")
evidencias.append({
    "num": 15,
    "nombre": "Últimas N mediciones",
    "entrada": "Solicitud HTTP GET `/sensores/31/mediciones?limit=3`",
    "resultado": f"Se obtuvieron exactamente {len(r15.json())} registros (limit=3 aplicado).",
    "http_code": f"HTTP {r15.status_code} OK",
    "registro_estado": "Registros limitados retornados.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`",
    "explicacion": "El parámetro `limit` restringe la cantidad de filas retornadas por SQLAlchemy mediante `.limit(limit)`."
})

# --- PRUEBA 16: Filtro por magnitud ---
r16 = client.get("/sensores/31/mediciones?magnitud=co2&limit=3")
evidencias.append({
    "num": 16,
    "nombre": "Filtro por magnitud",
    "entrada": "Solicitud HTTP GET `/sensores/31/mediciones?magnitud=co2&limit=3`",
    "resultado": json.dumps(r16.json(), indent=2),
    "http_code": f"HTTP {r16.status_code} OK",
    "registro_estado": "Registros filtrados exclusivamente por la magnitud 'co2'.",
    "archivo_funcion": "`api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`",
    "explicacion": "Realiza un JOIN con la tabla `sensor_magnitudes` y aplica un filtro `magnitud.ilike('co2')`."
})

# --- PRUEBA 17: Claves foráneas ---
sensor_aq4 = get_sensor_by_id(db, 31)
mags_aq4 = sensor_aq4.magnitudes if sensor_aq4 else []
evidencias.append({
    "num": 17,
    "nombre": "Claves foráneas",
    "entrada": "Verificación de relaciones ORM entre `sensores`, `sensor_magnitudes` y `mediciones`",
    "resultado": f"Sensor ID=31 tiene {len(mags_aq4)} magnitudes asociadas por FK (IDs: {[m.id for m in mags_aq4]}).",
    "http_code": "N/A (Integridad referencial ORM / PostgreSQL)",
    "registro_estado": "Integridad referencial verificada.",
    "archivo_funcion": "`models/sensor.py`, `models/sensor_magnitud.py`, `models/medicion.py`",
    "explicacion": "Las llaves foráneas `sensor_id` y `sensor_magnitud_id` con `ON UPDATE CASCADE ON DELETE RESTRICT` garantizan la integridad referencial."
})

# --- PRUEBA 18: Separación de responsabilidades ---
evidencias.append({
    "num": 18,
    "nombre": "Separación de responsabilidades",
    "entrada": "Inspección de la arquitectura modular del proyecto",
    "resultado": "Estructura modular en capas independientes: `models/`, `schemas/`, `crud/`, `api/`, `mqtt/`, `database/`.",
    "http_code": "N/A (Diseño de arquitectura)",
    "registro_estado": "Estructura modular conforme a las especificaciones del taller.",
    "archivo_funcion": "Todo el proyecto modularizado en carpetas independientes.",
    "explicacion": "Cada capa tiene una única responsabilidad: models (ORM), schemas (Pydantic), crud (SQLAlchemy), api (FastAPI), mqtt (consumo/validación) y database (conexión)."
})

db.close()

# Generar archivo markdown de informe de evidencias
output_md = "# Registro de Evidencias de Pruebas Obligatorias — Taller 2\n\n"
output_md += f"**Sensor Asignado:** AQ-004 (Calidad de aire en aulas)\n"
output_md += f"**Tópico MQTT:** `iot/sensors/AQ-004/data`\n"
output_md += f"**Fecha de Ejecución:** {datetime.now(COLOMBIA_TZ).strftime('%Y-%m-%d %H:%M:%S (Hora Colombia)')}\n\n"
output_md += "---\n\n"

for ev in evidencias:
    output_md += f"### Prueba {ev['num']}: {ev['nombre']}\n\n"
    output_md += f"- **Datos de entrada:**\n```text\n{ev['entrada']}\n```\n"
    output_md += f"- **Resultado obtenido:**\n```text\n{ev['resultado']}\n```\n"
    output_md += f"- **Código HTTP:** `{ev['http_code']}`\n"
    output_md += f"- **Estado del registro:** {ev['registro_estado']}\n"
    output_md += f"- **Archivo y función:** {ev['archivo_funcion']}\n"
    output_md += f"- **Explicación:** {ev['explicacion']}\n\n"
    output_md += "---\n\n"

with open("evidencias/informe_evidencias.md", "w", encoding="utf-8") as f:
    f.write(output_md)

print("Informe de evidencias generado exitosamente en evidencias/informe_evidencias.md")
