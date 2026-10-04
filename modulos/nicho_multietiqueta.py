#!/data/data/com.termux/files/usr/bin/python3
"""
Clasificación multietiqueta con confianza para BrainHub.
Detecta nichos simultáneos y genera híbridos automáticamente.
"""

import re
from typing import Dict, List, Tuple


class NichoMultietiqueta:
    """Clasificador multietiqueta con puntuación de confianza."""
    
    # Matriz de híbridos automáticos
    MATRIZ_HIBRIDOS = {
        frozenset(['SALUD', 'TECNOLOGIA']): 'HEALTH-TECH',
        frozenset(['FINANZAS', 'TECNOLOGIA']): 'FIN-TECH',
        frozenset(['LEGAL', 'TECNOLOGIA']): 'LEGAL-TECH',
        frozenset(['SALUD', 'LEGAL']): 'MEDICO-LEGAL',
        frozenset(['CIBERSEGURIDAD', 'TECNOLOGIA']): 'SECURITY-TECH',
        frozenset(['SALUD', 'FINANZAS']): 'HEALTH-FINANCE',
    }
    
    # Diccionario de términos por nicho
    TERMINOS_NICHO = {
        'SALUD': [
            'paciente', 'diagnostico', 'diagnóstico', 'tratamiento', 'salud',
            'clinica', 'clínica', 'historia clinica', 'medico', 'médico',
            'enfermedad', 'sintoma', 'síntoma', 'hospital'
        ],
        'TECNOLOGIA': [
            'python', 'machine learning', 'deep learning', 'inteligencia artificial',
            'algoritmo', 'tensor', 'modelo', 'datos', 'software', 'codigo',
            'código', 'programacion', 'programación', 'ia', 'red neuronal'
        ],
        'LEGAL': [
            'expediente', 'juzgado', 'sentencia', 'demanda', 'fiscal',
            'abogado', 'ley', 'artículo', 'articulo', 'jurisprudencia'
        ],
        'CIBERSEGURIDAD': [
            'hacker', 'vulnerabilidad', 'phishing', 'malware', 'exploit',
            'seguridad', 'ataque', 'cifrado', 'encriptacion'
        ],
        'FINANZAS': [
            'inversion', 'inversión', 'mercado', 'acciones', 'cripto',
            'finanzas', 'banco', 'capital', 'rendimiento'
        ]
    }
    
    # Umbral para híbridos
    UMBRAL_HIBRIDO = 0.6
    
    def analizar(self, texto: str) -> Dict:
        """
        Analiza texto y retorna nichos con confianza.
        
        Returns:
            {
                'nichos': {'SALUD': 0.85, 'TECNOLOGIA': 0.70},
                'dominante': 'SALUD',
                'hibrido': 'HEALTH-TECH' (si aplica),
                'etiquetas': ['SALUD', 'TECNOLOGIA']
            }
        """
        texto_lower = texto.lower()
        confianzas = {}
        
        # Calcular confianza por nicho
        for nicho, terminos in self.TERMINOS_NICHO.items():
            score = 0
            for termino in terminos:
                if re.search(rf"\b{re.escape(termino)}\b", texto_lower):
                    score += 1
            # Normalizar a 0-1
            confianza = min(score / 10, 1.0)
            if confianza > 0:
                confianzas[nicho] = round(confianza, 2)
        
        if not confianzas:
            return {
                'nichos': {'GENERAL': 1.0},
                'dominante': 'GENERAL',
                'hibrido': None,
                'etiquetas': ['GENERAL']
            }
        
        # Ordenar por confianza
        ordenados = sorted(confianzas.items(), key=lambda x: x[1], reverse=True)
        dominante = ordenados[0][0]
        
        # Detectar híbrido si dos nichos superan umbral
        hibrido = None
        nichos_altos = [n for n, c in confianzas.items() if c >= self.UMBRAL_HIBRIDO]
        
        if len(nichos_altos) >= 2:
            clave = frozenset(nichos_altos[:2])
            hibrido = self.MATRIZ_HIBRIDOS.get(clave)
        
        return {
            'nichos': confianzas,
            'dominante': dominante,
            'hibrido': hibrido,
            'etiquetas': list(confianzas.keys())
        }


if __name__ == '__main__':
    clasificador = NichoMultietiqueta()
    
    # Test con contenido mixto SALUD + TECNOLOGIA
    texto_mixto = """
    Usamos deep learning y machine learning para analizar 
    la historia clinica del paciente. El modelo de inteligencia 
    artificial mejora el diagnostico médico.
    """
    
    resultado = clasificador.analizar(texto_mixto)
    
    print("📊 ANÁLISIS MULTIETIQUETA")
    print("=" * 40)
    print(f"\n   Nichos detectados:")
    for nicho, confianza in resultado['nichos'].items():
        barra = '█' * int(confianza * 20)
        print(f"   {nicho:20s} {confianza:.2f} {barra}")
    
    print(f"\n   Dominante: {resultado['dominante']}")
    print(f"   Híbrido: {resultado['hibrido'] or 'Ninguno'}")
    print(f"   Etiquetas: {', '.join(resultado['etiquetas'])}")
