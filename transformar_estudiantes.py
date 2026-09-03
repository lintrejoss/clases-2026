import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"


def transformar_estudiante(estudiante: dict) -> dict:
    """Transforma una fila externa del CSV al formato del panel académico."""
    return {
        "id": estudiante["codigo"],
        "nombre_completo": f"{estudiante['nombre']} {estudiante['apellido']}",
        "programa": estudiante["programa"],
        "semestre": int(estudiante["semestre"]),
        "promedio": float(estudiante["promedio"]),
        "estado": "Activo" if estudiante["activo"].strip().lower() == "true" else "Inactivo",
    }


def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)


def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def main():
    print("Hola, Aplicaciones y Servicios Web")

    # Paso 2: Leer el CSV
    with open(RUTA_CSV, encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        estudiantes_externos = list(lector)

    # Paso 5: Transformar todos los registros
    estudiantes_transformados = []
    for estudiante in estudiantes_externos:
        estudiante_transformado = transformar_estudiante(estudiante)
        estudiantes_transformados.append(estudiante_transformado)

    # Paso 6: Serializar y guardar el JSON
    serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
    print(f"Archivo JSON generado: {RUTA_JSON}")

    # Paso 7: Deserializar el JSON generado
    estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

    print("\nDatos recuperados desde el JSON:")
    print(estudiantes_recuperados[0])
    print(f"Total recuperado: {len(estudiantes_recuperados)}")


if __name__ == "__main__":
    main()
