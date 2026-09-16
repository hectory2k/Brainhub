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
RAM_MINIMA_GB = 2.5
TIMEOUT_SEG = 180
NUM_PREDICT = 80


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


def generar_resumen_desde_analisis(
    analisis: dict,
    modelo: str = MODELO_DEFAULT,
    usar_llm: bool = True,
) -> Optional[Dict]:
    """
    Genera resumen LLM usando contexto COMPACTO (~300 tokens).
    Aplica guardias de RAM y disponibilidad.

    Returns:
        dict con texto, modelo, tiempo_seg, ram_antes_gb, o None si falla
    """
    if not usar_llm:
        return None

    terminos = analisis.get("terminos_clave", [])[:10]
    terminos_str = ", ".join(f"{t}({f})" for t, f in terminos)
    sent = analisis.get("sentimiento_global", {})
    polaridad = sent.get("polaridad", 0)

    contexto = (
        f"Documento: {analisis.get('documento', '?')}\n"
        f"Nicho: {analisis.get('nicho', 'GENERAL')}\n"
        f"Segmentos: {analisis.get('total_segmentos', 0)}\n"
        f"Dialogos: {analisis.get('total_dialogos', 0)}\n"
        f"Polaridad: {polaridad:.2f}\n"
        f"Top terminos: {terminos_str}"
    )

    prompt = (
        "Genera un abstract de 3 oraciones en espanol. "
        "Debe describir el tema principal, el enfoque y el tono. "
        "NO inventes datos. Solo interpreta lo que ves.\n\n"
        f"{contexto}\n\n"
        "Abstract:"
    )

    hay_ram, ram_gb, razon_ram = hay_ram_suficiente(RAM_MINIMA_GB)
    if not hay_ram:
        print(f"  ⚠️  Sin RAM para LLM: {razon_ram}")
        return None

    cliente = OllamaClient(
        model=modelo,
        timeout=TIMEOUT_SEG,
        num_predict=NUM_PREDICT,
    )
    if not cliente.disponible():
        print("  ⚠️  Ollama no disponible")
        return None

    inicio = time.time()
    try:
        texto_resp = cliente.generar(prompt)
        tiempo = time.time() - inicio
        if not texto_resp or len(texto_resp.strip()) < 20:
            return None
        return {
            "texto": texto_resp.strip(),
            "modelo": modelo,
            "tiempo_seg": round(tiempo, 2),
            "ram_antes_gb": round(ram_gb, 2),
        }
    except Exception as e:
        print(f"  ⚠️  Ollama falló: {e}")
        return None
    finally:
        try:
            cliente.descargar()
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
