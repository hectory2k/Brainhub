#!/data/data/com.termux/files/usr/bin/python3
"""
Generador de preguntas de debate con plantillas morfológicas + datos reales.
Mantiene estructura consistente con especificidad del documento.
"""

from typing import Dict, List, Optional


class GeneradorPreguntas:
    """Genera preguntas combinando plantillas y co-ocurrencias reales."""
    
    # Plantillas morfológicas: verbo + slots
    PLANTILLAS = {
        'conceptual': '¿Qué implicancias tiene {origen} + {destino} (frecuencia: {frecuencia}) para {contexto}?',
        'metodologica': '¿Cómo se relaciona {herramienta} con {terminos}?',
        'critica': '¿Qué pasaría si {termino_principal} escala a producción?',
        'exploratoria': '¿Qué alternativas existen para {termino_principal} considerando {contexto}?',
    }
    
    def _detectar_idioma(self, terminos: List[str]) -> str:
        """Detecta idioma para generar en ES o EN."""
        palabras_en = {'the', 'and', 'for', 'with', 'documents', 'content', 'system', 'reflection'}
        palabras_es = {'el', 'la', 'los', 'para', 'con', 'documento', 'sistema'}
        
        score_en = sum(1 for t in terminos if t.lower() in palabras_en)
        score_es = sum(1 for t in terminos if t.lower() in palabras_es)
        
        return 'en' if score_en > score_es else 'es'
    
    def generar(
        self,
        jerarquia: Dict,
        terminos_clave: List[str],
        coocurrencias: List = None,
        texto_completo: str = ""
    ) -> Dict:
        """
        Genera preguntas usando plantillas morfológicas + datos reales.
        """
        preguntas = []
        idioma = self._detectar_idioma(terminos_clave)
        
        # 1. Pregunta conceptual desde co-ocurrencia más fuerte
        # Filtrar co-ocurrencias redundantes (singular vs plural)
        coocurrencias_filtradas = []
        for co in (coocurrencias or []):
            if isinstance(co, list) and len(co) >= 2:
                par, frecuencia = co
                origen, destino = par
                # Evitar pares muy similares (model vs models)
                if origen.lower().rstrip('s') != destino.lower().rstrip('s'):
                    coocurrencias_filtradas.append(co)
        
        coocurrencias = coocurrencias_filtradas if coocurrencias_filtradas else coocurrencias


        if coocurrencias and len(coocurrencias) > 0:
            par_top, frecuencia = coocurrencias[0]
            origen, destino = par_top
            
            if idioma == 'en':
                pregunta = (
                    f"What implications does the relationship between '{origen}' "
                    f"and '{destino}' (frequency: {frecuencia}) have for "
                    f"{jerarquia.get('nicho_principal', '')}?"
                )
            else:
                pregunta = self.PLANTILLAS['conceptual'].format(
                    origen=origen,
                    destino=destino,
                    frecuencia=frecuencia,
                    contexto=jerarquia.get('nicho_principal', '').lower()
                )
            
            preguntas.append({
                'tipo': 'Conceptual / Técnica',
                'pregunta': pregunta
            })
        
        # 2. Pregunta metodológica usando herramienta y términos
        secundarios = jerarquia.get('secundarios', {})
        herramienta = secundarios.get('herramienta')
        
        if herramienta and terminos_clave:
            terminos_str = ', '.join(terminos_clave[:3])
            
            if idioma == 'en':
                pregunta = (
                    f"How does {herramienta} relate to {terminos_str}?"
                )
            else:
                pregunta = self.PLANTILLAS['metodologica'].format(
                    herramienta=herramienta,
                    terminos=terminos_str
                )
            
            preguntas.append({
                'tipo': 'Metodológica',
                'pregunta': pregunta
            })
        
        # 3. Pregunta crítica usando término principal
        if terminos_clave:
            termino_principal = terminos_clave[0]
            
            if idioma == 'en':
                pregunta = (
                    f"What would happen if {termino_principal} scales to production?"
                )
            else:
                pregunta = self.PLANTILLAS['critica'].format(
                    termino_principal=termino_principal
                )
            
            preguntas.append({
                'tipo': 'Crítica / Reflexión',
                'pregunta': pregunta
            })
        
        # 4. Pregunta exploratoria si hay gaps
        gaps = ['error', 'problema', 'riesgo', 'falla', 'límite']
        if texto_completo:
            gaps_encontrados = [g for g in gaps if g in texto_completo.lower()]
            if gaps_encontrados and terminos_clave:
                if idioma == 'en':
                    pregunta = (
                        f"What alternatives exist for {terminos_clave[0]} "
                        f"considering {gaps_encontrados[0]}?"
                    )
                else:
                    pregunta = self.PLANTILLAS['exploratoria'].format(
                        termino_principal=terminos_clave[0],
                        contexto=gaps_encontrados[0]
                    )
                
                preguntas.append({
                    'tipo': 'Exploratoria',
                    'pregunta': pregunta
                })
        
        return {
            'recurso_id': jerarquia.get('recurso_id', 'sin_id'),
            'preguntas_debate': preguntas
        }


if __name__ == '__main__':
    jerarquia = {
        'recurso_id': 'test',
        'nicho_principal': 'TECNOLOGIA',
        'secundarios': {'herramienta': 'RAG'}
    }
    
    terminos = ['reflection', 'documents', 'const']
    coocurrencias = [[['reflection', 'documents'], 19]]
    
    gen = GeneradorPreguntas()
    resultado = gen.generar(jerarquia, terminos, coocurrencias)
    
    print("🎯 PREGUNTAS GENERADAS:")
    for p in resultado['preguntas_debate']:
        print(f"\n[{p['tipo']}]")
        print(f"   {p['pregunta']}")
