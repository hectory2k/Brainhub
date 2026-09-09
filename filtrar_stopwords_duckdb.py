import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Filtra stopwords en DuckDB usando el StopwordsManager del ecosistema.
"""

import sys
import subprocess
from pathlib import Path

# Agregar el directorio del proyecto al path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# Importar tu gestor de stopwords
from modulos.stopwords_manager import StopwordsManager

# Configuración
DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')

def filtrar_stopwords_en_duckdb(nicho='GENERAL', lang='es'):
    """Filtra stopwords en DuckDB usando el gestor."""
    
    # Inicializar el gestor
    manager = StopwordsManager()
    
    # Obtener stopwords para el nicho e idioma
    stopwords = manager.get_stopwords(nicho=nicho, lang=lang)
    
    if not stopwords:
        print(f"⚠️ No hay stopwords para nicho={nicho}, lang={lang}")
        return False
    
    # Convertir a lista si es set
    if isinstance(stopwords, set):
        stopwords_list = list(stopwords)
    else:
        stopwords_list = stopwords
    
    print(f"📋 Stopwords cargadas: {len(stopwords_list)} para {nicho}/{lang}")
    print(f"   Ejemplos: {stopwords_list[:10]}")
    
    # Crear lista SQL
    stopwords_sql = "', '".join(stopwords_list)
    
    # SQL para crear vistas filtradas
    sql = f"""
    CREATE OR REPLACE VIEW terminos_filtrados AS
    SELECT video, term, frequency
    FROM terminos_raw
    WHERE LOWER(term) NOT IN ('{stopwords_sql}');
    
    CREATE OR REPLACE VIEW top_terminos_filtrados AS
    SELECT term, SUM(frequency) as freq_total, COUNT(DISTINCT video) as videos
    FROM terminos_filtrados
    GROUP BY term
    ORDER BY freq_total DESC;
    
    CREATE OR REPLACE VIEW resumen_filtrado AS
    SELECT video,
           COUNT(*) as terminos_utiles,
           SUM(frequency) as frecuencia_util,
           AVG(frequency) as frecuencia_promedio
    FROM terminos_filtrados
    GROUP BY video;
    """
    
    try:
        result = subprocess.run(
            ['duckdb', DB_PATH],
            input=sql,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Vistas filtradas creadas en DuckDB")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def comparar_antes_despues(limit=20):
    """Compara términos antes y después del filtrado."""
    
    print(f"\n{'='*60}")
    print(f"📊 COMPARACIÓN: ANTES vs DESPUÉS")
    print(f"{'='*60}")
    
    # Antes (sin filtrar)
    print(f"\n🔴 ANTES (con stopwords):")
    sql_before = f"""
    SELECT term, SUM(frequency) as freq
    FROM terminos_raw
    GROUP BY term
    ORDER BY freq DESC
    LIMIT {limit};
    """
    result = subprocess.run(
        ['duckdb', DB_PATH, '-csv', '-c', sql_before],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines[1:limit+1], 1):
            parts = line.split(',')
            if len(parts) >= 2:
                print(f"   {i:2}. {parts[0]}: {parts[1]}")
    
    # Después (filtrado)
    print(f"\n🟢 DESPUÉS (sin stopwords):")
    sql_after = f"""
    SELECT term, freq_total
    FROM top_terminos_filtrados
    LIMIT {limit};
    """
    result = subprocess.run(
        ['duckdb', DB_PATH, '-csv', '-c', sql_after],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines[1:limit+1], 1):
            parts = line.split(',')
            if len(parts) >= 2:
                print(f"   {i:2}. {parts[0]}: {parts[1]}")

def exportar_terminos_filtrados():
    """Exporta los términos filtrados a CSV."""
    output_file = PROJECT_DIR / 'outputs' / 'terminos_filtrados.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    sql = f"""
    COPY (
        SELECT term, freq_total, videos
        FROM top_terminos_filtrados
        ORDER BY freq_total DESC
    ) TO '{output_file}' (FORMAT CSV, HEADER);
    """
    
    try:
        result = subprocess.run(
            ['duckdb', DB_PATH, '-c', sql],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print(f"\n✅ Exportado a: {output_file}")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analisis_por_nicho(nicho='GENERAL'):
    """Muestra análisis específico por nicho."""
    
    print(f"\n📊 ANÁLISIS PARA NICHO: {nicho}")
    print(f"{'='*40}")
    
    # Términos más frecuentes del nicho
    sql = f"""
    SELECT term, SUM(frequency) as freq_total
    FROM terminos_raw
    WHERE term IN (
        SELECT term FROM top_terminos_filtrados LIMIT 100
    )
    GROUP BY term
    ORDER BY freq_total DESC
    LIMIT 15;
    """
    
    result = subprocess.run(
        ['duckdb', DB_PATH, '-csv', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode == 0:
        print("\n🔝 Términos más relevantes:")
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 2:
                print(f"   • {parts[0]}: {parts[1]}")

if __name__ == "__main__":
    print("🔧 Filtrado de stopwords en DuckDB")
    print(f"Base de datos: {DB_PATH}")
    
    # Filtrar con stopwords en español e inglés
    print("\n1. Filtrando stopwords...")
    success = filtrar_stopwords_en_duckdb(nicho='GENERAL', lang='es')
    
    if success:
        # Comparar antes y después
        comparar_antes_despues(20)
        
        # Exportar
        exportar_terminos_filtrados()
        
        # Análisis por nicho
        analisis_por_nicho('TECNOLOGIA')
    else:
        print("\n❌ No se pudo filtrar")
