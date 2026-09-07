#!/data/data/com.termux/files/usr/bin/python3
"""
Generador de documento final 80/20 para BrainHub.
Une: Abstract + Preguntas + Métricas + Timestamps.
"""

import json
from typing import Dict, List

try:
    from modulos.mesh_cache import MeSHCache
except ImportError:
    MeSHCache = None
from pathlib import Path


class GeneradorDocumento:
    """Genera documento completo de estudio."""
    
    def __init__(self):
        self.abstract = None
        self.preguntas = None
        self.metricas = None
        self.terminos = None
    
    def cargar_datos(
        self,
        jerarquia: Dict,
        terminos_clave: List[str],
        abstract: str,
        preguntas: Dict,
        metricas: Dict = None
    ):
        """Carga todos los datos para el documento."""
        self.jerarquia = jerarquia
        self.terminos = terminos_clave
        self.abstract = abstract
        self.preguntas = preguntas
        self.metricas = metricas or {}
    
    def generar_markdown(self, ruta_salida: str) -> str:
        """Genera documento Markdown completo."""
        nicho = self.jerarquia.get('nicho_principal', 'GENERAL')
        secundarios = self.jerarquia.get('secundarios', {})
        
        doc = f"""# 📚 Documento de Estudio 80/20
## BrainHub - Análisis Jerárquico

---

{self.abstract}

---

## 🔑 Términos Clave

| # | Término | Nicho |
|---|---------|-------|
"""
        
        for i, termino in enumerate(self.terminos[:10], 1):
            doc += f"| {i} | {termino} | {nicho} |\n"
        
        doc += f"""---

## 🎯 Preguntas de Debate

"""
        
        for pregunta in self.preguntas.get('preguntas_debate', []):
            doc += f"### [{pregunta['tipo']}]\n"
            doc += f"{pregunta['pregunta']}\n\n"
        
        # Sección MeSH: solo términos clínicos validados
        if self.jerarquia.get('nicho_principal') in ['SALUD', 'AI_SAFETY'] and MeSHCache:
            try:
                from modulos.diccionario_clinico import DiccionarioClinico
                dc = DiccionarioClinico()
                
                doc += "---\n\n## 🔬 Términos MeSH Sugeridos\n\n"
                mesh = MeSHCache()
                
                for termino in self.terminos[:5]:
                    if dc.es_clinico(termino):
                        # Usar término normalizado (ej: vazu → ligamento)
                        termino_normalizado = dc.normalizar(termino)
                        alias_mesh = dc.get_alias_mesh(termino)
                        termino_busqueda = alias_mesh if alias_mesh else termino_normalizado
                        resultado = mesh.buscar(termino_busqueda)
                        if resultado.get('nombre_oficial'):
                            doc += f"- **{termino}** ({termino_normalizado}) → MeSH: {resultado['nombre_oficial']}\n"
                
                doc += "\n"
            except:
                pass
        
            doc += "---\n\n## 🧠 Reflexiones Post-Análisis\n\n"
            for i, reflexion in enumerate(self.reflexiones, 1):
                doc += f"{i}. {reflexion}\n\n"
        
        doc += f"""---

## 📊 Jerarquía Detectada

- **Núcleo**: {nicho}
"""
        
        if 'herramienta' in secundarios:
            doc += f"- **Herramienta**: {secundarios['herramienta']}\n"
        
        if 'contexto' in secundarios:
            doc += f"- **Contexto**: {secundarios['contexto']}\n"
        
        doc += f"""
---

*Generado por BrainHub v6.5 - {self._fecha()}*
"""
        
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write(doc)
        
        return doc
    
    def _fecha(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M')


if __name__ == '__main__':
    # Test
    from modulos.generar_abstract import GeneradorAbstract
    from modulos.preguntas_debate import GeneradorPreguntas
    
    jerarquia = {
        'recurso_id': 'test_01',
        'nicho_principal': 'SALUD',
        'secundarios': {
            'herramienta': 'TECNOLOGIA',
            'contexto': 'LEGAL'
        }
    }
    
    terminos = ['diagnóstico', 'paciente', 'machine learning', 'algoritmo']
    
    generador_abstract = GeneradorAbstract()
    abstract = generador_abstract.generar(jerarquia, terminos)
    
    generador_preguntas = GeneradorPreguntas()
    preguntas = generador_preguntas.generar(jerarquia, terminos)
    
    generador_doc = GeneradorDocumento()
    generador_doc.cargar_datos(jerarquia, terminos, abstract, preguntas)
    
    doc = generador_doc.generar_markdown('/data/data/com.termux/files/home/test_documento.md')
    
    print(doc)
