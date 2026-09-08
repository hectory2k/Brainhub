#!/data/data/com.termux/files/usr/bin/python3
"""Generador de preguntas de debate para BrainHub."""

from typing import Dict, List


class GeneradorPreguntas:
    """Genera preguntas específicas para documentos."""
    
    def generar_desde_citas(self, citas_clave: List[str], terminos_clave: List[str]) -> List[Dict]:
        """Genera preguntas basadas en citas reales del documento."""
        preguntas = []
        
        if not citas_clave:
            return self._generar_desde_coocurrencias(terminos_clave)
        
        cita_principal = citas_clave[0][:150] if citas_clave else ''
        termino_top = terminos_clave[0] if terminos_clave else 'el fenómeno'
        
        preguntas.append({
            'tipo': 'Evidencia',
            'pregunta': f"El documento plantea que \"{cita_principal}...\". ¿Qué evidencia respalda esta afirmación sobre {termino_top}?"
        })
        
        if len(terminos_clave) >= 2:
            t1, t2 = terminos_clave[0], terminos_clave[1]
            preguntas.append({
                'tipo': 'Implicación Práctica',
                'pregunta': f"Según el análisis, {t1} afecta {t2}. ¿Qué implicaciones tiene esto?"
            })
        
        preguntas.append({
            'tipo': 'Limitaciones',
            'pregunta': f"¿Qué limitaciones presenta el estudio sobre {termino_top}?"
        })
        
        return preguntas
    
    def _generar_desde_coocurrencias(self, terminos_clave: List[str]) -> List[Dict]:
        """Genera preguntas desde relaciones de co-ocurrencia."""
        preguntas = []
        
        if len(terminos_clave) < 2:
            return []
        
        t1, t2 = terminos_clave[0], terminos_clave[1]
        
        preguntas.append({
            'tipo': 'Relación Central',
            'pregunta': f"¿Qué mecanismos explican la relación entre {t1} y {t2}?"
        })
        
        if len(terminos_clave) >= 3:
            t3 = terminos_clave[2]
            preguntas.append({
                'tipo': 'Implicación',
                'pregunta': f"¿Cómo afecta {t3} a la relación entre {t1} y {t2}?"
            })
        
        preguntas.append({
            'tipo': 'Aplicación',
            'pregunta': f"¿Qué aplicaciones prácticas surgen de entender {t1} en profundidad?"
        })
        
        return preguntas
    
    def generar(self, jerarquia: Dict, terminos_clave: List[str], 
                coocurrencias: List = None, texto_completo: str = "") -> Dict:
        """Método principal: usa co-ocurrencias para preguntas específicas."""
        return {
            'recurso_id': jerarquia.get('recurso_id', 'sin_id'),
            'preguntas_debate': self._generar_desde_coocurrencias(terminos_clave)
        }


if __name__ == '__main__':
    gen = GeneradorPreguntas()
    terminos = ['cognitive', 'skills', 'acquisition']
    
    preguntas = gen.generar({'recurso_id': 'test'}, terminos)
    
    print("🎯 PREGUNTAS ESPECÍFICAS:")
    for p in preguntas['preguntas_debate']:
        print(f"\n[{p['tipo']}]")
        print(f"   {p['pregunta']}")
