#!/data/data/com.termux/files/usr/bin/python3
"""
Generador de preguntas PICO para documentos médicos.
Paciente + Intervención + Comparación + Outcome.
"""

from typing import Dict, List


class PICOGenerator:
    """Genera preguntas clínicas estructuradas."""
    
    def generar_pico(self, terminos: List[str], nicho: str) -> Dict:
        """
        Genera pregunta PICO desde términos clave.
        
        Returns:
            {'p': '...', 'i': '...', 'c': '...', 'o': '...', 'pregunta': '...'}
        """
        if len(terminos) < 2:
            return {'error': 'Se necesitan al menos 2 términos'}
        
        # Asignar roles PICO según posición y nicho
        p = 'pacientes con ' + terminos[0] if terminos else 'pacientes'
        i = terminos[1] if len(terminos) > 1 else 'intervención'
        c = 'tratamiento estándar'
        o = terminos[2] if len(terminos) > 2 else 'resultado clínico'
        
        pregunta = f"En {p}, ¿cuál es el efecto de {i} comparado con {c} sobre {o}?"
        
        return {
            'P': p,
            'I': i,
            'C': c,
            'O': o,
            'pregunta': pregunta
        }
    
    def generar_pico_ponderado(self, terminos_con_peso: List) -> Dict:
        """
        Genera PICO usando la frecuencia como señal.
        - Término más frecuente → P (problema principal)
        - Segundo más frecuente → I (intervención)
        - Términos de riesgo/resultado → O (outcome)
        """
        if not terminos_con_peso:
            return self.generar_pico([], 'SALUD')
        
        # Ordenar por frecuencia
        ordenados = sorted(terminos_con_peso, key=lambda x: x[1] if isinstance(x, (list, tuple)) else 0, reverse=True)
        
        # Palabras que indican outcome
        palabras_outcome = ['riesgo', 'riziko', 'risk', 'resultado', 'outcome', 'mortalidad']
        
        # Asignar roles por frecuencia
        p = ordenados[0][0] if ordenados else 'pacientes'
        i = ordenados[1][0] if len(ordenados) > 1 else 'intervención'
        o = 'riesgo'
        
        # Buscar término de outcome en la lista
        for termino, peso in ordenados:
            if termino.lower() in palabras_outcome:
                o = termino
                break
        
        pregunta = f"En pacientes con {p}, ¿cuál es el efecto de {i} sobre {o}?"
        
        return {
            'P': f'pacientes con {p}',
            'I': i,
            'C': 'tratamiento estándar',
            'O': o,
            'pregunta': pregunta,
            'pesos': [(t, p) for t, p in ordenados[:5]]
        }
    
    def generar_desde_analisis(self, analisis: Dict) -> Dict:
        """Genera PICO desde análisis BrainHub."""
        terminos = [t[0] if isinstance(t, (list, tuple)) else t 
                    for t in analisis.get('terminos_clave', [])]
        nicho = analisis.get('nicho', 'GENERAL')
        
        return self.generar_pico(terminos, nicho)


if __name__ == '__main__':
    gen = PICOGenerator()
    
    terminos = ['pacientes UCI', 'úlceras por presión', 'prevención']
    pico = gen.generar_pico(terminos, 'SALUD')
    
    print("📋 PREGUNTA PICO")
    print("=" * 50)
    print(f"\nP: {pico['P']}")
    print(f"I: {pico['I']}")
    print(f"C: {pico['C']}")
    print(f"O: {pico['O']}")
    print(f"\nPregunta: {pico['pregunta']}")
