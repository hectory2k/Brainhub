#!/data/data/com.termux/files/usr/bin/python3
"""
Generador de Abstract jerárquico para BrainHub.
Estructura: Núcleo → Herramienta → Contexto.
"""

from typing import Dict, List, Optional


class GeneradorAbstract:
    """Genera resúmenes jerárquicos con plantillas."""
    
    # Plantillas de estructura
    PLANTILLA_NUCLEO = (
        "Este recurso aborda principalmente el desarrollo de {concepto} "
        "en el ámbito de {nicho}. El foco está puesto en {detalle}."
    )
    
    PLANTILLA_HERRAMIENTA = (
        "Para su ejecución, se analiza la implementación de {herramienta}, "
        "detallando el uso de {conceptos_tecnicos} "
        "{detalle_timestamp}."
    )
    
    PLANTILLA_CONTEXTO = (
        "Finalmente, el análisis se contextualiza bajo el marco {contexto}, "
        "discutiendo las implicancias de {conceptos_contexto}."
    )
    
    # Diccionario de corrección de errores de transcripción
    CORRECCIONES = {
        'machin lerning': 'machine learning',
        'deep lerning': 'deep learning',
        'historia clinica': 'historia clínica',
        'inteligencia artifical': 'inteligencia artificial',
        'sistem': 'sistema',
        'mercdo': 'mercado',
    }
    
    def __init__(self, max_palabras_parrafo: int = 60):
        self.max_palabras = max_palabras_parrafo
    
    def corregir_errores(self, texto: str) -> str:
        """Aplica diccionario de corrección de transcripción."""
        for error, correcto in self.CORRECCIONES.items():
            texto = texto.replace(error, correcto)
        return texto
    
    def _controlar_extension(self, texto: str) -> str:
        """Limita párrafo a max_palabras."""
        palabras = texto.split()
        if len(palabras) > self.max_palabras:
            return ' '.join(palabras[:self.max_palabras]) + '...'
        return texto
    
    def extraer_concepto_nucleo(self, terminos_clave: List[str]) -> str:
        """Extrae concepto principal de términos clave."""
        if terminos_clave:
            return terminos_clave[0]
        return 'los hallazgos principales'
    
    def extraer_detalle(self, terminos_clave: List[str]) -> str:
        """Extrae detalle del núcleo."""
        if len(terminos_clave) >= 3:
            return f"la revisión de {', '.join(terminos_clave[:3])}"
        return 'los conceptos clave del contenido'
    
    def extraer_conceptos_tecnicos(self, terminos_clave: List[str]) -> str:
        """Extrae conceptos técnicos."""
        tecnicos = [t for t in terminos_clave if t not in ['salud', 'paciente', 'legal']]
        if tecnicos:
            return ', '.join(tecnicos[:3])
        return 'las herramientas técnicas relevantes'
    
    def generar(
        self,
        jerarquia: Dict,
        terminos_clave: List[str],
        timestamps: Optional[Dict] = None
    ) -> str:
        """
        Genera Abstract jerárquico.
        
        Args:
            jerarquia: {'nicho_principal': 'SALUD', 'secundarios': {...}}
            terminos_clave: Lista de términos principales
            timestamps: {'inicio': '03:15', 'fin': '06:40'} (opcional)
        
        Returns:
            Abstract en Markdown
        """
        nicho = jerarquia.get('nicho_principal', 'GENERAL')
        secundarios = jerarquia.get('secundarios', {})
        
        # Párrafo 1: Núcleo
        concepto = self.extraer_concepto_nucleo(terminos_clave)
        detalle = self.extraer_detalle(terminos_clave)
        parrafo_nucleo = self.PLANTILLA_NUCLEO.format(
            concepto=concepto,
            nicho=nicho,
            detalle=detalle
        )
        
        # Párrafo 2: Herramienta (si existe)
        parrafo_herramienta = None
        herramienta = secundarios.get('herramienta')
        if herramienta:
            conceptos = self.extraer_conceptos_tecnicos(terminos_clave)
            if timestamps and timestamps.get('inicio') and timestamps.get('fin'):
                inicio = timestamps['inicio']
                fin = timestamps['fin']
                detalle_timestamp = f" (Especialmente visible entre los minutos {inicio} y {fin})"
            else:
                detalle_timestamp = ""  # Sin timestamps para texto estático
            parrafo_herramienta = self.PLANTILLA_HERRAMIENTA.format(
                herramienta=herramienta,
                conceptos_tecnicos=conceptos,
                inicio=inicio,
                fin=fin
            )
        
        # Párrafo 3: Contexto (si existe)
        parrafo_contexto = None
        contexto = secundarios.get('contexto')
        if contexto:
            conceptos_contexto = 'las normativas y regulaciones aplicables'
            parrafo_contexto = self.PLANTILLA_CONTEXTO.format(
                contexto=contexto,
                conceptos_contexto=conceptos_contexto
            )
        
        # Ensamblar
        abstract = f"## Resumen Ejecutivo\n\n{parrafo_nucleo}"
        
        if parrafo_herramienta:
            abstract += f"\n\n{parrafo_herramienta}"
        
        if parrafo_contexto:
            abstract += f"\n\n{parrafo_contexto}"
        
        # Limpieza
        abstract = self.corregir_errores(abstract)
        
        return abstract


if __name__ == '__main__':
    generador = GeneradorAbstract()
    
    # Test
    jerarquia = {
        'nicho_principal': 'SALUD',
        'secundarios': {
            'herramienta': 'TECNOLOGIA',
            'contexto': 'LEGAL'
        }
    }
    
    terminos = ['diagnóstico', 'paciente', 'machine learning', 'algoritmo', 'normativa']
    
    abstract = generador.generar(
        jerarquia,
        terminos,
        timestamps={'inicio': '03:15', 'fin': '06:40'}
    )
    
    print(abstract)
