# Registro de Evidencias de Pruebas Obligatorias — Taller 2

**Estudiante:** Paulina Trejos  
**Sensor Asignado:** AQ-004 (Calidad de aire en aulas)  
**Tópico MQTT:** `iot/sensors/AQ-004/data`  
**Fecha de Ejecución:** 2026-10-09 17:58:15 (Hora Colombia)

---

### Prueba 1: Recepción MQTT

- **Datos de entrada:**
```text
{
  "sensor_id": "AQ-004",
  "timestamp": "2026-10-09T22:55:00Z",
  "measurements": {
    "co2": {
      "value": 850.5,
      "unit": "ppm"
    },
    "temperature": {
      "value": 24.2,
      "unit": "C"
    },
    "humidity": {
      "value": 55.0,
      "unit": "%"
    }
  }
}
```
- **Resultado obtenido:**
```text
Procesado exitosamente. Mensaje: Payload válido (3 magnitudes verificadas)
```
- **Código HTTP:** `N/A (Capa MQTT)`
- **Estado del registro:** Válido. 3 registros preparados para persistencia.
- **Archivo y función:** `mqtt/client.py` -> `on_message()`, `validar_y_procesar_payload()`
- **Explicación:** El cliente MQTT se suscribe a `iot/sensors/AQ-004/data`, recibe el mensaje JSON, decodifica el payload y lo valida estructuralmente.

---

### Prueba 2: Medición válida

- **Datos de entrada:**
```text
Payload MQTT para sensor AQ-004 con magnitudes co2, temperature y humidity dentro de rangos.
```
- **Resultado obtenido:**
```text
Registro insertado en la tabla `mediciones` con ID=33405, valor=31.47, timestamp_utc=2026-10-09T22:58:15+00:00
```
- **Código HTTP:** `N/A (Persistencia en PostgreSQL)`
- **Estado del registro:** Almacenado exitosamente en base de datos PostgreSQL.
- **Archivo y función:** `mqtt/client.py` -> `validar_y_procesar_payload()`, `crud/medicion.py` -> `create_mediciones_bulk()`
- **Explicación:** Tras superar todas las validaciones de Pydantic y reglas de negocio ORM, las mediciones se insertan de forma atómica en PostgreSQL.

---

### Prueba 3: Sensor inexistente

- **Datos de entrada:**
```text
{
  "sensor_id": "SENSOR-INEXISTENTE-999",
  "timestamp": "2026-10-09T22:55:00Z",
  "measurements": {
    "temperature": {
      "value": 24.0,
      "unit": "C"
    }
  }
}
```
- **Resultado obtenido:**
```text
Rechazado: Sensor inexistente en base de datos: código 'SENSOR-INEXISTENTE-999'
```
- **Código HTTP:** `N/A (Capa MQTT)`
- **Estado del registro:** Rechazado (No almacenado).
- **Archivo y función:** `mqtt/client.py` -> `validar_y_procesar_payload()`, `crud/sensor.py` -> `get_sensor_by_codigo()`
- **Explicación:** Se consulta en la tabla `sensores` por el código proporcionado. Al no existir, el mensaje se descarta sin modificar la base de datos.

---

### Prueba 4: Unidad incorrecta

- **Datos de entrada:**
```text
{
  "sensor_id": "AQ-004",
  "timestamp": "2026-10-09T22:55:00Z",
  "measurements": {
    "temperature": {
      "value": 24.0,
      "unit": "F"
    }
  }
}
```
- **Resultado obtenido:**
```text
Rechazado: Unidad incorrecta para la magnitud 'temperature': esperada 'C', recibida 'F'
```
- **Código HTTP:** `N/A (Capa MQTT)`
- **Estado del registro:** Rechazado (No almacenado).
- **Archivo y función:** `mqtt/client.py` -> `validar_y_procesar_payload()`
- **Explicación:** La unidad reportada ('F') no coincide con la unidad configurada en `sensor_magnitudes` ('C').

---

### Prueba 5: Tipo de dato incorrecto

- **Datos de entrada:**
```text
{
  "sensor_id": "AQ-004",
  "timestamp": "2026-10-09T22:55:00Z",
  "measurements": {
    "temperature": {
      "value": "NO_NUMERICO",
      "unit": "C"
    }
  }
}
```
- **Resultado obtenido:**
```text
Rechazado por Pydantic: Validación de estructura/Pydantic fallida: ('measurements', 'temperature', 'value'): Input should be a valid number, unable to parse string as a number
```
- **Código HTTP:** `N/A (Capa MQTT / Pydantic)`
- **Estado del registro:** Rechazado (No almacenado).
- **Archivo y función:** `schemas/medicion.py` -> `MQTTMeasurementDetail`, `MQTTPayloadSchema`
- **Explicación:** Pydantic detecta que el campo `value` no es numérico y arroja un ValidationError capturado en el consumidor.

---

### Prueba 6: Magnitud incorrecta

