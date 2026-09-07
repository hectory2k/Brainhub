#!/data/data/com.termux/files/usr/bin/python3
"""Resumen adaptativo por perfil para BrainHub."""

from typing import Dict


class ResumenPorPerfil:
    """Genera resúmenes adaptados al perfil del lector."""
    
    PERFIL_POR_NICHO = {
        'AI_SAFETY': 'tecnico',
        'TECNOLOGIA': 'tecnico',
        'SALUD': 'divulgacion',
        'LEGAL': 'ejecutivo',
        'COMPRAS_PUBLICAS': 'ejecutivo',
        'FINANZAS': 'ejecutivo',
        'CIBERSEGURIDAD': 'tecnico'
    }
    
    def generar(self, perfil: str = None, analisis: Dict = None) -> str:
        """Genera resumen según perfil auto-detectado."""
        if analisis is None:
            analisis = {}
        
        nicho = analisis.get('nicho', 'GENERAL')
        secundarios = analisis.get('secundarios', {})
        
        # Solo auto-detectar si no se especificó perfil
        if perfil is None:
            perfil = self.PERFIL_POR_NICHO.get(nicho, 'tecnico')
            
            # Refinar por secundarios solo en modo auto
            if secundarios.get('herramienta') in ['RAG', 'MACHINE_LEARNING']:
                perfil = 'tecnico'
            elif secundarios.get('contexto') in ['LEGAL', 'FINANZAS']:
                perfil = 'ejecutivo'
        
        terminos = analisis.get('terminos_clave', [])
        coocurrencias = analisis.get('coocurrencias', [])
        
        if perfil == 'ejecutivo':
            return self._resumen_ejecutivo(terminos, nicho, secundarios)
        elif perfil == 'tecnico':
            return self._resumen_tecnico(terminos, nicho, secundarios)
        else:
            return self._resumen_divulgacion(terminos, nicho)
    
    def _resumen_ejecutivo(self, terminos, nicho, secundarios):
        tesis = terminos[0][0] if terminos else 'el tema'
        herramienta = secundarios.get('herramienta', 'no especificada')
        
        return f"""# Resumen Ejecutivo

## Tesis Central
El contenido analiza {tesis} en el ámbito de {nicho}.

## Herramienta Principal
{herramienta}

## Impacto Estratégico
- Aplicación práctica para toma de decisiones
- Oportunidad de diferenciación
- Marco normativo relevante
"""
    
    def _resumen_tecnico(self, terminos, nicho, secundarios):
        herramienta = secundarios.get('herramienta', 'N/A')
        contexto = secundarios.get('contexto', 'N/A')
        
        return f"""# Resumen Técnico

## Dominio
{nicho} con {herramienta} como habilitador

## Contexto
{contexto}

## N-gramas Clave
{', '.join(t[0] for t in terminos[:5])}

## Metodología
- Extracción de términos por densidad
- Co-ocurrencias para relaciones
- Jerarquización multicriterio
"""
    
    def _resumen_divulgacion(self, terminos, nicho):
        return f"""# Resumen Divulgativo

## ¿De qué trata?
El contenido explica {nicho} en términos simples.

## Conceptos Clave
{chr(10).join(f'- {t[0]}: {t[1]} menciones' for t in terminos[:5])}

## En Simple
Es como un mapa que te muestra qué conceptos importan más.
"""


if __name__ == '__main__':
    gen = ResumenPorPerfil()
    
    analisis = {
        'nicho': 'AI_SAFETY',
        'secundarios': {'herramienta': 'MACHINE_LEARNING', 'contexto': 'LEGAL'},
        'terminos_clave': [('alignment', 20), ('scaling', 10), ('intelligence', 9)]
    }
    
    for perfil in ['ejecutivo', 'tecnico', 'divulgacion']:
        print(f"\n{'='*50}")
        print(gen.generar(perfil, analisis))
