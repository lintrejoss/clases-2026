#!/usr/bin/env python3
"""
Taller 1 — Integración de datos entre aplicaciones
Cliente integrador de datos meteorológicos.
"""

import os
import sys
import json
import csv
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional
import requests

# ---------------------------------------------------------------------------
# 13. Configuración y Constantes
# ---------------------------------------------------------------------------
URL_BASE = os.environ.get("URL_BASE", "https://appsweb.quantaiot.co").rstrip("/")
EQUIPO = os.environ.get("EQUIPO", "EQUIPO-12-APPSWEB")
TIMEOUT_HTTP = float(os.environ.get("TIMEOUT_HTTP", "5.0"))
MAX_RETRIES = 3  # 1 intento inicial + hasta 2 reintentos

DIRECTORIO_DATOS = "datos"
DIRECTORIO_SALIDA = "salida"
ARCHIVO_PROV_A = os.path.join(DIRECTORIO_DATOS, "proveedor_a.json")
ARCHIVO_PROV_B = os.path.join(DIRECTORIO_DATOS, "proveedor_b.csv")
ARCHIVO_NORMALIZADAS = os.path.join(DIRECTORIO_SALIDA, "normalizadas.json")
ARCHIVO_REPORTE = os.path.join(DIRECTORIO_SALIDA, "reporte.json")

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("IntegradorMeteorologico")


# ---------------------------------------------------------------------------
# 3. Funciones de Conversión y Normalización
# ---------------------------------------------------------------------------
def fahrenheit_a_celsius(temp_f: float) -> float:
    """Convierte grados Fahrenheit a Celsius: (F - 32) * 5 / 9."""
    return round((temp_f - 32.0) * 5.0 / 9.0, 2)


def ms_a_kmh(speed_ms: float) -> float:
    """Convierte velocidad de metros por segundo a kilómetros por hora: ms * 3.6."""
    return round(speed_ms * 3.6, 2)


def parse_iso_datetime(fecha_str: str) -> datetime:
    """Parsea una cadena ISO 8601 compatible con Python 3.9+ (soportando sufijo 'Z')."""
    s = str(fecha_str).strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def normalizar_fecha_iso(
    fecha_raw: Any,
    formato_origen: Optional[str] = None,
    tz_default: Optional[timezone] = timezone(timedelta(hours=-5))
) -> str:
    """
    Convierte o valida una fecha a formato ISO 8601 string con zona horaria.
    Lanza ValueError si la fecha no es válida.
    """
    if fecha_raw is None:
        raise ValueError("Fecha ausente (None)")
    
    fecha_str = str(fecha_raw).strip()
    if not fecha_str:
        raise ValueError("Fecha vacía")

    if formato_origen:
        # Ejemplo: DD/MM/YYYY HH:MM
        dt = datetime.strptime(fecha_str, formato_origen)
        if tz_default and dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_default)
        return dt.isoformat()
    else:
        # Validación de ISO 8601
        dt = parse_iso_datetime(fecha_str)
        if tz_default and dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_default)
            return dt.isoformat()
        return fecha_str