- **Datos de entrada:**
```text
{
  "sensor_id": "AQ-004",
  "timestamp": "2026-10-09T22:55:00Z",
  "measurements": {
    "radiacion_gamma": {
      "value": 10.5,
      "unit": "uSv"
    }
  }
}
```
- **Resultado obtenido:**
```text
Rechazado: Magnitud 'radiacion_gamma' no configurada para el sensor 'AQ-004'. Magnitudes válidas: ['humidity', 'temperature', 'co2']
```
- **Código HTTP:** `N/A (Capa MQTT)`
- **Estado del registro:** Rechazado (No almacenado).
- **Archivo y función:** `mqtt/client.py` -> `validar_y_procesar_payload()`
- **Explicación:** La magnitud `radiacion_gamma` no existe en el catálogo de magnitudes asociadas a AQ-004 (las cuales son humidity, temperature, co2).

---

### Prueba 7: Timestamp inválido

- **Datos de entrada:**
```text
{
  "sensor_id": "AQ-004",
  "timestamp": "FECHA_TOTALMENTE_INVALIDA_2026",
  "measurements": {
    "temperature": {
      "value": 24.0,
      "unit": "C"
    }
  }
}
```
- **Resultado obtenido:**
```text
Rechazado por Pydantic: Validación de estructura/Pydantic fallida: ('timestamp',): Input should be a valid datetime or date, invalid character in year
```
- **Código HTTP:** `N/A (Capa MQTT / Pydantic)`
- **Estado del registro:** Rechazado (No almacenado).
- **Archivo y función:** `schemas/medicion.py` -> `MQTTPayloadSchema`
- **Explicación:** El formato del timestamp no cumple con el estándar ISO 8601 exigido por el modelo Pydantic.

---

### Prueba 8: Consulta por ID existente

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31`
```
- **Resultado obtenido:**
```text
{
  "codigo": "AQ-004",
  "nombre": "Calidad de aire en aulas",
  "categoria": "AIRE",
  "ubicacion": "Edificio B - aula 101",
  "activo": true,
  "id": 31,
  "fecha_registro": "2026-10-09T13:26:04.225053Z"
}
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registro encontrado y retornado.
- **Archivo y función:** `api/sensor.py` -> `consultar_sensor_por_id()`, `crud/sensor.py` -> `get_sensor_by_id()`
- **Explicación:** Se consulta el sensor con ID 31 y FastAPI retorna exitosamente la información serializada mediante Pydantic.

---

### Prueba 9: Consulta por ID inexistente

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/999999`
```
- **Resultado obtenido:**
```text
{
  "detail": "Sensor con ID 999999 no encontrado"
}
```
- **Código HTTP:** `HTTP 404 Not Found`
- **Estado del registro:** No encontrado.
- **Archivo y función:** `api/sensor.py` -> `consultar_sensor_por_id()`
- **Explicación:** Al no existir el sensor con ID 999999, la API levanta una excepción `HTTPException(status_code=404)`.

---

### Prueba 10: Consulta histórica

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/mediciones?limit=5`
```
- **Resultado obtenido:**
```text
Se obtuvieron 5 registros históricos con conversión horaria local (Colombia UTC-5).
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registros históricos retornados.
- **Archivo y función:** `api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`
- **Explicación:** Retorna el histórico de mediciones del sensor ordenadas descendentemente por timestamp_utc, con conversión horaria local.

---

### Prueba 11: Consulta por rango de fechas

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/mediciones?desde=2026-10-01T00:00:00Z&hasta=2026-10-10T23:59:59Z&limit=5`
```
- **Resultado obtenido:**
```text
Se obtuvieron 5 registros dentro del rango especificado.
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registros filtrados retornados.
- **Archivo y función:** `api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`
- **Explicación:** Aplica cláusulas SQL WHERE `timestamp_utc >= desde` y `timestamp_utc <= hasta` sobre la consulta ORM.

---

### Prueba 12: Rango desde > hasta

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/mediciones?desde=2026-10-10T00:00:00Z&hasta=2026-10-01T00:00:00Z`
```
- **Resultado obtenido:**
```text
{
  "detail": "El par\u00e1metro 'desde' no puede ser mayor que 'hasta'"
}
```
- **Código HTTP:** `HTTP 400 Bad Request`
- **Estado del registro:** Solicitud rechazada.
- **Archivo y función:** `api/medicion.py` -> `consultar_historico_mediciones()`
- **Explicación:** La API valida que la fecha inicial no sea posterior a la fecha final; de lo contrario retorna HTTP 400.

---

### Prueba 13: Validación HTTP incorrecta

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/codigo-no-entero` (se esperaba un integer en el path)
```
- **Resultado obtenido:**
```text
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "path",
        "id"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "codigo-no-entero"
    }
  ]
}
```
- **Código HTTP:** `HTTP 422 Unprocessable Entity`
- **Estado del registro:** Solicitud rechazada por validación de esquema.
- **Archivo y función:** `api/sensor.py` -> `consultar_sensor_por_id(id: int)` (FastAPI/Pydantic)
- **Explicación:** FastAPI valida automáticamente el tipo de dato del parámetro de ruta `id: int` y retorna 422 al recibir un tipo incompatible.

---

### Prueba 14: Última medición

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/ultima-medicion`
```
- **Resultado obtenido:**
```text
{
  "id": 33405,
  "sensor_magnitud_id": 81,
  "magnitud": "humidity",
  "unidad": "%",
  "valor": 31.47,
  "timestamp_utc": "2026-10-09T22:58:15Z",
  "timestamp_local": "2026-10-09T17:58:15-05:00",
  "fecha_recepcion": "2026-10-09T22:58:15.353027Z"
}
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registro más reciente retornado.
- **Archivo y función:** `api/medicion.py` -> `consultar_ultima_medicion()`, `crud/medicion.py` -> `get_ultima_medicion_by_sensor()`
- **Explicación:** Ordena descendentemente por `timestamp_utc` y retorna la medición más reciente capturada.

