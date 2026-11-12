#!/usr/bin/env python3
"""
Inyecta el array 'chunks' en JSONs legacy que lo tienen como None o vacío.
Usa el chunker actual para evitar re-ejecutar el LLM.
"""
import json
import sys
from pathlib import Path
import subprocess

# Agregar ruta del proyecto para importar el chunker
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brainhub.chunking import Chunker

DISK_DIR = Path("/sdcard/Download")
HUERFANOS_FILE = Path.home() / "temp" / "jsons_huerfanos.txt"

if not HUERFANOS_FILE.exists():
    print("❌ No se encontró la lista de huérfanos. Ejecuta primero el diagnóstico.")
    sys.exit(1)

with open(HUERFANOS_FILE, 'r', encoding='utf-8') as f:
    huérfanos = [line.strip() for line in f if line.strip()]

print(f"📊 Procesando {len(huérfanos)} JSONs legacy...")

chunker = Chunker(estrategia='oraciones', max_oraciones=10)
exitosos = 0
fallidos = 0

for json_name in huérfanos:
    json_path = DISK_DIR / json_name
    
    # Inferir nombre del archivo .txt fuente (quitando '_analisis_completo.json')
    base_name = json_name.replace("_analisis_completo.json", "")
    txt_path = DISK_DIR / f"{base_name}.txt"
    
    if not txt_path.exists():
        print(f"  ⚠️ SKIP: No se encontró fuente {txt_path.name}")
        fallidos += 1
        continue
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Si ya tiene chunks válidos, saltar
        if data.get('chunks') and len(data.get('chunks', [])) > 0:
            print(f"  ✅ SKIP: {json_name} ya tiene chunks.")
            exitosos += 1
            continue
            
        # Leer texto y chunkear
        with open(txt_path, 'r', encoding='utf-8') as f:
            texto = f.read()
            
        chunks_objs = chunker.chunkear(texto, base_name)
        data['chunks'] = [c.a_dict() for c in chunks_objs]
        
        # Guardar JSON actualizado
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"  ✅ INYECTADO: {json_name} ({len(chunks_objs)} chunks)")
        exitosos += 1
        
    except Exception as e:
        print(f"  ❌ ERROR en {json_name}: {e}")
        fallidos += 1

print(f"\n🎉 Finalizado. Exitosos: {exitosos}, Fallidos/Skip: {fallidos}")
print("👉 Próximo paso: Ejecutar `python3 scripts/persistir_chunks.py` para subirlos a la DB.")
