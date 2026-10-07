"""Generación de abstracts con LLM local + fallback a reglas.

Filosofía VigiSalud aplicada a LLM:
- Falla antes de fallar (guardias de RAM y disponibilidad)
- Fallback graceful si algo falla
- Trazabilidad completa (metadata)
"""
import time
from typing import Optional, Tuple, Dict

from brainhub.llm.ollama_client import OllamaClient, hay_ram_suficiente


MODELO_DEFAULT = "brainhub-llama"
RAM_MINIMA_GB = 2.0
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
    # Solo los términos, sin frecuencia (evita confusión del LLM)
    terminos_str = ", ".join(str(t) for t, f in terminos)

    # Conceptos dominantes (si existen)
    conceptos = analisis.get("conceptos", [])[:5]
    conceptos_str = ", ".join(f"{c}" for c, f in conceptos) if conceptos else "(ninguno)"

    # Citas clave (si existen) — dan contexto real del contenido
    # Filtramos citas triviales (<30 chars) para evitar ruido tipo "No," "Sí,"
    todas_citas = analisis.get("citas_clave", [])
    citas_validas = [c for c in todas_citas if len(c.get("texto", "").strip()) >= 30]

    # Abstención: basada en TODAS las citas válidas, no solo en las 2 primeras
    # (evita que gemma:2b invente relaciones a partir de términos aislados,
    #  pero sin descartar videos con muchas citas útiles)
    citas_str_completo = " | ".join(c.get("texto", "") for c in citas_validas)
    if not citas_validas or len(citas_str_completo.strip()) < 80:
        print("  ℹ️  Sin citas suficientes, se omite resumen LLM")
        return {
            "texto": "Tema no claro",
            "modelo": "abstencion",
            "tiempo_seg": 0.0,
            "ram_antes_gb": 0.0,
        }

    # Para el prompt: top 5 citas válidas (evita meter 30+ en num_ctx=512)
    citas_prompt = citas_validas[:5]
    citas_str = " | ".join(c.get("texto", "")[:150] for c in citas_prompt) if citas_prompt else "(sin citas)"

    contexto = (
        f"Archivo: {analisis.get('documento', '?')}\n"
        f"Nicho: {analisis.get('nicho', 'GENERAL')}\n"
        f"Términos clave: {terminos_str}\n"
        f"Conceptos dominantes: {conceptos_str}\n"
        f"Citas del contenido: {citas_str}"
    )

    prompt = (
        "Dados estos datos sobre un documento de texto, generá un abstract "
        "de 3 oraciones en español describiendo el tema.\n\n"
        "REGLAS:\n"
        "- Basate UNICAMENTE en las 'Citas del contenido' y los 'Términos clave'\n"
        "- NO inventes relaciones entre conceptos si no están en las citas\n"
        "- NO menciones: polaridad, segmentos, diálogos, ni números\n"
        "- NO expandas ni traduzcas siglas: conservá exactamente LLM, HDC, RAG, NLP, etc.\n"
        "- NO asumas que es un video: puede ser un paper, artículo o transcripción\n"
        "- Si las citas están vacías o son insuficientes, respondé exactamente: 'Tema no claro'\n"
        "- Mencioná el tema principal y qué enfoque tiene\n\n"
        f"{contexto}\n\n"
        "Abstract:"
    )

    hay_ram, ram_gb, razon_ram = hay_ram_suficiente(RAM_MINIMA_GB)
    if not hay_ram:
        print(f"  ⚠️  Sin RAM para LLM: {razon_ram} (plantilla)")
        return resumen_por_reglas(analisis)

    cliente = OllamaClient(
        model=modelo,
        timeout=TIMEOUT_SEG,
        num_predict=NUM_PREDICT,
    )
    if not cliente.disponible():
        print("  ⚠️  Ollama no disponible (plantilla)")
        return resumen_por_reglas(analisis)

    inicio = time.time()
    try:
        texto_resp = cliente.generar_con_check(prompt)
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
        print(f"  ⚠️  Ollama falló: {e} (plantilla)")
        return resumen_por_reglas(analisis)
    finally:
        try:
            cliente.descargar()
        except Exception:
            pass


def resumen_por_reglas(analisis: dict) -> dict:
    """Fallback: resumen sin LLM usando plantilla."""
    nicho = analisis.get('nicho', 'GENERAL')
    terminos = [t for t, _ in analisis.get('terminos_clave', [])[:5]]
    polaridad = analisis.get('sentimiento_global', {}).get('polaridad', 0)
    tono = "positivo" if polaridad > 0.1 else "negativo" if polaridad < -0.1 else "neutro"
    texto = (
        f"El documento analiza temas de {nicho.lower()}, "
        f"con foco en {', '.join(terminos)}. "
        f"El tono general es {tono} (polaridad {polaridad:.2f})."
    )
    return {
        "texto": texto,
        "modelo": "plantilla",
        "tiempo_seg": 0.0,
        "ram_antes_gb": 0.0,
    }


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