---

### Prueba 15: Últimas N mediciones

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/mediciones?limit=3`
```
- **Resultado obtenido:**
```text
Se obtuvieron exactamente 3 registros (limit=3 aplicado).
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registros limitados retornados.
- **Archivo y función:** `api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`
- **Explicación:** El parámetro `limit` restringe la cantidad de filas retornadas por SQLAlchemy mediante `.limit(limit)`.

---

### Prueba 16: Filtro por magnitud

- **Datos de entrada:**
```text
Solicitud HTTP GET `/sensores/31/mediciones?magnitud=co2&limit=3`
```
- **Resultado obtenido:**
```text
[
  {
    "id": 33403,
    "sensor_magnitud_id": 83,
    "magnitud": "co2",
    "unidad": "ppm",
    "valor": 1315.92,
    "timestamp_utc": "2026-10-09T22:58:15Z",
    "timestamp_local": "2026-10-09T17:58:15-05:00",
    "fecha_recepcion": "2026-10-09T22:58:15.353027Z"
  },
  {
    "id": 33397,
    "sensor_magnitud_id": 83,
    "magnitud": "co2",
    "unidad": "ppm",
    "valor": 879.47,
    "timestamp_utc": "2026-10-09T22:58:10Z",
    "timestamp_local": "2026-10-09T17:58:10-05:00",
    "fecha_recepcion": "2026-10-09T22:58:10.439368Z"
  },
  {
    "id": 33391,
    "sensor_magnitud_id": 83,
    "magnitud": "co2",
    "unidad": "ppm",
    "valor": 512.61,
    "timestamp_utc": "2026-10-09T22:58:05Z",
    "timestamp_local": "2026-10-09T17:58:05-05:00",
    "fecha_recepcion": "2026-10-09T22:58:05.317655Z"
  }
]
```
- **Código HTTP:** `HTTP 200 OK`
- **Estado del registro:** Registros filtrados exclusivamente por la magnitud 'co2'.
- **Archivo y función:** `api/medicion.py` -> `consultar_historico_mediciones()`, `crud/medicion.py` -> `get_mediciones_by_sensor()`
- **Explicación:** Realiza un JOIN con la tabla `sensor_magnitudes` y aplica un filtro `magnitud.ilike('co2')`.

---

### Prueba 17: Claves foráneas

- **Datos de entrada:**
```text
Verificación de relaciones ORM entre `sensores`, `sensor_magnitudes` y `mediciones`
```
- **Resultado obtenido:**
```text
Sensor ID=31 tiene 3 magnitudes asociadas por FK (IDs: [81, 82, 83]).
```
- **Código HTTP:** `N/A (Integridad referencial ORM / PostgreSQL)`
- **Estado del registro:** Integridad referencial verificada.
- **Archivo y función:** `models/sensor.py`, `models/sensor_magnitud.py`, `models/medicion.py`
- **Explicación:** Las llaves foráneas `sensor_id` y `sensor_magnitud_id` con `ON UPDATE CASCADE ON DELETE RESTRICT` garantizan la integridad referencial.

---

### Prueba 18: Separación de responsabilidades

- **Datos de entrada:**
```text
Inspección de la arquitectura modular del proyecto
```
- **Resultado obtenido:**
```text
Estructura modular en capas independientes: `models/`, `schemas/`, `crud/`, `api/`, `mqtt/`, `database/`.
```
- **Código HTTP:** `N/A (Diseño de arquitectura)`
- **Estado del registro:** Estructura modular conforme a las especificaciones del taller.
- **Archivo y función:** Todo el proyecto modularizado en carpetas independientes.
- **Explicación:** Cada capa tiene una única responsabilidad: models (ORM), schemas (Pydantic), crud (SQLAlchemy), api (FastAPI), mqtt (consumo/validación) y database (conexión).

---

