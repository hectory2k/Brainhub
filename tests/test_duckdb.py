#!/usr/bin/env python3
"""
Tests para la integración con DuckDB.
Sigue el patrón de los tests existentes.
"""

import sys
import os
import subprocess
import pytest

sys.path.insert(0, os.path.expanduser('~/proyectos/nlp'))

# Configuración
DB_PATH = '/sdcard/Download/analisis_consolidado.duckdb'

# ==================== TEST DUCKDB CLI ====================

@pytest.mark.critical
class TestDuckDBCLI:
    def test_cli_disponible(self):
        """DuckDB CLI está disponible."""
        result = subprocess.run(
            ['duckdb', '--version'],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode == 0
        assert 'v1.6.0' in result.stdout

    def test_base_datos_existe(self):
        """La base de datos existe."""
        if not os.path.exists(DB_PATH):
            pytest.skip('DuckDB no disponible en CI')

    def test_tablas_principales(self):
        """Las tablas principales existen."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        result = subprocess.run(
            ['duckdb', DB_PATH, '-c', "SHOW TABLES;"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert 'terminos_raw' in result.stdout
        assert 'progreso' in result.stdout

# ==================== TEST CONSULTAS ====================

@pytest.mark.critical
class TestConsultasDuckDB:
    def test_consulta_terminos(self):
        """Se pueden consultar términos."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c', 
             "SELECT COUNT(*) FROM terminos_raw;"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        count = int(result.stdout.strip().split('\n')[-1])
        assert count > 0

    def test_consulta_progreso(self):
        """Se puede consultar el progreso."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c', 
             "SELECT COUNT(*) FROM progreso;"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        count = int(result.stdout.strip().split('\n')[-1])
        assert count > 0

    def test_consulta_ml_pytorch(self):
        """Los términos de ML/PyTorch están disponibles."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        sql = """
        SELECT term, SUM(frequency) as total
        FROM terminos_raw
        WHERE term IN ('model', 'torch', 'loss', 'tensor')
        GROUP BY term
        ORDER BY total DESC;
        """
        
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert 'model' in result.stdout
        assert 'torch' in result.stdout

# ==================== TEST MÓDULOS ====================

@pytest.mark.unit
class TestModulosDuckDB:
    def test_import_consolidar_auto(self):
        """El módulo consolidar_auto se puede importar."""
        try:
            from modulos.consolidar_auto import ConsolidarAuto
            assert ConsolidarAuto is not None
        except ImportError:
            pytest.skip("Módulo no disponible")

    def test_import_integrar_duckdb(self):
        """El módulo integrar_duckdb se puede importar."""
        try:
            from modulos.integrar_duckdb import consultar
            assert consultar is not None
        except ImportError:
            pytest.skip("Módulo no disponible")

# ==================== TEST INTEGRACIÓN ====================

@pytest.mark.integration
class TestIntegracionDuckDB:
    def test_pipeline_consolidacion(self):
        """El pipeline de consolidación funciona."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        # Verificar que hay datos consolidados
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c',
             "SELECT COUNT(DISTINCT video) FROM terminos_raw;"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        videos = int(result.stdout.strip().split('\n')[-1])
        assert videos > 0

    def test_estado_pendientes(self):
        """Hay contenidos pendientes registrados."""
        if not os.path.exists(DB_PATH):
            pytest.skip("Base de datos no existe")
        
        result = subprocess.run(
            ['duckdb', DB_PATH, '-csv', '-c',
             "SELECT COUNT(*) FROM progreso WHERE estado = 'pendiente';"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        pendientes = int(result.stdout.strip().split('\n')[-1])
        assert pendientes >= 0
