# Análisis de Integración de Datos — Taller 1

**Asignatura:** Aplicaciones y Servicios Web / Integración de Sistemas  
**Componente:** Cliente Integrador Meteorológico  
**Equipo:** `EQUIPO-12-APPSWEB`  
**API Oficial:** `https://appsweb.quantaiot.co`  
**Fecha:** Septiembre 2026  

---

## 1. Comparación y Diferencias entre Contratos de los Proveedores

El sistema recibe información meteorológica proveniente de dos fuentes externas con modelos de datos, formatos de serialización y convenciones semánticas heterogéneas. A continuación, se presenta la matriz comparativa frente al contrato institucional:

### Tabla de Correspondencia de Contratos

| Campo Institucional | Tipo Requerido | Restricción / Unidad | Proveedor A (JSON) | Proveedor B (CSV) | Transformación Requerida |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ciudad`** | `string` | Obligatorio, No vacío | `station.city_name` | `municipality` | Extracción desde objeto anidado (A) o lectura directa de columna (B). Sanitización de espacios en blanco. |
| **`pais`** | `string` | Obligatorio, No vacío | `station.country_code` | `country` | Extracción anidada (A) vs. columna CSV (B). |
| **`latitud`** | `number` | [-90.0, 90.0] | `location.lat` | `latitude_deg` | Mapeo directo de float (A) vs. casteo de string a float (B). |
| **`longitud`** | `number` | [-180.0, 180.0] | `location.lon` | `longitude_deg` | Mapeo directo de float (A) vs. casteo de string a float (B). |
| **`temperatura_c`** | `number` | Numérico (°C) | `measurements.temperature_f` | `temp_celsius` | Conversión de Fahrenheit a Celsius `(°F - 32) * 5/9` (A) vs. casteo a float (B). |
| **`humedad`** | `number` | [0.0, 100.0] (%) | `measurements.relative_humidity` | `humidity_pct` | Mapeo float (A) vs. casteo de string a float (B). |
| **`viento_kmh`** | `number` | >= 0.0 (km/h) | `measurements.wind_speed_ms` | `wind_kmh` | Conversión de velocidad `m/s * 3.6` (A) vs. casteo a float (B). |
| **`fecha_hora`** | `string` | ISO 8601 válido con zona horaria | `observed_at` | `measurement_time` | Validación de formato ISO 8601 (A) vs. parseo desde `DD/MM/YYYY HH:MM` a ISO 8601 con zona horaria `-05:00` (B). |
| **`origen`** | `string` | `"proveedor_a"` \| `"proveedor_b"` | Constante institucional | Constante institucional | Asignación explícita del identificador institucional de procedencia. |
| *Identificador de Traza* | `string` | Uso interno/reporte | `provider_record_id` | `record_code` | Conservado internamente para auditoría y reporte; no se envía en el body a la API. |

---

## 2. Transformaciones Necesarias

Para homogeneizar los datos hacia el contrato institucional se desarrollaron las siguientes operaciones deterministas:

1. **Aplanamiento y Extracción Estructural:**
   - **Proveedor A:** Estructura jerárquica con sub-objetos anidados (`station`, `location`, `measurements`). Se extrajeron los campos individuales desarmando la jerarquía.
   - **Proveedor B:** Estructura tabular delimitada por punto y coma (`;`). Se mapearon los nombres de columnas a la nomenclatura canónica.
2. **Conversión de Unidades Físicas:**
   - **Temperatura:** El Proveedor A entrega grados Fahrenheit (°F). Se aplicó la fórmula estandarizada $T_C = (T_F - 32) \times \frac{5}{9}$, redondeando a 2 decimales. El Proveedor B ya entrega Celsius.
   - **Velocidad del Viento:** El Proveedor A reporta en metros por segundo (m/s). Se convirtió a kilómetros por hora multiplicando por 3.6 ($V_{km/h} = V_{m/s} \times 3.6$).
3. **Estandarización Temporal con Zona Horaria:**
   - El Proveedor A maneja marcas temporales en ISO 8601 con zona horaria (e.g. `2026-09-01T00:00:00-05:00`).
   - El Proveedor B suministra cadenas con formato tradicional `DD/MM/YYYY HH:MM` (e.g. `01/09/2026 06:00`), las cuales se transformaron a representación canónica ISO 8601 asignando la zona horaria colombiana UTC-5 (`2026-09-01T06:00:00-05:00`).
4. **Casteo Seguro de Tipos de Datos:**
   - En el CSV del Proveedor B todas las entradas ingresan como strings, requiriendo parseo explícito a tipos numéricos (`float`) con captura de excepciones.

---

## 3. Tipos de Errores Encontrados antes del Envío

Se identificó y aplicó una separación conceptual estricta entre **Errores de Normalización** y **Registros Rechazados Localmente**:

### A. Errores de Normalización (9 registros en total)
Corresponden a datos que impiden construir una instancia válida del contrato por fallas de tipo, sintaxis o ausencia irrecuperable de valores requeridos:
- **Campos Numéricos Corruptos o con Texto:** Registro `A-0082` con temperatura `"N/A"` y registro `B-0114` con temperatura `"error"`.
- **Valores Nulos / Vacíos en Campos Obligatorios:** Registro `A-0040` (`observed_at: None`), `A-0150` (`country_code: None`), `A-0173` (`temperature_f: None`), `B-0076` (fecha vacía `""`), y `B-0146` (`temp_celsius: ""`).
- **Fechas con Formato Sintácticamente Inválido:** Registro `A-0174` con fecha `"09-XX-2026 25:61"` y registro `B-0171` con fecha `"31/13/2026 28:75"` (mes 13 y hora 28 inválidos).

*Acción:* Estos registros no se envían a la API, no se incluyen en `salida/normalizadas.json` y se documentan en `salida/reporte.json`.

### B. Registros Rechazados por Validación Local (11 registros en total)
Corresponden a registros que pudieron normalizarse formalmente al esquema institucional, pero cuyos valores violan las reglas de negocio:
- **Humedad Relativa fuera de rango [0, 100]:** `A-0015` ($108.4\%$) y `B-0004` ($117.5\%$).
- **Latitud fuera de rango [-90, 90]:** `A-0031` ($95.245^\circ$) y `B-0006` ($-94.22^\circ$).
- **Longitud fuera de rango [-180, 180]:** `A-0175` ($-190.75^\circ$) y `B-0190` ($188.45^\circ$).
- **Velocidad de Viento Negativa (< 0):** `A-0088` ($-8.64\text{ km/h}$) y `B-0115` ($-7.4\text{ km/h}$).
- **Cadenas de Texto Vacías:** `A-0136` (ciudad vacía `""`), `B-0128` (ciudad vacía `""`), y `B-0135` (país vacío `""`).

*Acción:* Permanecen en `salida/normalizadas.json` pero se descartan para el envío HTTP a la API.

---

## 4. Diferencias entre Validación Local y Validación del Servidor

1. **Ámbito y Autonomía:**
   - **Validación Local:** Es ejecutada por el cliente de forma aislada y estática. Verifica tipos, rangos físicos elementales (humedad 0-100, latitud, etc.) y campos no vacíos antes de generar tráfico de red. Evita saturar el servidor con registros manifiestamente defectuosos.
   - **Validación del Servidor:** Aplica reglas globales de consistencia, unicidad, integridad referencial y restricciones de negocio en base de datos.
2. **Hallazgo en Ejecución Real:**
   - La API institucional implementa control estricto de duplicidad (`400 Bad Request: {"detail": "La medición ya existe"}`) impidiendo reinsertar dos veces la misma medición.
   - La API exige obligatoriamente zona horaria en el timestamp (`422 Unprocessable Entity: "fecha_hora debe incluir zona horaria, por ejemplo Z o -05:00"`), lo que motivó la inclusión explícita de `tzinfo` en el proceso de normalización de Proveedor B.

---

## 5. Decisión de Implementación más Importante y Justificación

**Decisión Principal:** El desacoplamiento modular en un **Pipeline por Etapas (Lectura $\rightarrow$ Normalización $\rightarrow$ Validación Local $\rightarrow$ Cliente HTTP Resiliente $\rightarrow$ Trazabilidad/Reporte)** con aislamiento total de excepciones y manejo de zona horaria.

**Justificación:**
- **Robustez y Tolerancia a Fallos:** Ningún registro defectuoso ni eventuales respuestas inesperadas interrumpen la ejecución del lote completo.
- **Auditabilidad Total:** Cada uno de los 400 registros conserva su identificador de traza (`provider_record_id` o `record_code`), permitiendo auditar con exactitud el estado final y motivo de rechazo o aceptación.
- **Resiliencia en Red:** La política de reintentos controlada (hasta 3 intentos ante 5xx/timeouts y descarte inmediato ante 4xx) protege contra tormentas de peticiones garantizando una integración confiable.

---

## 6. Evidencia de Ejecución Real con la API Oficial

### Resumen Cuantitativo de Ejecución

```json
{
  "procesados": 400,
  "normalizados": 391,
  "errores_normalizacion": 9,
  "validos_localmente": 380,
  "rechazados_localmente": 11,
  "enviados": 380,
  "total_registrados_en_servidor": 380
}
```

### Casos de Muestra de Errores y Validaciones

#### Caso 1: Error de Normalización (Dato no convertible)
- **ID de Traza:** `A-0082`
- **Fuente:** `proveedor_a.json`
- **Valor Original:** `"temperature_f": "N/A"`
- **Resultado:** Estado `ERROR_NORMALIZACION`
- **Motivo:** `Error de conversión/tipos: could not convert string to float: 'N/A'`

#### Caso 2: Rechazo en Validación Local (Regla de negocio)
- **ID de Traza:** `B-0004`
- **Fuente:** `proveedor_b.csv`
- **Valor Normalizado:** `{"ciudad": "Medellin", "humedad": 117.5, ...}`
- **Resultado:** Estado `RECHAZADO_LOCAL`
- **Motivo:** `humedad fuera de rango [0, 100]: 117.5`

#### Caso 3: Registro Válido Normalizado y Enviado
- **ID de Traza:** `A-0001`
- **Payload Enviado:**
```json
{
  "ciudad": "Medellin",
  "pais": "CO",
  "latitud": 6.242282,
  "longitud": -75.595933,
  "temperatura_c": 18.94,
  "humedad": 81.3,
  "viento_kmh": 30.49,
  "fecha_hora": "2026-09-01T00:00:00-05:00",
  "origen": "proveedor_a"
}
```
- **Respuesta API (HTTP 201 Created):**
```json
{
  "id": 2861,
  "estado": "aceptada",
  "mensaje": "Medición registrada correctamente"
}
```

### Resultado de la Consulta Final mediante GET

- **Petición:** `GET https://appsweb.quantaiot.co/api/v1/mediciones?equipo=EQUIPO-12-APPSWEB`
- **Respuesta del Servidor (HTTP 200 OK):**
```json
{
  "equipo": "EQUIPO-12-APPSWEB",
  "total": 380,
  "mediciones": [
    {
      "id": 2861,
      "ciudad": "Medellin",
      "pais": "CO",
      "latitud": 6.242282,
      "longitud": -75.595933,
      "temperatura_c": 18.94,
      "humedad": 81.3,
      "viento_kmh": 30.49,
      "fecha_hora": "2026-09-01T00:00:00-05:00",
      "origen": "proveedor_a"
    }
  ]
}
```
*Total de mediciones almacenadas exitosamente en la API institucional:* **380 / 380 mediciones válidas (100% de efectividad).**
