"""Configuracion global de pytest para BrainHub.

Asegura que modulos/ y brainhub/ esten en el path
en CUALQUIER entorno (Termux, CI, Windows, macOS, Linux).
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
