#!/data/data/com.termux/files/usr/bin/python3
"""
Tests para el módulo de timestamps.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.expanduser('~/proyectos/nlp'))

from modulos.timestamps import ParserVTT, SegmentoTemporal, TimestampsDB


VTT_EJEMPLO = """WEBVTT

00:00:00.000 --> 00:00:05.000
En este video vamos a aprender

00:00:05.000 --> 00:00:12.000
cómo usar PyTorch para deep learning

00:00:12.000 --> 00:00:20.000
El modelo mejora la precisión
"""


@pytest.mark.unit
class TestParserVTT:
    
    def test_parsear_texto(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        assert len(segmentos) == 3
        assert segmentos[0].texto == "En este video vamos a aprender"
        assert segmentos[0].inicio_segundos == 0.0
        assert segmentos[0].fin_segundos == 5.0
    
    def test_formato_tiempo(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        assert segmentos[0].inicio_formato == "00:00:00"
        assert segmentos[1].inicio_formato == "00:00:05"
        assert segmentos[2].inicio_formato == "00:00:12"
    
    def test_duracion(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        assert segmentos[0].duracion == 5.0
        assert segmentos[1].duracion == 7.0
        assert segmentos[2].duracion == 8.0
    
    def test_buscar_termino(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        resultados = [s for s in segmentos if 'PyTorch' in s.texto]
        assert len(resultados) == 1
        assert resultados[0].inicio_formato == "00:00:05"
    
    def test_segmento_en_tiempo(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        seg = next((s for s in segmentos if s.inicio_segundos <= 7.5 <= s.fin_segundos), None)
        assert seg is not None
        assert "PyTorch" in seg.texto
    
    def test_a_dict(self):
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        dict_seg = segmentos[0].a_dict()
        assert 'texto' in dict_seg
        assert 'inicio' in dict_seg
        assert 'fin' in dict_seg
        assert 'grounding' in dict_seg


@pytest.mark.integration
class TestTimestampsDB:
    
    def test_guardar_y_buscar(self):
        """Test de integración con DuckDB (si existe)."""
        db_path = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
        if not os.path.exists(db_path):
            pytest.skip("DuckDB no disponible")
        
        parser = ParserVTT()
        segmentos = parser.parsear_texto(VTT_EJEMPLO)
        
        db = TimestampsDB(db_path)
        success = db.guardar_segmentos('test_timestamps', segmentos)
        
        assert success
        
        # Buscar término
        resultados = db.buscar_en_video('test_timestamps', 'PyTorch')
        assert len(resultados) >= 1
        
        # Limpiar datos de prueba
        import subprocess
        subprocess.run(
            ['duckdb', db_path, '-c', 
             "DELETE FROM segmentos_timestamp WHERE video_id = 'test_timestamps';"],
            capture_output=True, text=True, timeout=10
        )
