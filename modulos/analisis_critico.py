#!/data/data/com.termux/files/usr/bin/python3
"""
Análisis Crítico: Premisa vs Evidencia para BrainHub.
Extrae premisas, evalúa evidencia y califica rigor lógico.
"""

from typing import Dict, List


class AnalisisCritico:
    """Extrae y evalúa premisas con su evidencia."""
    
    # Palabras que indican especulación
    MARCADORES_ESPECULATIVO = [
        'probablemente', 'posiblemente', 'podría', 'puede que',
        'se espera', 'se anticipa', 'potencialmente', 'quizás'
    ]
    
    # Palabras que indican evidencia empírica
    MARCADORES_EVIDENCIA = [
        'demostró', 'observó', 'evaluaciones', 'incidente',
        'resultados', 'datos', 'experimento', 'prueba',
        'evaluations', 'observed', 'results', 'incident',
        'evidence', 'empirical', 'internal results'
    ]
    
    def analizar(self, texto: str, terminos_clave: List[str]) -> Dict:
        """
        Analiza texto y extrae matriz premisa vs evidencia.
        
        Returns:
            {'nodos': [...], 'resumen_calidad': {...}}
        """
        texto_lower = texto.lower()
        nodos = []
        
        # Detectar premisas principales (por términos clave)
        premisas_vistas = set()
        for termino in terminos_clave[:5]:
            if termino in texto_lower:
                premisa = self._extraer_premisa(texto, termino)
                evidencia = self._buscar_evidencia(texto, termino)
                supuestos = self._detectar_supuestos(texto, termino)
                calificacion = self._calificar(texto, termino)
                
                if premisa in premisas_vistas:
                    continue
                premisas_vistas.add(premisa)
                
                nodos.append({
                    'nodo_id': f"nodo_{termino.replace(' ', '_')}",
                    'nicho': 'AI_SAFETY',
                    'premisa': premisa,
                    'evidencia': evidencia,
                    'supuestos_implicitos': supuestos,
                    'nivel_respaldo': calificacion
                })
        
        return {
            'nodos': nodos,
            'resumen_calidad': self._resumen_calidad(nodos)
        }
    
    def _extraer_premisa(self, texto: str, termino: str) -> str:
        """Extrae la premisa principal relacionada al término."""
        # Buscar oración que contenga el término
        oraciones = texto.split('.')
        for oracion in oraciones:
            if termino in oracion.lower() and len(oracion.strip()) > 50:
                return oracion.strip()[:200]
        return f"Premisa sobre {termino}"
    
    def _buscar_evidencia(self, texto: str, termino: str) -> List[str]:
        """Busca evidencia en la misma oración que el término."""
        evidencia = []
        oraciones = texto.split('.')
        
        # Buscar evidencia en la oración específica del término
        for oracion in oraciones:
            if termino in oracion.lower():
                oracion_lower = oracion.lower()
                for marcador in self.MARCADORES_EVIDENCIA:
                    if marcador in oracion_lower:
                        evidencia.append(f"Evidencia local: '{marcador}' en la misma oración")
                break
        
        return evidencia if evidencia else ['Sin evidencia empírica directa en la misma oración']
    
    def _detectar_supuestos(self, texto: str, termino: str) -> List[str]:
        """Detecta supuestos implícitos."""
        supuestos = []
        
        if 'scaling' in texto.lower() or 'escalado' in texto.lower():
            supuestos.append('Asume que el escalado continuará sin cuellos de botella')
        
        if 'monitoring' in texto.lower() or 'monitoreo' in texto.lower():
            supuestos.append('Asume que el razonamiento no verbalizado oculta comportamientos')
        
        if not supuestos:
            supuestos.append('Supuesto implícito no detectado')
        
        return supuestos
    
    def _calificar(self, texto: str, termino: str) -> str:
        """Califica usando la oración específica del término."""
        oraciones = texto.split('.')
        
        # Encontrar la oración del término
        oracion_termino = ""
        for oracion in oraciones:
            if termino in oracion.lower():
                oracion_termino = oracion.lower()
                break
        
        if not oracion_termino:
            return 'ESPECULATIVO'
        
        tiene_evidencia = any(m in oracion_termino for m in self.MARCADORES_EVIDENCIA)
        tiene_especulacion = any(m in oracion_termino for m in self.MARCADORES_ESPECULATIVO)
        
        if tiene_evidencia and not tiene_especulacion:
            return 'SOSTENIDO'
        elif tiene_evidencia and tiene_especulacion:
            return 'PARCIAL'
        else:
            return 'ESPECULATIVO'
    
    def _resumen_calidad(self, nodos: List[Dict]) -> Dict:
        """Resumen de calidad del análisis."""
        total = len(nodos)
        sostenidos = sum(1 for n in nodos if n['nivel_respaldo'] == 'SOSTENIDO')
        especulativos = sum(1 for n in nodos if n['nivel_respaldo'] == 'ESPECULATIVO')
        
        return {
            'total_premisas': total,
            'sostenidas': sostenidos,
            'especulativas': especulativos,
            'porcentaje_evidencia': round((sostenidos / total * 100) if total else 0, 1)
        }


if __name__ == '__main__':
    analizador = AnalisisCritico()
    
    texto = """
    La capacidad de monitorear mediante chain-of-thought se reduce.
    Evaluaciones internas demostraron degradación.
    El progreso puede sostenerse hacia automejora recursiva.
    El incidente OpenAI-Hugging Face observó fallos de alcance.
    """
    
    terminos = ['alignment', 'scaling', 'monitoring', 'reasoning']
    
    resultado = analizador.analizar(texto, terminos)
    
    print("🔬 ANÁLISIS CRÍTICO")
    print("=" * 50)
    
    for nodo in resultado['nodos']:
        print(f"\n📌 {nodo['premisa'][:80]}...")
        print(f"   Calificación: {nodo['nivel_respaldo']}")
        print(f"   Evidencia: {nodo['evidencia'][:2]}")
    
    print(f"\n📊 Resumen: {resultado['resumen_calidad']}")
