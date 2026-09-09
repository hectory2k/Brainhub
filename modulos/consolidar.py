#!/usr/bin/env python3
"""
Módulo de consolidación para DuckDB
Uso: from modulos.consolidar import consolidar_archivo, consolidar_carpeta
"""

import os
import sqlite3
import subprocess
from pathlib import Path

def consolidar_archivo(db_path, video_id=None):
    """
    Consolida un archivo SQLite en DuckDB.
    
    Args:
        db_path: Ruta al archivo SQLite
        video_id: ID del video (opcional, se extrae del nombre)
    
    Returns:
        bool: True si se consolidó correctamente
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        print(f"❌ Archivo no encontrado: {db_path}")
        return False
    
    # Extraer video_id del nombre si no se proporciona
    if video_id is None:
        video_id = db_path.stem.replace('_analisis', '').replace('_ES', '').replace('_EN', '')
        video_id = video_id.replace('Transcript_', '')
    
    # Generar CSV temporal
    csv_path = db_path.with_suffix('.csv')
    
    try:
        # Exportar SQLite a CSV
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM keywords;")
        
        import csv
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(cursor.fetchall())
        conn.close()
        
        # Insertar en DuckDB
        import duckdb
        duckdb_path = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
        
        conn_duck = duckdb.connect(duckdb_path)
        
        # Verificar si la tabla existe
        conn_duck.execute("""
            CREATE TABLE IF NOT EXISTS terminos_raw (
                video VARCHAR,
                term VARCHAR,
                frequency INTEGER
            )
        """)
        
        # Insertar datos
        conn_duck.execute(f"""
            INSERT INTO terminos_raw (video, term, frequency)
            SELECT 
                '{video_id}' as video,
                term,
                frequency
            FROM read_csv_auto('{csv_path}')
        """)
        
        # Actualizar progreso
        conn_duck.execute(f"""
            INSERT OR IGNORE INTO progreso (video)
            VALUES ('{video_id}')
        """)
        
        conn_duck.close()
        
        # Limpiar CSV temporal
        if csv_path.exists():
            csv_path.unlink()
        
        print(f"✅ Consolidado: {video_id} en DuckDB")
        return True
        
    except Exception as e:
        print(f"⚠️ Error consolidando {video_id}: {e}")
        if csv_path.exists():
            csv_path.unlink()
        return False

def consolidar_carpeta(carpeta, patron="*_analisis.db"):
    """
    Consolida todos los archivos SQLite en una carpeta.
    
    Args:
        carpeta: Ruta a la carpeta
        patron: Patrón de búsqueda (default: *_analisis.db)
    
    Returns:
        tuple: (exitosos, fallidos)
    """
    carpeta = Path(carpeta)
    
    if not carpeta.exists():
        print(f"❌ Carpeta no encontrada: {carpeta}")
        return (0, 0)
    
    archivos = list(carpeta.glob(patron))
    
    if not archivos:
        print(f"⚠️ No se encontraron archivos con patrón: {patron}")
        return (0, 0)
    
    print(f"📁 Consolidando {len(archivos)} archivos...")
    
    exitosos = 0
    fallidos = 0
    
    for archivo in archivos:
        if consolidar_archivo(archivo):
            exitosos += 1
        else:
            fallidos += 1
    
    print(f"\n✅ Exitosos: {exitosos}")
    print(f"❌ Fallidos: {fallidos}")
    
    return (exitosos, fallidos)

# Función de conveniencia para comandos
def consolidar_ultimo():
    """Consolida el último archivo SQLite generado."""
    import glob
    archivos = glob.glob("/sdcard/Download/Transcript_*_analisis.db")
    if archivos:
        ultimo = max(archivos, key=os.path.getctime)
        print(f"📄 Último archivo: {ultimo}")
        return consolidar_archivo(ultimo)
    else:
        print("❌ No se encontraron archivos SQLite")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ultimo":
            consolidar_ultimo()
        elif sys.argv[1] == "--carpeta" and len(sys.argv) > 2:
            consolidar_carpeta(sys.argv[2])
        else:
            consolidar_archivo(sys.argv[1])
    else:
        print("❌ Uso: python3 consolidar.py archivo.db")
        print("   python3 consolidar.py --ultimo")
        print("   python3 consolidar.py --carpeta /ruta/")
