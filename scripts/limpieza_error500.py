import re
from pathlib import Path
import shutil

# Archivos confirmados con contaminación
archivos = [
    "/sdcard/Download/Transcript_ONrw_JAOHvo_cs_original_es.txt",
    "/sdcard/Download/Transcript_ONrw_JAOHvo_cs_original_en.txt"
]

# Firma exacta del error (el \s* captura el espacio extra antes del texto real)
firma_error = r"Error 500 \(Server Error\)!!1500\.That’s an error\.There was an error\. Please try again later\.That’s all we know\.?\s*"

for ruta in archivos:
    p = Path(ruta)
    assert p.exists(), f"CRÍTICO: No existe {ruta}"
    
    # 1. Backup obligatorio
    backup = p.with_suffix(p.suffix + ".PRE_LIMPIEZA_500")
    if not backup.exists():
        shutil.copy2(p, backup)
        print(f"✅ Backup creado: {backup.name}")
    
    src = p.read_text(encoding="utf-8")
    
    # 2. Assert de presencia: debe tener al menos 1 ocurrencia
    n_antes = len(re.findall(firma_error, src))
    assert n_antes > 0, f"ALERTA: No se encontró la firma de error en {p.name}. ¿Ya estaba limpio?"
    
    # 3. Limpieza
    src_limpio = re.sub(firma_error, "", src)
    
    # 4. Assert de eliminación: no debe quedar rastro
    n_despues = len(re.findall(firma_error, src_limpio))
    assert n_despues == 0, f"FALLO: La limpieza no fue total en {p.name}"
    
    # 5. Escritura segura
    p.write_text(src_limpio, encoding="utf-8")
    print(f"🧹 OK: {n_antes} ocurrencia(s) eliminada(s) de {p.name}")

print("\n🎉 Limpieza completada. Listo para reprocesar.")
