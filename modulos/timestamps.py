import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Módulo de timestamps VTT - Grounding temporal y navegación.
Incluye todas las funciones para búsqueda y análisis temporal.
"""

import re
import subprocess
import csv
import io
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class SegmentoTemporal:
    """Segmento con timestamp."""
    texto: str
    inicio_segundos: float
    fin_segundos: float
    
    @property
    def inicio_formato(self) -> str:
        return self._formatear(self.inicio_segundos)
    
    @property
    def fin_formato(self) -> str:
        return self._formatear(self.fin_segundos)
    
    @property
    def duracion(self) -> float:
        return self.fin_segundos - self.inicio_segundos
    
    def _formatear(self, segundos: float) -> str:
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    
    def a_dict(self) -> Dict:
        return {
            'texto': self.texto,
            'inicio': self.inicio_formato,
            'fin': self.fin_formato,
            'inicio_segundos': self.inicio_segundos,
            'fin_segundos': self.fin_segundos,
            'duracion': self.duracion,
            'grounding': f"{self.inicio_formato}-{self.fin_formato}"
        }


class ParserVTT:
    """Parsea archivos VTT."""
    
    PATRON_TIEMPO = re.compile(
        r'(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})'
    )
    
    def _a_segundos(self, h: str, m: str, s: str, ms: str) -> float:
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    def parsear_archivo(self, ruta_vtt: str) -> List[SegmentoTemporal]:
        with open(ruta_vtt, 'r', encoding='utf-8') as f:
            return self.parsear_texto(f.read())
    
    def parsear_texto(self, contenido: str) -> List[SegmentoTemporal]:
        segmentos = []
        lineas = contenido.split('\n')
        i = 0
        
        while i < len(lineas):
            linea = lineas[i].strip()
            match = self.PATRON_TIEMPO.search(linea)
            
            if match:
                inicio = self._a_segundos(
                    match.group(1), match.group(2), match.group(3), match.group(4)
                )
                fin = self._a_segundos(
                    match.group(5), match.group(6), match.group(7), match.group(8)
                )
                
                textos = []
                i += 1
                while i < len(lineas) and lineas[i].strip():
                    textos.append(lineas[i].strip())
                    i += 1
                
                texto = ' '.join(textos).strip()
                if texto:
                    segmentos.append(SegmentoTemporal(
                        texto=texto,
                        inicio_segundos=inicio,
                        fin_segundos=fin
                    ))
            i += 1
        
        return segmentos


class TimestampsDB:
    """Gestión de timestamps en DuckDB."""
    
    def __init__(self, db_path=os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')):
        self.db_path = db_path
        self._crear_schema()
    
    def _crear_schema(self):
        """Crea tabla si no existe."""
        schema = """
        CREATE TABLE IF NOT EXISTS segmentos_timestamp (
            video_id VARCHAR,
            inicio_segundos DOUBLE,
            fin_segundos DOUBLE,
            inicio_formato VARCHAR,
            fin_formato VARCHAR,
            texto TEXT,
            PRIMARY KEY (video_id, inicio_segundos)
        );
        """
        self._ejecutar(schema)
    
    def _ejecutar(self, sql: str, timeout: int = 30) -> tuple:
        """Ejecuta SQL y retorna (success, output, error)."""
        try:
            resultado = subprocess.run(
                ['duckdb', self.db_path],
                input=sql,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return resultado.returncode == 0, resultado.stdout, resultado.stderr
        except Exception as e:
            return False, "", str(e)
    
    def guardar_segmentos(self, video_id: str, segmentos: List[SegmentoTemporal]) -> bool:
        """Guarda segmentos en DuckDB (idempotente)."""
        delete_sql = f"DELETE FROM segmentos_timestamp WHERE video_id = '{video_id}';"
        
        inserts = []
        for seg in segmentos:
            texto_escapado = seg.texto.replace("'", "''")
            inserts.append(f"""
            INSERT INTO segmentos_timestamp VALUES (
                '{video_id}', {seg.inicio_segundos}, {seg.fin_segundos},
                '{seg.inicio_formato}', '{seg.fin_formato}', '{texto_escapado}'
            );
            """)
        
        success, output, error = self._ejecutar(delete_sql + '\n'.join(inserts))
        return success
    
    def buscar_en_video(self, video_id: str, termino: str) -> List[Dict]:
        """Busca texto en segmentos de UN video."""
        sql = f"""
        SELECT inicio_formato, fin_formato, texto
        FROM segmentos_timestamp
        WHERE video_id = '{video_id}' 
          AND LOWER(texto) LIKE '%{termino.lower()}%'
        ORDER BY inicio_segundos;
        """
        return self._consultar(sql)
    
    def buscar_en_todos(self, termino: str) -> List[Dict]:
        """Busca texto en TODOS los videos."""
        sql = f"""
        SELECT video_id, inicio_formato, fin_formato, texto
        FROM segmentos_timestamp
        WHERE LOWER(texto) LIKE '%{termino.lower()}%'
        ORDER BY video_id, inicio_segundos;
        """
        return self._consultar(sql)
    
    def obtener_segmento_en_tiempo(self, video_id: str, tiempo: float) -> Optional[Dict]:
        """Obtiene segmento que contiene un tiempo específico."""
        sql = f"""
        SELECT inicio_formato, fin_formato, texto
        FROM segmentos_timestamp
        WHERE video_id = '{video_id}' 
          AND inicio_segundos <= {tiempo} 
          AND fin_segundos >= {tiempo}
        LIMIT 1;
        """
        resultados = self._consultar(sql)
        return resultados[0] if resultados else None
    
    def obtener_todos(self, video_id: str) -> List[Dict]:
        """Lista todos los segmentos de un video."""
        sql = f"""
        SELECT inicio_formato, fin_formato, texto
        FROM segmentos_timestamp
        WHERE video_id = '{video_id}'
        ORDER BY inicio_segundos;
        """
        return self._consultar(sql)
    
    def contar_por_video(self) -> List[Dict]:
        """Métricas: segmentos por video."""
        sql = """
        SELECT video_id, COUNT(*) as total_segmentos
        FROM segmentos_timestamp
        GROUP BY video_id
        ORDER BY total_segmentos DESC;
        """
        return self._consultar(sql)
    
    def integrar_con_analisis(self):
        """Crea vista SQL uniendo con análisis NLP."""
        sql = """
        CREATE OR REPLACE VIEW analisis_con_segmentos AS
        SELECT 
            s.video_id,
            s.inicio_formato,
            s.fin_formato,
            s.texto as segmento_texto,
            t.term as termino_clave,
            t.frequency as frecuencia
        FROM segmentos_timestamp s
        LEFT JOIN terminos_raw t ON s.video_id = t.video
        WHERE s.video_id IS NOT NULL;
        """
        success, _, error = self._ejecutar(sql)
        return success
    
    def _consultar(self, sql: str) -> List[Dict]:
        """Consulta SQL y parsea CSV."""
        success, output, error = self._ejecutar(sql, timeout=15)
        if not success:
            return []
        
        reader = csv.reader(io.StringIO(output))
        headers = next(reader, [])
        
        resultados = []
        for fila in reader:
            if fila:
                resultados.append(dict(zip(headers, fila)))
        
        return resultados


# Test
if __name__ == '__main__':
    vtt_ejemplo = """WEBVTT

00:00:00.000 --> 00:00:05.000
En este video vamos a aprender

00:00:05.000 --> 00:00:12.000
cómo usar PyTorch para deep learning

00:00:12.000 --> 00:00:20.000
El modelo mejora la precisión
"""
    
    parser = ParserVTT()
    segmentos = parser.parsear_texto(vtt_ejemplo)
    
    print(f"✅ Segmentos: {len(segmentos)}")
    for seg in segmentos:
        print(f"   [{seg.inicio_formato} → {seg.fin_formato}] {seg.texto[:50]}")
    
    # Búsqueda local
    resultados = [s for s in segmentos if 'PyTorch' in s.texto]
    print(f"\n🔍 'PyTorch' en {len(resultados)} segmentos")
    for seg in resultados:
        print(f"   [{seg.inicio_formato}] {seg.texto}")
    
    # Segmento en tiempo
    seg = next((s for s in segmentos if s.inicio_segundos <= 7.5 <= s.fin_segundos), None)
    if seg:
        print(f"\n⏱️ Tiempo 7.5s → [{seg.inicio_formato}] {seg.texto}")
