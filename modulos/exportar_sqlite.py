import json
import sqlite3
import csv
import os
from pathlib import Path

def exportar_sqlite_desde_json(json_path, db_path=None):
    json_path = Path(json_path)
    
    if db_path is None:
        db_path = json_path.with_suffix('.db')
    else:
        db_path = Path(db_path)
    
    if db_path == json_path:
        db_path = json_path.with_suffix('.db')
    
    if db_path.exists() and db_path.stat().st_size > 0:
        with db_path.open('rb') as f:
            cabecera = f.read(16)
        if cabecera != b'SQLite format 3\x00':
            db_path.unlink()
    
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            term TEXT,
            frequency INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            language TEXT,
            analyzed_at TEXT,
            total_lines INTEGER,
            total_words INTEGER,
            sentiment_polarity REAL,
            sentiment_subjectivity REAL,
            nicho TEXT
        )
    ''')
    
    terminos = data.get('terminos_clave', [])
    for i, (term, freq) in enumerate(terminos, 1):
        cursor.execute('INSERT OR IGNORE INTO keywords (id, analysis_id, term, frequency) VALUES (?, ?, ?, ?)',
                      (i, 1, term, freq))
    
    sentiment = data.get('sentimiento_global', {})
    cursor.execute('''
        INSERT OR IGNORE INTO analysis (id, filename, language, analyzed_at, total_lines, total_words,
                             sentiment_polarity, sentiment_subjectivity, nicho)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        1,
        data.get('documento', 'desconocido'),
        'ES' if 'es' in data.get('documento', '').lower() else 'EN',
        '2026-08-31',
        data.get('total_segmentos', 0),
        len(' '.join([s.get('texto', '') for s in data.get('segmentos', [])])),
        sentiment.get('polaridad', 0),
        sentiment.get('subjetividad', 0),
        data.get('nicho', 'GENERAL')
    ))
    
    conn.commit()
    conn.close()
    return str(db_path)

def consolidar_en_duckdb(csv_path, video_id, db_path_duckdb=os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')):
    """
    Consolidar en DuckDB usando duckdb.sql() (universal)
    """
    try:
        import duckdb
        
        # Usar duckdb.sql() que funciona en todas las versiones
        duckdb.sql(f"""
            CREATE OR REPLACE TABLE terminos_raw AS
            SELECT 
                '{video_id}' as video,
                term,
                frequency
            FROM read_csv_auto('{csv_path}')
        """)
        
        # Verificar que se insertaron los datos
        resultado = duckdb.sql(f"SELECT COUNT(*) FROM terminos_raw WHERE video = '{video_id}'").fetchone()
        print(f"✅ Consolidado: {video_id} en DuckDB ({resultado[0]} términos)")
        return True
        
    except Exception as e:
        print(f"⚠️ No se pudo consolidar en DuckDB: {e}")
        return False
