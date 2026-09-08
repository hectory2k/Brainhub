#!/data/data/com.termux/files/usr/bin/python3
"""
Anatomía BodyParts3D en Parquet + DuckDB.
3,432 conceptos anatómicos consultables localmente.
"""

import subprocess
import csv
import io


class AnatomiaParquet:
    """Gestión de anatomía en formato Parquet/DuckDB."""
    
    DB_PATH = '/sdcard/Download/analisis_consolidado.duckdb'
    
    def crear_tabla(self):
        """Crea tabla anatomia en DuckDB."""
        sql = """
        CREATE TABLE IF NOT EXISTS anatomia (
            concepto_id VARCHAR PRIMARY KEY,
            nombre_es VARCHAR,
            nombre_en VARCHAR,
            mesh_id VARCHAR,
            sistema VARCHAR,
            categoria VARCHAR
        );
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql], 
                      capture_output=True, text=True)
        print("✅ Tabla anatomia creada")
    
    def cargar_csv(self, ruta_csv: str):
        """Carga conceptos desde CSV a DuckDB."""
        sql = f"""
        COPY anatomia FROM '{ruta_csv}' (FORMAT CSV, HEADER);
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql], 
                      capture_output=True, text=True)
        print(f"✅ Datos cargados desde {ruta_csv}")
    
    def buscar(self, termino: str) -> list:
        """Busca concepto anatómico."""
        sql = f"""
        SELECT nombre_es, nombre_en, mesh_id, sistema
        FROM anatomia
        WHERE LOWER(nombre_es) LIKE '%{termino.lower()}%'
           OR LOWER(nombre_en) LIKE '%{termino.lower()}%'
        LIMIT 10;
        """
        resultado = subprocess.run(
            ['duckdb', self.DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=10
        )
        return resultado.stdout
    
    def exportar_parquet(self, ruta_salida: str):
        """Exporta tabla a Parquet."""
        sql = f"""
        COPY (SELECT * FROM anatomia) TO '{ruta_salida}' (FORMAT PARQUET);
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql], 
                      capture_output=True, text=True)
        print(f"✅ Parquet exportado: {ruta_salida}")


if __name__ == '__main__':
    anatomia = AnatomiaParquet()
    anatomia.crear_tabla()
    print("Listo para cargar conceptos BodyParts3D")
