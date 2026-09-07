#!/data/data/com.termux/files/usr/bin/python3
"""Gestor de diccionario clínico para HealthOntology."""

import json
import os
from typing import Dict, List


class DiccionarioClinico:
    """Gestiona el diccionario de términos clínicos desde JSON."""
    
    DEFAULT_JSON_PATH = os.path.expanduser('~/proyectos/nlp/diccionario_clinico.json')
    
    def __init__(self, json_path: str = None):
        self.json_path = json_path or self.DEFAULT_JSON_PATH
        self._data = None
        self._mapa_sinonimos = {}
        self._load()
    
    def _load(self):
        if not os.path.exists(self.json_path):
            print(f"⚠️ Diccionario no encontrado: {self.json_path}")
            self._data = {}
            return
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            
            self._mapa_sinonimos = {}
            for concepto, info in self._data.items():
                for sinonimo in info.get('sinonimos', []):
                    self._mapa_sinonimos[sinonimo.lower()] = concepto
            
            print(f"✅ Diccionario clínico cargado: {len(self._data)} conceptos")
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            self._data = {}
    
    def reload(self):
        self._load()
    
    def normalizar(self, termino: str) -> str:
        termino_norm = termino.lower().strip()
        if termino_norm in self._mapa_sinonimos:
            return self._mapa_sinonimos[termino_norm]
        return termino_norm
    
    def es_clinico(self, termino: str) -> bool:
        termino_norm = self.normalizar(termino)
        return termino_norm in self._data
    
    def get_categoria(self, concepto: str) -> str:
        if concepto in self._data:
            return self._data[concepto].get('categoria', 'general')
        return 'general'
    
    def get_sinonimos(self, concepto: str) -> List[str]:
        if concepto in self._data:
            return self._data[concepto].get('sinonimos', [])
        return []
    
    def get_alias_mesh(self, termino: str) -> str:
        """Retorna el alias MeSH en inglés para un término."""
        normalizado = self.normalizar(termino)
        if normalizado in self._data:
            return self._data[normalizado].get('alias_mesh', '')
        return ''
    
    def get_todos_conceptos(self) -> List[str]:
        return list(self._data.keys())


if __name__ == '__main__':
    dc = DiccionarioClinico()
    
    print(f"\n📋 Conceptos: {len(dc.get_todos_conceptos())}")
    
    tests = [
        'historia clinica',
        'registro electronico de salud',
        'HC',
        'interoperabilidad',
        'FHIR',
        'datos'
    ]
    
    print("\n🔍 Normalización:")
    for termino in tests:
        normalizado = dc.normalizar(termino)
        es_clinico = dc.es_clinico(termino)
        print(f"   '{termino}' → '{normalizado}' (clínico: {es_clinico})")
