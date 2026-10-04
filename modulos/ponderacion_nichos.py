#!/data/data/com.termux/files/usr/bin/python3
"""
Análisis de Ponderación Multicriterio para jerarquizar nichos.
Métricas: densidad, posición, co-ocurrencia sintáctica.
"""

import re
from typing import Dict, List, Tuple


class PonderacionNichos:
    """Jerarquiza nichos con scoring 0-100."""
    
    # Nichos instrumentales (herramientas)
    NICHOS_INSTRUMENTALES = {'TECNOLOGIA', 'CIBERSEGURIDAD', 'IA'}
    
    # Nichos normativos/contextuales
    NICHOS_CONTEXTUALES = {'LEGAL', 'FINANZAS', 'EDUCACION'}
    
    def __init__(self, diccionario_nichos: Dict[str, List[str]] = None):
        self.diccionario = diccionario_nichos or {}
        self.margen_ganador = 0.15  # 15% de diferencia mínima
        # Precompilar patrones una sola vez: {nicho: [(termino, regex), ...]}
        self._patrones = {
            nicho: [(t, re.compile(rf"\b{re.escape(t)}\b")) for t in terminos]
            for nicho, terminos in self.diccionario.items()
        }
    
    # Reglas de coherencia de dominio
    HERRAMIENTAS_TECNOLOGIA = {'TECNOLOGIA': ['RAG', 'MACHINE_LEARNING']}
    
    def _detectar_herramienta_especifica(self, texto: str) -> str:
        """Detecta herramienta específica para TECNOLOGIA."""
        texto_lower = texto.lower()
        
        if 'rag' in texto_lower or 'retrieval' in texto_lower:
            return 'RAG'
        if 'machine learning' in texto_lower or 'deep learning' in texto_lower:
            return 'MACHINE_LEARNING'
        
        return 'TECNOLOGIA'
    
    def _densidad_semantica(self, texto: str) -> Dict[str, float]:
        """Métrica 1: densidad por volumen."""
        texto_lower = texto.lower()
        scores = {}
        
        for nicho, pares in self._patrones.items():
            count = sum(1 for _, pat in pares if pat.search(texto_lower))
            scores[nicho] = count
        
        # Normalizar a 0-100
        total = sum(scores.values())
        if total > 0:
            return {n: round((c / total) * 100, 2) for n, c in scores.items()}
        return scores
    
    def _relevancia_posicion(self, texto: str) -> Dict[str, float]:
        """Métrica 2: posición (apertura y cierre pesan más)."""
        palabras = texto.split()
        total = len(palabras)

        if total < 10:
            return {}

        # Dividir en 3 secciones
        apertura = ' '.join(palabras[:int(total * 0.15)])
        cuerpo = ' '.join(palabras[int(total * 0.15):int(total * 0.85)])
        cierre = ' '.join(palabras[int(total * 0.85):])

        scores = {}
        apertura_l = apertura.lower()
        cuerpo_l = cuerpo.lower()
        cierre_l = cierre.lower()

        for nicho, pares in self._patrones.items():
            score = 0
            # Apertura y cierre pesan x2
            for _, pat in pares:
                if pat.search(apertura_l):
                    score += 2
                if pat.search(cuerpo_l):
                    score += 1
                if pat.search(cierre_l):
                    score += 2
            scores[nicho] = score

        total = sum(scores.values())
        if total > 0:
            return {n: round((c / total) * 100, 2) for n, c in scores.items()}
        return scores
    
    def _coocurrencia_sintactica(self, texto: str) -> Dict[str, float]:
        """Métrica 3: sujeto vs complemento."""
        oraciones = re.split(r'[.!?]+', texto)
        scores = {}
        
        for nicho, pares in self._patrones.items():
            score = 0
            for oracion in oraciones:
                oracion_lower = oracion.lower()
                oracion_strip = oracion_lower.strip()
                # Termino al inicio de oracion = sujeto (nucleo)
                for _, pat in pares:
                    if pat.match(oracion_strip):
                        score += 3  # Sujeto
                    elif pat.search(oracion_lower):
                        score += 1  # Complemento
            scores[nicho] = score
        
        total = sum(scores.values())
        if total > 0:
            return {n: round((c / total) * 100, 2) for n, c in scores.items()}
        return scores
    
    def analizar(self, texto: str) -> Dict:
        """
        Análisis completo de jerarquización.
        
        Returns:
            {
                'scores': {'SALUD': 75.5, 'TECNOLOGIA': 45.2, 'LEGAL': 20.1},
                'nicho_principal': 'SALUD',
                'secundarios': {
                    'herramienta': 'TECNOLOGIA',
                    'contexto': 'LEGAL'
                }
            }
        """
        # Calcular las 3 métricas
        densidad = self._densidad_semantica(texto)
        posicion = self._relevancia_posicion(texto)
        sintactica = self._coocurrencia_sintactica(texto)
        
        # Consolidar (promedio ponderado: densidad 40%, posición 30%, sintáctica 30%)
        scores_finales = {}
        nichos = set(list(densidad.keys()) + list(posicion.keys()) + list(sintactica.keys()))
        
        for nicho in nichos:
            d = densidad.get(nicho, 0)
            p = posicion.get(nicho, 0)
            s = sintactica.get(nicho, 0)
            scores_finales[nicho] = round(d * 0.4 + p * 0.3 + s * 0.3, 2)
        
        # Ordenar
        ordenados = sorted(scores_finales.items(), key=lambda x: x[1], reverse=True)
        
        if not ordenados:
            return {
                'scores': {},
                'nicho_principal': 'GENERAL',
                'secundarios': {}
            }
        
        nicho_principal = ordenados[0][0]
        
        # Clasificar secundarios
        secundarios = {}
        for nicho, score in ordenados[1:]:
            if nicho in self.NICHOS_INSTRUMENTALES:
                secundarios['herramienta'] = nicho
            elif nicho in self.NICHOS_CONTEXTUALES:
                secundarios['contexto'] = nicho
            else:
                secundarios['secundario'] = nicho
        
        return {
            'scores': scores_finales,
            'nicho_principal': nicho_principal,
            'secundarios': secundarios
        }


if __name__ == '__main__':
    # Diccionario de prueba
    diccionario = {
        'SALUD': ['diagnóstico', 'paciente', 'tratamiento', 'síntoma', 'hospital'],
        'TECNOLOGIA': ['software', 'algoritmo', 'python', 'datos', 'machine learning'],
        'LEGAL': ['ley', 'juzgado', 'normativa', 'expediente', 'fiscal']
    }
    
    ponderador = PonderacionNichos(diccionario)
    
    texto_prueba = """
    Hoy analizaremos el impacto de las leyes en el diagnóstico clínico.
    El software de machine learning procesa datos de pacientes.
    La normativa legal establece que el tratamiento debe ser validado.
    Finalmente, el hospital implementa estas regulaciones.
    """
    
    resultado = ponderador.analizar(texto_prueba)
    
    print("📊 PONDERACIÓN MULTICRITERIO")
    print("=" * 50)
    print(f"\n   Scores:")
    for nicho, score in resultado['scores'].items():
        barra = '█' * int(score / 5)
        print(f"   {nicho:15s} {score:>6.2f} {barra}")
    
    print(f"\n   Nicho principal: {resultado['nicho_principal']}")
    print(f"   Secundarios: {resultado['secundarios']}")
