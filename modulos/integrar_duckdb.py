#!/data/data/com.termux/files/usr/bin/python3
"""
Módulo de integración DuckDB para el ecosistema NLP.
Proporciona funciones auxiliares para consultas y análisis.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuración
PROJECT_DIR = Path(__file__).parent.parent
DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')

def consultar(sql: str, return_raw: bool = False) -> List:
    """Ejecuta una consulta SQL y retorna resultados."""
    try:
        # Usar modo csv para mejor parsing
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c', sql],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            if return_raw:
                return result.stdout
            return _parse_csv_output(result.stdout)
        else:
            print(f"❌ Error: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def _parse_csv_output(output: str) -> List:
    """Parsea la salida CSV del CLI de DuckDB."""
    import csv
    import io
    
    results = []
    try:
        reader = csv.reader(io.StringIO(output))
        headers = next(reader, [])
        
        for row in reader:
            if row:
                # Convertir números si es posible
                converted_row = []
                for value in row:
                    try:
                        if value.isdigit():
                            converted_row.append(int(value))
                        else:
                            converted_row.append(value)
                    except:
                        converted_row.append(value)
                results.append(converted_row)
    except Exception as e:
        print(f"⚠️ Error parseando CSV: {e}")
    
    return results

def _parse_output(output: str) -> List:
    """Parsea la salida del CLI de DuckDB (modo tabla)."""
    lines = output.strip().split('\n')
    results = []
    headers = []
    
    for line in lines:
        if '│' in line and '┌' not in line and '└' not in line and '├' not in line:
            parts = [p.strip() for p in line.split('│')]
            data = [p for p in parts if p and p != '│']
            if data:
                if not headers:
                    headers = data
                else:
                    results.append(data)
    
    return results

def obtener_estadisticas() -> Dict[str, Any]:
    """Obtiene estadísticas generales de la base de datos."""
    stats = {}
    
    # Total de términos
    result = consultar("SELECT COUNT(*) as total FROM terminos_raw;")
    if result and result[0]:
        stats['total_terminos'] = result[0][0] if isinstance(result[0][0], int) else int(result[0][0])
    
    # Total de videos
    result = consultar("SELECT COUNT(DISTINCT video) as total FROM terminos_raw;")
    if result and result[0]:
        stats['total_videos'] = result[0][0] if isinstance(result[0][0], int) else int(result[0][0])
    
    # Videos completados
    result = consultar("SELECT COUNT(*) as total FROM progreso WHERE estado = 'completado';")
    if result and result[0]:
        stats['videos_completados'] = result[0][0] if isinstance(result[0][0], int) else int(result[0][0])
    
    # Videos pendientes
    result = consultar("SELECT COUNT(*) as total FROM progreso WHERE estado = 'pendiente';")
    if result and result[0]:
        stats['videos_pendientes'] = result[0][0] if isinstance(result[0][0], int) else int(result[0][0])
    
    return stats

def top_terminos(limit: int = 20) -> List:
    """Obtiene los términos más frecuentes."""
    sql = f"""
    SELECT term, SUM(frequency) as freq_total
    FROM terminos_raw
    GROUP BY term
    ORDER BY freq_total DESC
    LIMIT {limit};
    """
    return consultar(sql)

def terminos_por_video(video_id: str) -> List:
    """Obtiene términos de un video específico."""
    sql = f"""
    SELECT term, frequency
    FROM terminos_raw
    WHERE video = '{video_id}'
    ORDER BY frequency DESC;
    """
    return consultar(sql)

def buscar_termino(termino: str) -> List:
    """Busca un término en todos los videos."""
    sql = f"""
    SELECT video, term, frequency
    FROM terminos_raw
    WHERE term LIKE '%{termino}%'
    ORDER BY frequency DESC;
    """
    return consultar(sql)

def actualizar_estado(video_id: str, estado: str = 'completado'):
    """Actualiza el estado de un video en progreso."""
    if estado == 'completado':
        sql = f"""
        UPDATE progreso 
        SET estado = 'completado', 
            fecha_completado = CURRENT_DATE
        WHERE video = '{video_id}';
        """
    else:
        sql = f"""
        UPDATE progreso 
        SET estado = '{estado}'
        WHERE video = '{video_id}';
        """
    
    try:
        result = subprocess.run(
            ['duckdb', DB_PATH, '-c', sql],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Estado actualizado: {video_id} → {estado}")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def exportar_csv(tabla: str, output_file: str = None) -> bool:
    """Exporta una tabla a CSV."""
    if output_file is None:
        output_file = str(PROJECT_DIR / 'outputs' / f'{tabla}.csv')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    sql = f"COPY {tabla} TO '{output_file}' (FORMAT CSV, HEADER);"
    
    try:
        result = subprocess.run(
            ['duckdb', DB_PATH, '-c', sql],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {tabla} exportada a {output_file}")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def crear_vistas():
    """Crea vistas útiles para análisis."""
    vistas_sql = """
    -- Vista de top términos por video
    CREATE OR REPLACE VIEW top_terminos_por_video AS
    SELECT video, term, frequency,
           RANK() OVER (PARTITION BY video ORDER BY frequency DESC) as rank
    FROM terminos_raw;
    
    -- Vista de resumen por video
    CREATE OR REPLACE VIEW resumen_por_video AS
    SELECT video,
           COUNT(*) as total_terminos,
           SUM(frequency) as frecuencia_total,
           AVG(frequency) as frecuencia_promedio
    FROM terminos_raw
    GROUP BY video;
    """
    
    try:
        result = subprocess.run(
            ['duckdb', DB_PATH],
            input=vistas_sql,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Vistas creadas")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Módulo de integración DuckDB")
    print(f"Base de datos: {DB_PATH}")
    print()
    
    # Mostrar estadísticas
    stats = obtener_estadisticas()
    print("📊 Estadísticas:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Mostrar top 10 términos
    print("\n🏆 Top 10 términos:")
    top = top_terminos(10)
    for row in top:
        print(f"   {row[0]}: {row[1]}")
    
    # Crear vistas
    print("\n🔄 Creando vistas...")
    crear_vistas()
