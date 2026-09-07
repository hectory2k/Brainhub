#!/data/data/com.termux/files/usr/bin/python3
"""
Coherencia de nichos para BrainHub.
Valida que la jerarquía sea lógica según el dominio.
"""

from typing import Dict, Optional


class CoherenciaNichos:
    """Valida coherencia de jerarquía de nichos."""
    
    # Herramientas válidas por nicho principal
    HERRAMIENTAS_POR_NICHO = {
        'TECNOLOGIA': ['RAG', 'MACHINE_LEARNING', 'DATA_SCIENCE', 'CIBERSEGURIDAD', 'AI_SAFETY'],
        'SALUD': ['TECNOLOGIA', 'IA', 'DATA_SCIENCE'],
        'LEGAL': ['TECNOLOGIA', 'CIBERSEGURIDAD'],
        'FINANZAS': ['TECNOLOGIA', 'DATA_SCIENCE'],
        'COMPRAS_PUBLICAS': ['DATA_SCIENCE', 'MACHINE_LEARNING'],
    }
    
    # Contextos válidos por nicho principal
    CONTEXTOS_POR_NICHO = {
        'TECNOLOGIA': ['LEGAL', 'FINANZAS', 'COMPRAS_PUBLICAS', 'AI_SAFETY'],
        'SALUD': ['LEGAL', 'FINANZAS'],
        'LEGAL': ['FINANZAS', 'SALUD'],
        'FINANZAS': ['LEGAL', 'COMPRAS_PUBLICAS'],
        'COMPRAS_PUBLICAS': ['LEGAL', 'FINANZAS'],
    }
    
    # Detección de herramientas específicas
    PATRONES_HERRAMIENTA = {
        'RAG': ['rag', 'retrieval', 'embedding'],
        'MACHINE_LEARNING': ['machine learning', 'deep learning', 'model'],
        'DATA_SCIENCE': ['data science', 'analytics', 'mining'],
        'CIBERSEGURIDAD': ['security', 'hack', 'vulnerability'],
    }
    
    def detectar_herramienta(self, texto: str, nicho_principal: str) -> Optional[str]:
        """Detecta herramienta específica según contenido."""
        texto_lower = texto.lower()
        
        # Herramientas válidas para el nicho
        herramientas_validas = self.HERRAMIENTAS_POR_NICHO.get(nicho_principal, [])
        
        # Buscar herramienta con más evidencia
        mejor_herramienta = None
        mejor_score = 0
        
        for herramienta, patrones in self.PATRONES_HERRAMIENTA.items():
            if herramienta not in herramientas_validas:
                continue
            
            score = sum(1 for p in patrones if p in texto_lower)
            if score > mejor_score:
                mejor_score = score
                mejor_herramienta = herramienta
        
        return mejor_herramienta
    
    def validar_jerarquia(self, jerarquia: Dict) -> bool:
        """Valida que la jerarquía sea coherente."""
        nucleo = jerarquia.get('nicho_principal', '')
        secundarios = jerarquia.get('secundarios', {})
        
        herramienta = secundarios.get('herramienta')
        contexto = secundarios.get('contexto')
        
        # Validar herramienta
        if herramienta and nucleo in self.HERRAMIENTAS_POR_NICHO:
            if herramienta not in self.HERRAMIENTAS_POR_NICHO[nucleo]:
                return False
        
        # Validar contexto
        if contexto and nucleo in self.CONTEXTOS_POR_NICHO:
            if contexto not in self.CONTEXTOS_POR_NICHO[nucleo]:
                return False
        
        return True
    
    def corregir_jerarquia(self, jerarquia: Dict, texto: str) -> Dict:
        """Corrige jerarquía si es incoherente."""
        nucleo = jerarquia.get('nicho_principal', '')
        
        # Detectar herramienta correcta
        herramienta_detectada = self.detectar_herramienta(texto, nucleo)
        if herramienta_detectada:
            jerarquia['secundarios']['herramienta'] = herramienta_detectada
        
        # Validar
        if not self.validar_jerarquia(jerarquia):
            # Corregir eliminando secundarios inválidos
            herramientas_validas = self.HERRAMIENTAS_POR_NICHO.get(nucleo, [])
            herramienta_actual = jerarquia.get('secundarios', {}).get('herramienta')
            
            if herramienta_actual and herramienta_actual not in herramientas_validas:
                del jerarquia['secundarios']['herramienta']
        
        return jerarquia


if __name__ == '__main__':
    coherencia = CoherenciaNichos()
    
    # Test
    jerarquia = {
        'nicho_principal': 'TECNOLOGIA',
        'secundarios': {'herramienta': 'CIBERSEGURIDAD'}
    }
    
    texto = "rag retrieval documents"
    
    corregida = coherencia.corregir_jerarquia(jerarquia, texto)
    print(f"✅ Jerarquía corregida:")
    print(f"   Núcleo: {corregida['nicho_principal']}")
    print(f"   Secundarios: {corregida['secundarios']}")
