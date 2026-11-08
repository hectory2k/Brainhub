import subprocess
import json
import textwrap
import sys
import os

DB_PATH = os.environ.get("BRAINHUB_DB", "/sdcard/Download/analisis_consolidado.duckdb")

def run_duckdb(query):
    cmd = ["duckdb", "-json", "-c", query, DB_PATH]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error en DuckDB: {result.stderr}")
        return None
    try:
        stdout = result.stdout.strip()
        if not stdout:
            return []
        if stdout.startswith('['):
            return json.loads(stdout)
        else:
            return [json.loads(line) for line in stdout.split('\n') if line.strip().startswith('{')]
    except json.JSONDecodeError as e:
        print(f"⚠️ Warning parseando JSON: {e}")
        return []

def main():
    print(f"🔍 Conectando a: {DB_PATH}")
    
    query_find = "SELECT chunk_id, video, t_inicio, t_fin, texto FROM chunks WHERE LENGTH(texto) > 2000;"
    chunks_grandes = run_duckdb(query_find)
    
    if not chunks_grandes:
        print("✅ No se encontraron chunks > 2000 caracteres. DB limpia.")
        return 0
        
    print(f"⚠️ Se encontraron {len(chunks_grandes)} chunks > 2000 caracteres. Procesando...")
    
    for chunk in chunks_grandes:
        chunk_id = str(chunk.get('chunk_id', ''))
        video = str(chunk.get('video', ''))
        t_inicio = chunk.get('t_inicio')
        t_fin = chunk.get('t_fin')
        texto = str(chunk.get('texto', ''))
        
        if not chunk_id or not texto:
            continue
            
        bloques = textwrap.wrap(texto, width=1500, break_long_words=True, replace_whitespace=False)
        print(f"  - Subdividiendo '{chunk_id}' ({len(texto)} chars) en {len(bloques)} partes...")
        
        del_query = f"DELETE FROM chunks WHERE chunk_id = '{chunk_id}';"
        run_duckdb(del_query)
        
        for i, bloque in enumerate(bloques):
            new_id = f"{chunk_id}_sub_{i+1}"
            safe_text = bloque.replace("'", "''")
            t_in_val = t_inicio if t_inicio is not None else "NULL"
            t_fin_val = t_fin if t_fin is not None else "NULL"
            
            insert_query = f"INSERT INTO chunks (chunk_id, video, t_inicio, t_fin, texto) VALUES ('{new_id}', '{video}', {t_in_val}, {t_fin_val}, '{safe_text}');"
            run_duckdb(insert_query)
            
    print("✅ Subdivisión completada.")
    
    verify_query = "SELECT COUNT(*) as count FROM chunks WHERE LENGTH(texto) > 2000;"
    remaining = run_duckdb(verify_query)
    count = remaining[0].get('count', 0) if remaining and len(remaining) > 0 else 0
    print(f"🔍 Verificación final: {count} chunks > 2000 caracteres restantes.")
    
    return 0 if count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
