#!/data/data/com.termux/files/usr/bin/python3
"""Extractor simple .tex → .txt (sin comandos LaTeX)."""

import re
import sys

def tex_a_texto(archivo_tex, archivo_salida=None):
    with open(archivo_tex, 'r') as f:
        tex = f.read()
    
    # Quitar comandos
    texto = re.sub(r'\\[a-zA-Z]+', ' ', tex)
    # Quitar símbolos LaTeX
    texto = re.sub(r'[{}[\]$^_&#%]', ' ', texto)
    # Limpiar espacios
    texto = re.sub(r'\s+', ' ', texto)
    
    if archivo_salida is None:
        archivo_salida = archivo_tex.replace('.tex', '.txt')
    
    with open(archivo_salida, 'w') as f:
        f.write(texto)
    
    return archivo_salida

if __name__ == '__main__':
    archivo = sys.argv[1] if len(sys.argv) > 1 else 'acl_latex.tex'
    salida = tex_a_texto(archivo)
    print(f"✅ {salida}")
