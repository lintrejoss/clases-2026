"""Configuración global de Pytest y ajuste de PYTHONPATH."""

import os
import sys

# Agregar el directorio raíz del proyecto al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