def normalizar_proveedor_a(raw_record: Dict[str, Any], indice: int) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normaliza un registro del Proveedor A (JSON jerárquico).
    Retorna: (registro_normalizado, id_trazabilidad, error_mensaje)
    """
    traza_id = raw_record.get("provider_record_id") if isinstance(raw_record, dict) else None
    if not traza_id:
        traza_id = f"PROV_A_{indice:04d}"

    try:
        if not isinstance(raw_record, dict):
            return None, traza_id, "Estructura de registro no es un objeto/diccionario"

        station = raw_record.get("station")
        location = raw_record.get("location")
        measurements = raw_record.get("measurements")

        if not isinstance(station, dict) or not isinstance(location, dict) or not isinstance(measurements, dict):
            return None, traza_id, "Bloques station, location o measurements ausentes o inválidos"

        # Extracción y casteo de tipos para contrato institucional
        ciudad = station.get("city_name")
        if ciudad is None:
            return None, traza_id, "Campo city_name ausente (None)"
        ciudad = str(ciudad)

        pais = station.get("country_code")
        if pais is None:
            return None, traza_id, "Campo country_code ausente (None)"
        pais = str(pais)

        lat_raw = location.get("lat")
        lon_raw = location.get("lon")
        if lat_raw is None or lon_raw is None:
            return None, traza_id, "Coordenadas lat/lon ausentes (None)"
        latitud = float(lat_raw)
        longitud = float(lon_raw)

        temp_f_raw = measurements.get("temperature_f")
        rh_raw = measurements.get("relative_humidity")
        wind_ms_raw = measurements.get("wind_speed_ms")

        if temp_f_raw is None or rh_raw is None or wind_ms_raw is None:
            return None, traza_id, "Mediciones (temperatura_f, relative_humidity o wind_speed_ms) ausentes (None)"

        temperatura_c = fahrenheit_a_celsius(float(temp_f_raw))
        humedad = round(float(rh_raw), 2)
        viento_kmh = ms_a_kmh(float(wind_ms_raw))

        obs_raw = raw_record.get("observed_at")
        fecha_hora = normalizar_fecha_iso(obs_raw)

        registro_norm = {
            "ciudad": ciudad,
            "pais": pais,
            "latitud": latitud,
            "longitud": longitud,
            "temperatura_c": temperatura_c,
            "humedad": humedad,
            "viento_kmh": viento_kmh,
            "fecha_hora": fecha_hora,
            "origen": "proveedor_a"
        }
        return registro_norm, traza_id, None

    except Exception as e:
        return None, traza_id, f"Error de conversión/tipos: {str(e)}"


def normalizar_proveedor_b(raw_row: Dict[str, Any], indice: int) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Normaliza una fila del Proveedor B (CSV plano con delimitador ';').
    Retorna: (registro_normalizado, id_trazabilidad, error_mensaje)
    """
    traza_id = raw_row.get("record_code") if isinstance(raw_row, dict) else None
    if not traza_id or not str(traza_id).strip():
        traza_id = f"PROV_B_{indice:04d}"

    try:
        if not isinstance(raw_row, dict):
            return None, traza_id, "Fila no es un diccionario"

        ciudad = raw_row.get("municipality")
        if ciudad is None:
            return None, traza_id, "Columna municipality ausente"
        ciudad = str(ciudad)

        pais = raw_row.get("country")
        if pais is None:
            return None, traza_id, "Columna country ausente"
        pais = str(pais)

        lat_raw = raw_row.get("latitude_deg")
        lon_raw = raw_row.get("longitude_deg")
        if lat_raw is None or str(lat_raw).strip() == "" or lon_raw is None or str(lon_raw).strip() == "":
            return None, traza_id, "Coordenadas lat/lon vacías o ausentes"
        latitud = float(lat_raw)
        longitud = float(lon_raw)

        temp_raw = raw_row.get("temp_celsius")
        if temp_raw is None or str(temp_raw).strip() == "":
            return None, traza_id, "temp_celsius vacío o ausente"
        temperatura_c = round(float(temp_raw), 2)

        rh_raw = raw_row.get("humidity_pct")
        if rh_raw is None or str(rh_raw).strip() == "":
            return None, traza_id, "humidity_pct vacío o ausente"
        humedad = round(float(rh_raw), 2)

        wind_raw = raw_row.get("wind_kmh")
        if wind_raw is None or str(wind_raw).strip() == "":
            return None, traza_id, "wind_kmh vacío o ausente"
        viento_kmh = round(float(wind_raw), 2)

        time_raw = raw_row.get("measurement_time")
        fecha_hora = normalizar_fecha_iso(time_raw, formato_origen="%d/%m/%Y %H:%M")

        registro_norm = {
            "ciudad": ciudad,
            "pais": pais,
            "latitud": latitud,
            "longitud": longitud,
            "temperatura_c": temperatura_c,
            "humedad": humedad,
            "viento_kmh": viento_kmh,
            "fecha_hora": fecha_hora,
            "origen": "proveedor_b"
        }
        return registro_norm, traza_id, None

    except Exception as e:
        return None, traza_id, f"Error de conversión/tipos: {str(e)}"


