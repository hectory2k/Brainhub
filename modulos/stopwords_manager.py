#!/usr/bin/env python3
"""
Módulo de gestión de stopwords desde JSON V1
Uso: from modulos.stopwords_manager import StopwordsManager
"""

import os
import json
from pathlib import Path

class StopwordsManager:
    """Gestiona stopwords por nicho desde un archivo JSON."""
    
    # Ruta por defecto al archivo JSON
    DEFAULT_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'stopwords.json')
    
    def __init__(self, json_path=None):
        """
        Inicializa el gestor de stopwords.
        
        Args:
            json_path: Ruta al archivo JSON de stopwords. Si es None, usa la ruta por defecto.
        """
        self.json_path = json_path or self.DEFAULT_JSON_PATH
        self._data = None
        self._cache = {}
        self._load()
    
    def _load(self):
        """Carga el archivo JSON en memoria."""
        if not os.path.exists(self.json_path):
            print(f"⚠️ Archivo stopwords.json no encontrado: {self.json_path}")
            self._data = {'base': {}, 'nichos': {}}
            return
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            print(f"✅ Stopwords cargadas desde: {self.json_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            self._data = {'base': {}, 'nichos': {}}
    
    def reload(self):
        """Recarga el archivo JSON."""
        self._cache = {}
        self._load()
    
    def get_stopwords(self, nicho='GENERAL', lang='es'):
        """
        Retorna las stopwords para un nicho e idioma.
        
        Args:
            nicho: 'SALUD', 'CIBERSEGURIDAD', 'TECNOLOGIA', 'FINANZAS', 'LEGAL', 'GENERAL'
            lang: 'es' o 'en'
        
        Returns:
            set: Conjunto de stopwords
        """
        cache_key = f"{nicho}_{lang}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Obtener stopwords base
        base = self._data.get('base', {}).get(lang, [])
        
        # Obtener stopwords del nicho
        nichos = self._data.get('nichos', {})
        nicho_stopwords = nichos.get(nicho, {}).get(lang, [])
        
        # Combinar y convertir a set
        result = set(base) | set(nicho_stopwords)
        self._cache[cache_key] = result
        
        return result
    
    def get_base_stopwords(self, lang='es'):
        """Retorna solo las stopwords base para un idioma."""
        return set(self._data.get('base', {}).get(lang, []))
    
    def get_nicho_stopwords(self, nicho='GENERAL', lang='es'):
        """Retorna solo las stopwords del nicho para un idioma."""
        nichos = self._data.get('nichos', {})
        return set(nichos.get(nicho, {}).get(lang, []))
    
    def add_stopwords(self, nicho, lang, palabras):
        """
        Agrega stopwords a un nicho en el archivo JSON.
        
        Args:
            nicho: 'SALUD', 'CIBERSEGURIDAD', etc.
            lang: 'es' o 'en'
            palabras: Lista o set de palabras a agregar
        """
        # Asegurar que el nicho existe
        if nicho not in self._data['nichos']:
            self._data['nichos'][nicho] = {'en': [], 'es': []}
        
        # Asegurar que el idioma existe
        if lang not in self._data['nichos'][nicho]:
            self._data['nichos'][nicho][lang] = []
        
        # Agregar palabras (evitando duplicados)
        current = set(self._data['nichos'][nicho][lang])
        current.update(palabras)
        self._data['nichos'][nicho][lang] = list(current)
        
        # Guardar cambios en el archivo
        self._save()
        
        # Limpiar caché
        self._cache.pop(f"{nicho}_{lang}", None)
        print(f"✅ Stopwords agregadas a {nicho}/{lang}: {len(palabras)} palabras")
    
    def remove_stopwords(self, nicho, lang, palabras):
        """
        Elimina stopwords de un nicho.
        
        Args:
            nicho: 'SALUD', 'CIBERSEGURIDAD', etc.
            lang: 'es' o 'en'
            palabras: Lista o set de palabras a eliminar
        """
        if nicho not in self._data['nichos']:
            return
        
        if lang not in self._data['nichos'][nicho]:
            return
        
        current = set(self._data['nichos'][nicho][lang])
        current.difference_update(palabras)
        self._data['nichos'][nicho][lang] = list(current)
        
        self._save()
        self._cache.pop(f"{nicho}_{lang}", None)
        print(f"✅ Stopwords eliminadas de {nicho}/{lang}: {len(palabras)} palabras")
    
    def add_base_stopwords(self, lang, palabras):
        """
        Agrega stopwords a la lista base.
        
        Args:
            lang: 'es' o 'en'
            palabras: Lista o set de palabras a agregar
        """
        current = set(self._data['base'].get(lang, []))
        current.update(palabras)
        self._data['base'][lang] = list(current)
        self._save()
        self._cache.pop(f"GENERAL_{lang}", None)
        self._cache.pop(f"_base_{lang}", None)
        print(f"✅ Stopwords base agregadas a {lang}: {len(palabras)} palabras")
    
    def _save(self):
        """Guarda los datos en el archivo JSON."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            print(f"✅ Stopwords guardadas en: {self.json_path}")
        except Exception as e:
            print(f"❌ Error al guardar stopwords: {e}")
    
    def get_all_nichos(self):
        """Retorna la lista de todos los nichos disponibles."""
        return list(self._data.get('nichos', {}).keys())
    
    def get_stats(self):
        """Retorna estadísticas de las stopwords."""
        stats = {
            'total_nichos': len(self.get_all_nichos()),
            'nichos': {}
        }
        
        for nicho in self.get_all_nichos():
            stats['nichos'][nicho] = {
                'es': len(self.get_nicho_stopwords(nicho, 'es')),
                'en': len(self.get_nicho_stopwords(nicho, 'en'))
            }
        
        stats['base'] = {
            'es': len(self.get_base_stopwords('es')),
            'en': len(self.get_base_stopwords('en'))
        }
        
        return stats
    
    def print_stats(self):
        """Imprime estadísticas de las stopwords."""
        stats = self.get_stats()
        print("📊 ESTADÍSTICAS DE STOPWORDS")
        print("=" * 40)
        print(f"Base ES: {stats['base']['es']} palabras")
        print(f"Base EN: {stats['base']['en']} palabras")
        print(f"Total nichos: {stats['total_nichos']}")
        print("\nNICHOS:")
        for nicho, counts in stats['nichos'].items():
            print(f"  {nicho}: ES={counts['es']}, EN={counts['en']}")

# Instancia global por defecto
_default_manager = None

def get_stopwords_manager(json_path=None):
    """Obtiene la instancia global del gestor de stopwords."""
    global _default_manager
    if _default_manager is None or json_path is not None:
        _default_manager = StopwordsManager(json_path)
    return _default_manager

def get_stopwords(nicho='GENERAL', lang='es'):
    """Función de conveniencia para obtener stopwords."""
    return get_stopwords_manager().get_stopwords(nicho, lang)

if __name__ == "__main__":
    # Test
    print("🔍 Probando StopwordsManager...")
    manager = StopwordsManager()
    
    # Mostrar estadísticas
    manager.print_stats()
    
    # Test de get_stopwords
    salud_es = manager.get_stopwords('SALUD', 'es')
    print(f"\n✅ Stopwords SALUD (ES): {len(salud_es)} palabras")
    print(f"   Ejemplos: {list(salud_es)[:5]}")
    
    # Test de agregar
    manager.add_stopwords('SALUD', 'es', ['prueba1', 'prueba2'])
    salud_es_nuevo = manager.get_stopwords('SALUD', 'es')
    print(f"✅ Stopwords SALUD (ES) después de agregar: {len(salud_es_nuevo)} palabras")
