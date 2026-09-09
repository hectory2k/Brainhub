"""Configuración centralizada para BrainHub."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = os.environ.get('BRAINHUB_DB', str(BASE_DIR / 'data' / 'analisis_consolidado.duckdb'))
STOPWORDS_PATH = BASE_DIR / 'stopwords.json'
DICCIONARIO_CLINICO = BASE_DIR / 'diccionario_clinico.json'
DICCIONARIO_NICHOS = BASE_DIR / 'diccionario_nichos.json'
