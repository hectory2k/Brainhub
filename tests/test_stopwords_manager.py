#!/data/data/com.termux/files/usr/bin/python3
"""Tests para stopwords_manager."""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modulos.stopwords_manager import StopwordsManager


@pytest.mark.unit
class TestStopwordsManager:
    
    def test_carga_json(self):
        """Carga stopwords desde JSON."""
        manager = StopwordsManager()
        assert manager._data is not None
        assert 'base' in manager._data
    
    def test_get_stopwords_es(self):
        """Obtiene stopwords en español."""
        manager = StopwordsManager()
        sw = manager.get_stopwords('GENERAL', 'es')
        assert len(sw) > 0
        assert 'que' in sw
    
    def test_get_stopwords_en(self):
        """Obtiene stopwords en inglés."""
        manager = StopwordsManager()
        sw = manager.get_stopwords('GENERAL', 'en')
        assert len(sw) > 0
        assert 'the' in sw
    
    def test_nicho_especifico(self):
        """Obtiene stopwords por nicho."""
        manager = StopwordsManager()
        sw_salud = manager.get_stopwords('SALUD', 'es')
        sw_general = manager.get_stopwords('GENERAL', 'es')
        assert len(sw_salud) >= len(sw_general)
