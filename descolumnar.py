import re

def procesar_columnas(archivo_entrada, archivo_salida, ancho_columna=48):
    with open(archivo_entrada, 'r', encoding='utf-8', errors='ignore') as f:
        lineas = f.readlines()

    col_izquierda = []
    col_derecha = []

    for linea in lineas:
        izq = linea[:ancho_columna].rstrip()
        der = linea[ancho_columna:].strip()

        if izq:
            col_izquierda.append(izq)
        if der:
            col_derecha.append(der)

    texto_final = "=== COLUMNA IZQUIERDA ===\n\n"
    texto_final += "\n".join(col_izquierda)
    texto_final += "\n\n=== COLUMNA DERECHA ===\n\n"
    texto_final += "\n".join(col_derecha)

    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(texto_final)

    print(f"✅ Archivo guardado: {archivo_salida}")

if __name__ == "__main__":
    import sys
    archivo_entrada = sys.argv[1] if len(sys.argv) > 1 else 'salida.txt'
    archivo_salida = sys.argv[2] if len(sys.argv) > 2 else archivo_entrada.replace('.txt', '_continuo.txt')
    procesar_columnas(archivo_entrada, archivo_salida)
