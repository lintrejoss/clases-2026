# Clase 4 — Datos e interacción entre aplicaciones

## Propósito

En esta práctica vas a leer un dataset CSV de estudiantes, transformarlo a una estructura propia y generar un archivo JSON.

El flujo completo es:

```text
estudiantes.csv → estructuras de Python → transformación → estudiantes_resumen.json
```

Al finalizar, podrás identificar cómo una aplicación recibe datos externos, los interpreta, selecciona la información necesaria y produce una representación que otra aplicación podría consumir.

## Estructura del proyecto

```text
clase-03-datos/
├── datos/
│   └── estudiantes.csv
├── salida/
│   └── estudiantes_resumen.json
├── transformar_estudiantes.py
└── README.md
```

Crea las carpetas `datos/` y `salida/` si aún no existen. Ubica el archivo `estudiantes.csv` dentro de `datos/`.

## Requisitos

- Python 3 instalado.
- Editor de código, preferiblemente Visual Studio Code.
- Git configurado con tu cuenta de GitHub.

Esta práctica utiliza únicamente módulos de la biblioteca estándar de Python:

- `csv`: permite leer archivos CSV.
- `json`: permite serializar y deserializar datos JSON.
- `pathlib`: permite construir rutas de archivos de forma segura.

No es necesario instalar paquetes con `pip`.

## Paso 1 — Verificar Python

Crea el archivo `transformar_estudiantes.py` en la carpeta raíz del proyecto y agrega:

```python
print("Hola, Aplicaciones y Servicios Web")

nombre = "Valentina"
semestre = 5
promedio = 4.2
activo = True

print(f"Estudiante: {nombre}")
print(f"Semestre: {semestre}")
print(f"Promedio: {promedio}")
print(f"¿Activo?: {activo}")

print(type(nombre))
print(type(semestre))
print(type(promedio))
print(type(activo))
```

Ejecuta el archivo desde la terminal:

```bash
python transformar_estudiantes.py
```

En Windows, si el comando anterior no funciona:

```powershell
py transformar_estudiantes.py
```

## Paso 2 — Leer el CSV

Reemplaza el contenido de `transformar_estudiantes.py` por:

```python
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"

with open(RUTA_CSV, encoding="utf-8", newline="") as archivo:
    lector = csv.DictReader(archivo, delimiter=";")
    estudiantes_externos = list(lector)

print(estudiantes_externos[0])
print(type(estudiantes_externos))
print(type(estudiantes_externos[0]))
```

Ejecuta el programa y comprueba que:

- `estudiantes_externos` es una lista.
- Cada fila del archivo CSV se representa como un diccionario.
- Los valores leídos desde el CSV llegan inicialmente como texto.

## Paso 3 — Transformar un estudiante

Agrega al final del archivo:

```python
estudiante = estudiantes_externos[0]

estudiante_transformado = {
    "id": estudiante["codigo"],
    "nombre_completo": f'{estudiante["nombre"]} {estudiante["apellido"]}',
    "programa": estudiante["programa"],
    "semestre": int(estudiante["semestre"]),
    "promedio": float(estudiante["promedio"]),
    "estado": "Activo" if estudiante["activo"] == "true" else "Inactivo"
}

print(estudiante_transformado)
```

Verifica estos cambios:

| Dato de entrada | Dato de salida |
|---|---|
| `codigo` | `id` |
| `nombre` + `apellido` | `nombre_completo` |
| `semestre` como texto | `semestre` como entero |
| `promedio` como texto | `promedio` como decimal |
| `activo` con `true` o `false` | `estado` con `Activo` o `Inactivo` |
| `correo` | No se incluye en la salida |

## Paso 4 — Crear una función de transformación

Reemplaza el bloque de transformación del paso anterior por una función:

```python
def transformar_estudiante(estudiante: dict) -> dict:
    """Transforma una fila externa del CSV al formato del panel académico."""
    return {
        "id": estudiante["codigo"],
        "nombre_completo": f'{estudiante["nombre"]} {estudiante["apellido"]}',
        "programa": estudiante["programa"],
        "semestre": int(estudiante["semestre"]),
        "promedio": float(estudiante["promedio"]),
        "estado": "Activo" if estudiante["activo"] == "true" else "Inactivo"
    }


estudiante_transformado = transformar_estudiante(estudiantes_externos[0])
print(estudiante_transformado)
```

## Paso 5 — Transformar todos los registros

Agrega el siguiente bloque:

```python
estudiantes_transformados = []

for estudiante in estudiantes_externos:
    estudiante_transformado = transformar_estudiante(estudiante)
    estudiantes_transformados.append(estudiante_transformado)

print(estudiantes_transformados)
```

Comprueba que la lista transformada contiene cinco estudiantes.

## Paso 6 — Serializar y guardar el JSON

Agrega el import al inicio del archivo:

```python
import json
```

Luego agrega la función de serialización:

```python
def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)
```

Al final del archivo, define la ruta de salida y llama la función:

```python
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"

serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
print(f"Archivo JSON generado: {RUTA_JSON}")
```

Abre el archivo `salida/estudiantes_resumen.json` y comprueba que:

- Contiene un arreglo JSON válido.
- Los nombres con tildes se visualizan correctamente.
- Los valores de `semestre` y `promedio` no tienen comillas.
- El campo `correo` no aparece.

## Paso 7 — Deserializar el JSON generado

Agrega esta función:

```python
def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)
```

Y úsala al final:

```python
estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")
```

## Flujo final esperado

Tu programa debe completar este recorrido:

```text
1. Leer estudiantes.csv con csv.DictReader.
2. Convertir cada fila del CSV a un diccionario Python.
3. Transformar los registros al formato del panel académico.
4. Serializar la lista transformada en estudiantes_resumen.json.
5. Deserializar el JSON generado.
6. Mostrar el primer estudiante recuperado y el total de registros.
```

## Entregables

Para completar la práctica debes incluir:

- `datos/estudiantes.csv`.
- `transformar_estudiantes.py` funcionando.
- `salida/estudiantes_resumen.json` generado por tu programa.
- Un Pull Request hacia la rama `main`.

## Entrega en GitHub

Cuando el programa funcione, ejecuta:

```bash
git status
git checkout -b clase3-csv-json
git add datos/estudiantes.csv transformar_estudiantes.py salida/estudiantes_resumen.json README.md
git commit -m "feat: transforma estudiantes CSV a JSON"
git push -u origin clase3-csv-json
```

Luego crea un Pull Request hacia `main`.

Usa este título:

```text
Clase 3 - Transformación de CSV a JSON - Nombre Apellido
```

Usa esta descripción:

```markdown
- Leí el dataset estudiantes.csv.
- Transformé sus registros a un formato propio.
- Serialicé el resultado como JSON.
- Deserialicé el JSON generado para comprobar la información.
```

## Reto opcional

Si terminaste todos los pasos:

- Agrega `correo_institucional` con el formato `<id>@universidad.edu.co`.
- Agrega un campo `rendimiento`:
  - `Superior` si promedio es mayor o igual a 4.5.
  - `Alto` si promedio es mayor o igual a 4.0 y menor que 4.5.
  - `Básico` si promedio es mayor o igual a 3.0 y menor que 4.0.
  - `Bajo` si promedio es menor que 3.0.
- Ordena los estudiantes por promedio de mayor a menor antes de guardar el JSON.
