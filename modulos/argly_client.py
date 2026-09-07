#!/data/data/com.termux/files/usr/bin/python3
"""
Cliente ArgLy API para BrainHub.
Consulta datos de IPC y otros indicadores argentinos.
"""

import requests
from typing import Dict, List


class ArgLyClient:
    """Cliente para API ArgLy."""
    
    BASE_URL = 'https://api.argly.com.ar/v1'
    
    def consultar_ipc(self) -> Dict:
        """Consulta IPC actual."""
        try:
            r = requests.get(f'{self.BASE_URL}/ipc', timeout=10)
            return r.json()
        except Exception as e:
            return {'error': str(e)}
    
    def analizar_con_brainhub(self, datos: Dict) -> Dict:
        """Analiza datos de ArgLy con BrainHub."""
        from modulos.detectar_nicho import detectar_nicho
        
        # Convertir datos a texto para análisis
        texto = self._datos_a_texto(datos)
        
        # Detectar nicho
        nicho = detectar_nicho(texto)
        
        return {
            'nicho': nicho,
            'texto_analizado': texto[:200],
            'datos_crudos': datos
        }
    
    def _datos_a_texto(self, datos: Dict) -> str:
        """Convierte datos a texto para NLP."""
        if 'error' in datos:
            return f"Error: {datos['error']}"
        
        # Los datos vienen anidados en 'data'
        datos_planos = datos.get('data', datos)
        
        partes = []
        for clave, valor in datos_planos.items():
            # Convertir clave snake_case a palabras
            clave_legible = clave.replace('_', ' ')
            partes.append(clave_legible)
            
            if isinstance(valor, (int, float)):
                partes.append(str(valor))
            elif isinstance(valor, str):
                partes.append(valor)
        
        return ' '.join(partes)


if __name__ == '__main__':
    cliente = ArgLyClient()
    
    print("🔍 Consultando ArgLy API...")
    datos = cliente.consultar_ipc()
    
    print(f"\n📊 Datos recibidos:")
    print(datos)
    
    print(f"\n🧠 Análisis BrainHub:")
    analisis = cliente.analizar_con_brainhub(datos)
    print(f"   Nicho: {analisis['nicho']}")