# ---------------------------------------------------------------------------
# 4. Validación Local de Reglas de Negocio
# ---------------------------------------------------------------------------
def validar_registro_institucional(registro: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida un registro normalizado contra las reglas del contrato institucional:
    - ciudad: string no vacío
    - pais: string no vacío
    - latitud: -90 a 90
    - longitud: -180 a 180
    - temperatura_c: numérico
    - humedad: 0 a 100
    - viento_kmh: >= 0
    - fecha_hora: formato ISO 8601 válido
    - origen: valor permitido ("proveedor_a" o "proveedor_b")
    """
    errores = []

    # Validar ciudad
    ciudad = registro.get("ciudad")
    if not isinstance(ciudad, str) or not ciudad.strip():
        errores.append("ciudad no puede estar vacía")

    # Validar país
    pais = registro.get("pais")
    if not isinstance(pais, str) or not pais.strip():
        errores.append("pais no puede estar vacío")

    # Validar latitud (-90 a 90)
    latitud = registro.get("latitud")
    if not isinstance(latitud, (int, float)):
        errores.append("latitud debe ser numérica")
    elif not (-90.0 <= float(latitud) <= 90.0):
        errores.append(f"latitud fuera de rango [-90, 90]: {latitud}")

    # Validar longitud (-180 a 180)
    longitud = registro.get("longitud")
    if not isinstance(longitud, (int, float)):
        errores.append("longitud debe ser numérica")
    elif not (-180.0 <= float(longitud) <= 180.0):
        errores.append(f"longitud fuera de rango [-180, 180]: {longitud}")

    # Validar temperatura_c (numérico)
    temp_c = registro.get("temperatura_c")
    if not isinstance(temp_c, (int, float)):
        errores.append("temperatura_c debe ser numérica")

    # Validar humedad (0 a 100)
    humedad = registro.get("humedad")
    if not isinstance(humedad, (int, float)):
        errores.append("humedad debe ser numérica")
    elif not (0.0 <= float(humedad) <= 100.0):
        errores.append(f"humedad fuera de rango [0, 100]: {humedad}")

    # Validar viento_kmh (>= 0)
    viento = registro.get("viento_kmh")
    if not isinstance(viento, (int, float)):
        errores.append("viento_kmh debe ser numérico")
    elif float(viento) < 0.0:
        errores.append(f"viento_kmh no puede ser negativo: {viento}")

    # Validar fecha_hora (ISO 8601)
    fecha_hora = registro.get("fecha_hora")
    if not isinstance(fecha_hora, str) or not fecha_hora.strip():
        errores.append("fecha_hora no puede estar vacía")
    else:
        try:
            parse_iso_datetime(fecha_hora)
        except Exception:
            errores.append(f"fecha_hora no es una fecha ISO 8601 válida: {fecha_hora}")

    # Validar origen
    origen = registro.get("origen")
    if origen not in ("proveedor_a", "proveedor_b"):
        errores.append(f"origen no permitido por el contrato: {origen}")

    es_valido = len(errores) == 0
    return es_valido, errores


# ---------------------------------------------------------------------------
# 7 & 8. Cliente HTTP con Reintentos y Consulta
RETRY_BACKOFF = float(os.environ.get("RETRY_BACKOFF", "0.05"))

# ---------------------------------------------------------------------------
# 7 & 8. Cliente HTTP con Reintentos y Consulta
# ---------------------------------------------------------------------------
class ClienteAPI:
    """Cliente HTTP para interactuar con la API institucional."""

    def __init__(
        self,
        url_base: str,
        equipo: str,
        timeout: float = TIMEOUT_HTTP,
        max_retries: int = MAX_RETRIES,
        backoff: float = RETRY_BACKOFF
    ):
        self.url_base = url_base.rstrip("/")
        self.equipo = equipo
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = requests.Session()
        self._logged_connection_error = False

    def registrar_medicion(self, payload: Dict[str, Any]) -> Tuple[str, int, Optional[Dict[str, Any]], str]:
        """
        Envía una medición normalizada mediante POST /api/v1/mediciones.
        Retorna: (estado, status_code, respuesta_json_o_dict, mensaje)
        Estados posibles:
        - "ACEPTADO_API" (201)
        - "RECHAZADO_API" (4xx)
        - "ERROR_COMUNICACION" (5xx o fallos de red persistentes)
        """
        endpoint = f"{self.url_base}/api/v1/mediciones"
        headers = {
            "Content-Type": "application/json",
            "X-Equipo": self.equipo
        }

        ultimo_status = 0
        ultimo_mensaje = ""
        ultima_respuesta = None

        for intento in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                ultimo_status = response.status_code

                # Parsear respuesta JSON si existe
                try:
                    ultima_respuesta = response.json()
                except Exception:
                    ultima_respuesta = {"raw_text": response.text}

                # 201: Aceptado
                if ultimo_status == 201:
                    return "ACEPTADO_API", 201, ultima_respuesta, "Registro aceptado exitosamente"

                # 4xx: Error de cliente / validación servidor -> No reintentar
                if 400 <= ultimo_status < 500:
                    msg = f"Rechazado por API ({ultimo_status}): {ultima_respuesta}"
                    return "RECHAZADO_API", ultimo_status, ultima_respuesta, msg

                # 5xx: Error del servidor -> Reintentar
                if 500 <= ultimo_status < 600:
                    ultimo_mensaje = f"Error de servidor HTTP {ultimo_status} (intento {intento}/{self.max_retries})"
                    logger.warning(f"{ultimo_mensaje}. Reintentando...")
                    if intento < self.max_retries and self.backoff > 0:
                        time.sleep(self.backoff * intento)
                    continue

                # Código inesperado
                ultimo_mensaje = f"Código HTTP inesperado: {ultimo_status}"
                return "ERROR_COMUNICACION", ultimo_status, ultima_respuesta, ultimo_mensaje

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as net_err:
                ultimo_mensaje = f"Fallo de comunicación ({type(net_err).__name__}) en intento {intento}/{self.max_retries}"
                if not self._logged_connection_error:
                    logger.warning(f"{ultimo_mensaje} hacia {endpoint}: {net_err}")
                    self._logged_connection_error = True
                if intento < self.max_retries and self.backoff > 0:
                    time.sleep(self.backoff * intento)
                continue
            except Exception as e:
                ultimo_mensaje = f"Excepción en envío HTTP: {str(e)}"
                logger.error(ultimo_mensaje)
                break

        return "ERROR_COMUNICACION", ultimo_status, ultima_respuesta, f"Agotados {self.max_retries} intentos. {ultimo_mensaje}"

    def consultar_mediciones(self) -> Dict[str, Any]:
        """
        Consulta las mediciones registradas para el equipo mediante GET /api/v1/mediciones?equipo=<EQUIPO>.
        """
        endpoint = f"{self.url_base}/api/v1/mediciones"
        params = {"equipo": self.equipo}
        try:
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            if response.status_code == 200:
                try:
                    return {
                        "status_code": 200,
                        "exitoso": True,
                        "datos": response.json()
                    }
                except Exception:
                    return {
                        "status_code": 200,
                        "exitoso": True,
                        "datos": response.text
                    }
            else:
                return {
                    "status_code": response.status_code,
                    "exitoso": False,
                    "error": f"Respuesta HTTP no exitosa ({response.status_code}): {response.text}"
                }
        except Exception as e:
            return {
                "status_code": 0,
                "exitoso": False,
                "error": f"Error de comunicación al consultar: {str(e)}"
            }


# ---------------------------------------------------------------------------
# 2, 6, 10. Pipeline Principal de Integración
# ---------------------------------------------------------------------------
class PipelineIntegracion:
    """Orquesta lectura, normalización, validación local, envío HTTP y reportes."""

    def __init__(self, url_base: str = URL_BASE, equipo: str = EQUIPO):
        self.url_base = url_base
        self.equipo = equipo
        self.cliente_api = ClienteAPI(url_base=self.url_base, equipo=self.equipo)

        # Contadores y almacenamiento
        self.total_procesados = 0
        self.registros_normalizados: List[Dict[str, Any]] = []
        self.trazabilidad: List[Dict[str, Any]] = []

        self.conteo = {
            "procesados": 0,
            "normalizados": 0,
            "errores_normalizacion": 0,
            "validos_localmente": 0,
            "rechazados_localmente": 0,
            "enviados": 0,
            "aceptados_api": 0,
            "rechazados_api": 0,
            "errores_comunicacion": 0
        }

    def leer_proveedor_a(self, ruta_archivo: str = ARCHIVO_PROV_A) -> List[Dict[str, Any]]:
        """Lee el dataset JSON del Proveedor A con manejo controlado de excepciones."""
        if not os.path.exists(ruta_archivo):
            logger.error(f"Archivo no encontrado: {ruta_archivo}")
            return []
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", [])
                if not isinstance(records, list):
                    logger.error(f"El campo 'records' en {ruta_archivo} no es una lista")
                    return []
                return records
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON en {ruta_archivo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al leer {ruta_archivo}: {e}")
            return []

    def leer_proveedor_b(self, ruta_archivo: str = ARCHIVO_PROV_B) -> List[Dict[str, Any]]:
        """Lee el dataset CSV del Proveedor B con manejo controlado de excepciones."""
        if not os.path.exists(ruta_archivo):
            logger.error(f"Archivo no encontrado: {ruta_archivo}")
            return []
        try:
            filas = []
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                # Detectar delimitador o usar ';' por defecto
                reader = csv.DictReader(f, delimiter=";")
                for fila in reader:
                    filas.append(fila)
            return filas
        except Exception as e:
            logger.error(f"Error al leer CSV {ruta_archivo}: {e}")
            return []

    def ejecutar(self, enviar_http: bool = True) -> Dict[str, Any]:
        """Ejecuta el flujo completo de integración."""
        logger.info(f"Iniciando integración para el equipo '{self.equipo}' hacia '{self.url_base}'")

        # 1. Leer datasets
        registros_a = self.leer_proveedor_a()
        registros_b = self.leer_proveedor_b()
        self.conteo["procesados"] = len(registros_a) + len(registros_b)
        logger.info(f"Registros leídos: Proveedor A ({len(registros_a)}), Proveedor B ({len(registros_b)}) -> Total: {self.conteo['procesados']}")

        # 2. Procesar Proveedor A
        for idx, raw_a in enumerate(registros_a, start=1):
            norm, traza_id, err_norm = normalizar_proveedor_a(raw_a, idx)
            self._procesar_registro(norm, traza_id, "proveedor_a", err_norm, enviar_http)

        # 3. Procesar Proveedor B
        for idx, raw_b in enumerate(registros_b, start=1):
            norm, traza_id, err_norm = normalizar_proveedor_b(raw_b, idx)
            self._procesar_registro(norm, traza_id, "proveedor_b", err_norm, enviar_http)

        # 4. Consulta final de mediciones registradas mediante GET
        consulta_resultado = {}
        if enviar_http:
            logger.info("Realizando consulta final de mediciones (GET /api/v1/mediciones)...")
            consulta_resultado = self.cliente_api.consultar_mediciones()
            if consulta_resultado.get("exitoso"):
                logger.info(f"Consulta final exitosa: {consulta_resultado.get('datos')}")
            else:
                logger.warning(f"Consulta final no disponible: {consulta_resultado.get('error')}")

        # 5. Guardar archivos de salida
        self._guardar_salidas(consulta_resultado)

        logger.info("Integración finalizada con éxito.")
        self._imprimir_resumen()

        return {
            "resumen": self.conteo,
            "consulta_final": consulta_resultado,
            "total_trazabilidad": len(self.trazabilidad)
        }

    def _procesar_registro(
        self,
        norm: Optional[Dict[str, Any]],
        traza_id: str,
        origen: str,
        err_norm: Optional[str],
        enviar_http: bool
    ):
        """Procesa un registro individual a través del ciclo de vida."""
        if err_norm is not None or norm is None:
            # Error de normalización: No se incluye en normalizadas.json ni se envía a API
            self.conteo["errores_normalizacion"] += 1
            self.trazabilidad.append({
                "id_trazabilidad": traza_id,
                "origen": origen,
                "estado": "ERROR_NORMALIZACION",
                "motivo": err_norm,
                "datos_normalizados": None,
                "respuesta_servidor": None
            })
            return

        # Registro normalizado con éxito
        self.conteo["normalizados"] += 1
        self.registros_normalizados.append(norm)

        # Validación local
        es_valido, errores_locales = validar_registro_institucional(norm)
        if not es_valido:
            # Rechazado localmente: SÍ permanece en normalizadas.json, NO se envía a API
            self.conteo["rechazados_localmente"] += 1
            self.trazabilidad.append({
                "id_trazabilidad": traza_id,
                "origen": origen,
                "estado": "RECHAZADO_LOCAL",
                "motivo": "; ".join(errores_locales),
                "datos_normalizados": norm,
                "respuesta_servidor": None
            })
            return

        # Válido localmente
        self.conteo["validos_localmente"] += 1

        if not enviar_http:
            self.trazabilidad.append({
                "id_trazabilidad": traza_id,
                "origen": origen,
                "estado": "VALIDO_LOCAL_NO_ENVIADO",
                "motivo": "Envío HTTP omitido por configuración",
                "datos_normalizados": norm,
                "respuesta_servidor": None
            })
            return

        # Envío HTTP
        self.conteo["enviados"] += 1
        estado_envio, status_code, resp_servidor, msg_envio = self.cliente_api.registrar_medicion(norm)

        if estado_envio == "ACEPTADO_API":
            self.conteo["aceptados_api"] += 1
        elif estado_envio == "RECHAZADO_API":
            self.conteo["rechazados_api"] += 1
        else:
            self.conteo["errores_comunicacion"] += 1

        self.trazabilidad.append({
            "id_trazabilidad": traza_id,
            "origen": origen,
            "estado": estado_envio,
            "status_code": status_code,
            "motivo": msg_envio,
            "datos_normalizados": norm,
            "respuesta_servidor": resp_servidor
        })

    def _guardar_salidas(self, consulta_resultado: Dict[str, Any]):
        """Crea el directorio de salida y guarda normalizadas.json y reporte.json."""
        os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

        # 1. Guardar normalizadas.json
        with open(ARCHIVO_NORMALIZADAS, "w", encoding="utf-8") as f:
            json.dump(self.registros_normalizados, f, indent=2, ensure_ascii=False)
        logger.info(f"Guardado {ARCHIVO_NORMALIZADAS} con {len(self.registros_normalizados)} registros")

        # 2. Guardar reporte.json
        reporte_completo = {
            "metadata": {
                "equipo": self.equipo,
                "url_base": self.url_base,
                "timestamp_ejecucion": datetime.now().isoformat()
            },
            "resumen": self.conteo,
            "consulta_final": consulta_resultado,
            "detalle_trazabilidad": self.trazabilidad
        }
        with open(ARCHIVO_REPORTE, "w", encoding="utf-8") as f:
            json.dump(reporte_completo, f, indent=2, ensure_ascii=False)
        logger.info(f"Guardado {ARCHIVO_REPORTE} con resumen y trazabilidad completa")

    def _imprimir_resumen(self):
        """Muestra una tabla de resumen en consola."""
        print("\n" + "=" * 50)
        print(" RESUMEN DE INTEGRACIÓN — TALLER 1")
        print("=" * 50)
        for clave, valor in self.conteo.items():
            nombre_legible = clave.replace("_", " ").capitalize()
            print(f"  {nombre_legible:<30}: {valor:>6}")
        print("=" * 50 + "\n")


# ---------------------------------------------------------------------------
# Punto de Entrada
# ---------------------------------------------------------------------------
def main():
    try:
        pipeline = PipelineIntegracion(url_base=URL_BASE, equipo=EQUIPO)
        pipeline.ejecutar(enviar_http=True)
    except KeyboardInterrupt:
        logger.warning("Ejecución interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error inesperado en la ejecución principal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
