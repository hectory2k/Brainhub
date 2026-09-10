"""descolumnar.py - Descolumnado con validación de integridad.

Uso:
    python3 descolumnar.py archivo.txt [salida.txt]
    python3 descolumnar.py archivo.txt --ancho 48
    python3 descolumnar.py archivo.txt --test  # solo valida, no escribe
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ResultadoDescolumnado:
    lineas_totales: int
    lineas_izq: int
    lineas_der: int
    lineas_vacias: int
    lineas_cortadas: int
    ancho_usado: int
    
    @property
    def ratio(self) -> float:
        return self.lineas_izq / max(self.lineas_der, 1)
    
    @property
    def tasa_corte(self) -> float:
        return self.lineas_cortadas / max(self.lineas_totales, 1)
    
    def es_valido(self) -> tuple:
        """Retorna (valido, razon)"""
        if self.lineas_izq < 10:
            return False, f"Pocas líneas izquierda: {self.lineas_izq}"
        if self.lineas_der < 10:
            return False, f"Pocas líneas derecha: {self.lineas_der}"
        if not (0.3 <= self.ratio <= 3.0):
            return False, f"Ratio izq/der desbalanceado: {self.ratio:.2f}"
        if self.tasa_corte > 0.4:
            return False, f"Demasiadas líneas cortadas: {self.tasa_corte:.1%}"
        return True, "OK"


def detectar_ancho_columna(lineas: list, ancho_default: int = 48) -> int:
    """Detecta el ancho de columna por frecuencia de espacios."""
    candidatos = {}
    for linea in lineas[:500]:
        for match in re.finditer(r"\s{3,}", linea):
            pos = match.start()
            if 30 <= pos <= 80:
                candidatos[pos] = candidatos.get(pos, 0) + 1
    if not candidatos:
        return ancho_default
    return max(candidatos, key=candidatos.get)


def procesar_columnas(archivo_entrada: str, archivo_salida: str = None,
                       ancho_columna: int = None, solo_validar: bool = False) -> ResultadoDescolumnado:
    """Descolumnar con validación de integridad."""
    with open(archivo_entrada, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()
    
    if ancho_columna is None:
        ancho_columna = detectar_ancho_columna(lineas)
        print(f"📏 Ancho detectado: {ancho_columna}")
    
    col_izquierda = []
    col_derecha = []
    lineas_vacias = 0
    lineas_cortadas = 0
    
    for linea in lineas:
        izq = linea[:ancho_columna].rstrip()
        der = linea[ancho_columna:].strip()
        
        if not izq and not der:
            lineas_vacias += 1
            continue
        
        # Detectar corte sospechoso: palabra cortada a mitad
        if izq and der and not izq.endswith((".", ",", ";", ":", ")", "]", "?", "!", "-")):
            if der and der[0].islower():
                lineas_cortadas += 1
        
        if izq:
            col_izquierda.append(izq)
        if der:
            col_derecha.append(der)
    
    resultado = ResultadoDescolumnado(
        lineas_totales=len(lineas),
        lineas_izq=len(col_izquierda),
        lineas_der=len(col_derecha),
        lineas_vacias=lineas_vacias,
        lineas_cortadas=lineas_cortadas,
        ancho_usado=ancho_columna,
    )
    
    if archivo_salida and not solo_validar:
        texto_final = "=== COLUMNA IZQUIERDA ===\n\n"
        texto_final += "\n".join(col_izquierda)
        texto_final += "\n\n=== COLUMNA DERECHA ===\n\n"
        texto_final += "\n".join(col_derecha)
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(texto_final)
        print(f"✅ Guardado: {archivo_salida}")
    
    print(f"   📊 Izq: {resultado.lineas_izq} | Der: {resultado.lineas_der} "
          f"| Vacías: {resultado.lineas_vacias} | Cortes: {resultado.lineas_cortadas}")
    
    return resultado


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: descolumnar.py archivo.txt [salida.txt] [--ancho N] [--test]")
        sys.exit(1)
    
    archivo_entrada = sys.argv[1]
    archivo_salida = None
    ancho = None
    solo_validar = "--test" in sys.argv
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--ancho" and i + 1 < len(sys.argv):
            ancho = int(sys.argv[i + 1])
        elif arg == "--test":
            continue
        elif not arg.startswith("--") and archivo_salida is None:
            archivo_salida = arg
    
    if archivo_salida is None and not solo_validar:
        archivo_salida = archivo_entrada.replace(".txt", "_continuo.txt")
    
    resultado = procesar_columnas(archivo_entrada, archivo_salida, ancho, solo_validar)
    
    valido, razon = resultado.es_valido()
    if not valido:
        print(f"🚨 GUARDIA DE DESCOLUMNADO FALLÓ: {razon}")
        print(f"   Probá con --ancho N (actual: {resultado.ancho_usado})")
        sys.exit(1)
    
    print("✅ Descolumnado válido")


if __name__ == "__main__":
    main()
