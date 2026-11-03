#!/usr/bin/env python3
import argparse, json, re, sys, urllib.request, urllib.error
from pathlib import Path

DEFAULT_DB = "/sdcard/Download/analisis_consolidado.duckdb"
DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_K = 3
OLLAMA_TIMEOUT_S = 300  # Extendido a 5 minutos para ARM
MAX_CHUNK_CHARS = 800   # Optimización crítica para velocidad en CPU

SYSTEM_PROMPT = """Eres un asistente de preguntas y respuestas sobre documentos técnicos.
Reglas estrictas:
1. Usa SOLO el contexto proporcionado. Si la respuesta no está, di: "No tengo información suficiente en los documentos para responder eso."
2. Cita cada afirmación con [Fuente: <video> @ <timestamp>].
3. Si varios chunks aportan, sintetiza sin repetir.
4. No inventes URLs ni IDs de YouTube.

Contexto:
{context}"""

def formatear_timestamp(t) -> str:
    if t is None: return "?"
    try: t = int(float(t))
    except (ValueError, TypeError): return "?"
    if t < 0: return "?"
    if t < 3600: return f"{t // 60:02d}:{t % 60:02d}"
    else: return f"{t // 3600:02d}:{(t % 3600) // 60:02d}:{t % 60:02d}"

def buscar_chunks(query: str, k: int, db_path: str, video_filter: str = None) -> list:
    query_terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    if not query_terms: return []
    sql = "SELECT chunk_id, video, posicion, t_inicio, t_fin, texto FROM chunks WHERE texto IS NOT NULL AND length(texto) > 20"
    if video_filter:
        sql += f" AND video = '{video_filter.replace(chr(39), chr(39)+chr(39))}'"
    sql += f" LIMIT {k}"
    try:
        import subprocess
        result = subprocess.run(["duckdb", "-json", db_path, "-c", sql], capture_output=True, text=True, check=True, timeout=30)
        chunks = json.loads(result.stdout) if result.stdout.strip() else []
    except Exception: return []
    
    scored = []
    for chunk in chunks:
        texto = (chunk.get("texto") or "").lower()
        score = sum(texto.count(t) for t in query_terms)
        if score > 0: scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]

def formatear_contexto(chunks: list) -> str:
    partes = []
    for i, chunk in enumerate(chunks, 1):
        fuente = chunk.get("video") or "desconocido"
        pos = chunk.get("posicion", "?")
        t_i = formatear_timestamp(chunk.get("t_inicio"))
        t_f = formatear_timestamp(chunk.get("t_fin"))
        # OPTIMIZACIÓN: Truncar texto para acelerar inferencia en ARM
        texto_raw = (chunk.get('texto') or '').strip()
        texto_corto = texto_raw[:MAX_CHUNK_CHARS] + ("..." if len(texto_raw) > MAX_CHUNK_CHARS else "")
        partes.append(f"[Chunk {i}] Fuente: {fuente} | Pos: {pos} | Tiempo: {t_i}→{t_f}\n{texto_corto}")
    return "\n\n".join(partes)

def formatear_cita(chunk: dict) -> str:
    video = chunk.get("video") or "?"
    t_str = formatear_timestamp(chunk.get("t_inicio"))
    m = re.match(r"Transcript_([A-Za-z0-9_-]{11})", video)
    if m: return f"https://youtube.com/watch?v={m.group(1)} @ {t_str}"
    return f"{video} @ {t_str}"

def consultar_ollama(prompt: str, model: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1, 
            "num_predict": 500,
            "num_ctx": 2048  # OPTIMIZACIÓN: Limita ventana de contexto para velocidad en CPU
        }
    }
    
    print("   ⏳ Generando respuesta (streaming optimizado):", flush=True)
    respuesta_completa = []
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_S) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    text = chunk.get("response", "")
                    if text:
                        print(text, end="", flush=True)
                        respuesta_completa.append(text)
                    if chunk.get("done"):
                        break
        print("\n")
        return "".join(respuesta_completa).strip()
        
    except urllib.error.URLError as e:
        print(f"\n❌ Error de conexión con Ollama: {e.reason}")
        return ""
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        return ""

def ciclo_pregunta(pregunta: str, db_path: str, model: str, k: int, video_filter: str = None, verbose: bool = True) -> dict:
    if verbose:
        print(f"\n🔎 Buscando hasta {k} chunks relevantes...")
        if video_filter: print(f"   Filtro: {video_filter}")
    
    chunks = buscar_chunks(pregunta, k, db_path, video_filter)
    if not chunks:
        if verbose: print("⚠️ Sin chunks relevantes. Reformula la pregunta.")
        return {"chunks": [], "respuesta": None, "citas": []}
    
    if verbose:
        print(f"   ✅ {len(chunks)} chunks encontrados")
        print(f"🤖 Consultando {model}...")
    
    contexto = formatear_contexto(chunks)
    prompt = SYSTEM_PROMPT.format(context=contexto) + f"\n\nPregunta: {pregunta}"
    respuesta = consultar_ollama(prompt, model)
    citas = [formatear_cita(c) for c in chunks]
    
    if verbose and respuesta:
        print("\n📚 Fuentes:")
        vistos = set()
        for c in citas:
            if c not in vistos:
                print(f"   - {c}")
                vistos.add(c)
        print()
    return {"chunks": chunks, "respuesta": respuesta, "citas": citas}

def main():
    p = argparse.ArgumentParser(description="BrainHub Q&A interactivo")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--k", type=int, default=DEFAULT_K)
    p.add_argument("--video", help="Filtrar por video")
    p.add_argument("--once", help="Modo no-interactivo: responde una pregunta y sale")
    args = p.parse_args()

    if not Path(args.db).exists():
        print(f"❌ DB no encontrada: {args.db}", file=sys.stderr)
        sys.exit(1)

    print("🧠 BrainHub Q&A Interactivo")
    print(f"   DB: {args.db} | Modelo: {args.model} | Top-K: {args.k}")
    if args.video: print(f"   Filtro video: {args.video}")
    print("   Escribe 'exit' o 'quit' para salir.\n")

    if args.once:
        ciclo_pregunta(args.once, args.db, args.model, args.k, args.video)
        return

    while True:
        try: pregunta = input("📝 Pregunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Adiós."); break
        if not pregunta or pregunta.lower() in {"exit", "quit", "salir"}:
            print("👋 Adiós."); break
        ciclo_pregunta(pregunta, args.db, args.model, args.k, args.video)

if __name__ == "__main__":
    main()
