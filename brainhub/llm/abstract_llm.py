"""Generación de abstracts con LLM local + fallback a reglas.

Filosofía VigiSalud aplicada a LLM:
- Falla antes de fallar (guardias de RAM y disponibilidad)
- Fallback graceful si algo falla
- Trazabilidad completa (metadata)
"""
import time
from typing import Optional, Tuple, Dict

from brainhub.llm.ollama_client import OllamaClient, hay_ram_suficiente


MODELO_DEFAULT = "gemma:2b"
RAM_MINIMA_GB = 3.0
TIMEOUT_SEG = 180
NUM_PREDICT = 200


def generar_abstract_llm(
    texto: str,
    usar_llm: bool = True,
    modelo: str = MODELO_DEFAULT,
    forzar: bool = False,
) -> Tuple[Optional[str], Dict]:
    """Genera abstract con LLM + fallback.
    
    Aplica guardias antes de intentar:
    1. ¿usar_llm activado?
    2. ¿RAM suficiente?
    3. ¿Ollama disponible?
    
    Returns:
        (abstract: str | None, metadata: dict)
    """
    metadata = {
        "usado_llm": False,
        "razon_fallback": None,
        "tiempo_seg": 0.0,
        "modelo": None,
        "ram_antes_gb": 0.0,
        "ram_despues_gb": 0.0,
    }
    
    inicio = time.time()
    
    # GUARDIA 1: ¿usar_llm activado?
    if not usar_llm:
        metadata["razon_fallback"] = "llm_desactivado"
        metadata["tiempo_seg"] = time.time() - inicio
        return None, metadata
    
    # GUARDIA 2: ¿RAM suficiente?
    hay_ram, ram_gb, razon_ram = hay_ram_suficiente(RAM_MINIMA_GB)
    metadata["ram_antes_gb"] = ram_gb
    
    if not hay_ram and not forzar:
        metadata["razon_fallback"] = f"sin_ram: {razon_ram}"
        metadata["tiempo_seg"] = time.time() - inicio
        return None, metadata
    
    # GUARDIA 3: ¿Ollama disponible?
    cliente = OllamaClient(model=modelo, timeout=TIMEOUT_SEG, num_predict=NUM_PREDICT)
    
    if not cliente.disponible():
        metadata["razon_fallback"] = "ollama_no_disponible"
        metadata["tiempo_seg"] = time.time() - inicio
        return None, metadata
    
    # INTENTO: generar con LLM
    try:
        abstract = cliente.resumir(texto, max_oraciones=5)
        
        if not abstract or abstract.startswith("Error"):
            metadata["razon_fallback"] = f"respuesta_invalida: {abstract[:50]}"
            metadata["tiempo_seg"] = time.time() - inicio
            return None, metadata
        
        metadata["usado_llm"] = True
        metadata["modelo"] = modelo
        metadata["tiempo_seg"] = time.time() - inicio
        return abstract, metadata
    
    except Exception as e:
        metadata["razon_fallback"] = f"excepcion: {type(e).__name__}: {e}"
        metadata["tiempo_seg"] = time.time() - inicio
        return None, metadata
    
    finally:
        # LIMPIEZA: liberar RAM SIEMPRE
        try:
            cliente.descargar()
            _, ram_despues, _ = hay_ram_suficiente(0)
            metadata["ram_despues_gb"] = ram_despues
        except Exception:
            pass


if __name__ == "__main__":
    texto = "Kubernetes es un orquestador de contenedores que permite desplegar, escalar y gestionar aplicaciones en clusters de servidores. Facilita la administracion de microservicios en produccion."
    
    print("=== Test con LLM ===")
    abstract, meta = generar_abstract_llm(texto, usar_llm=True)
    
    if abstract:
        print(f"OK Abstract ({meta['tiempo_seg']:.1f}s):")
        print(f"   {abstract}")
    else:
        print(f"Fallback: {meta['razon_fallback']}")
    
    print(f"\nMetadata:")
    for k, v in meta.items():
        print(f"  {k}: {v}")
