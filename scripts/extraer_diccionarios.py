#!/data/data/com.termux/files/usr/bin/python3
"""
Extrae términos de los diccionarios del proyecto a CSVs
para cargarlos en v_terminos_tecnicos vía DuckDB.

Formatos soportados:
- diccionario_clinico.json: {concepto: {sinonimos: [...], categoria, alias_mesh}}
- diccionario_nichos.json:  {NICHO: {terminos: [...]}}
- terminos_tecnicos.json:   {es: [...], en: [...]}
- terminos_vacios.json:     {es: [...], en: [...]}
- stopwords.json:           {base: {es, en}, nichos: {NICHO: {es, en}}}
- detectar_nicho.py:        NICHO_KEYWORDS = {NICHO: [...]}
"""
import json
import sys
from pathlib import Path

RAIZ = Path.home() / "proyectos/nlp"
OUT = RAIZ / "data" / "diccionarios"
OUT.mkdir(parents=True, exist_ok=True)


def guardar(nombre: str, terminos: set):
    """Guarda un set de términos en un CSV (uno por línea)."""
    terminos = {t.lower().strip() for t in terminos if t and str(t).strip()}
    if not terminos:
        print(f"⚠️  {nombre}: 0 términos")
        return
    out = OUT / f"{nombre}.csv"
    with open(out, "w", encoding="utf-8") as f:
        for t in sorted(terminos):
            f.write(f"{t}\n")
    print(f"✅ {nombre}.csv: {len(terminos)} términos")


# ─── 1. diccionario_clinico.json ───
p = RAIZ / "diccionario_clinico.json"
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    terms = set()
    for concepto, info in data.items():
        terms.add(concepto)
        terms.update(info.get("sinonimos", []))
        # alias_mesh es en inglés, útil también
        if info.get("alias_mesh"):
            terms.add(info["alias_mesh"])
    guardar("clinico", terms)
else:
    print(f"⚠️  No existe: {p}")


# ─── 2. diccionario_nichos.json ───
p = RAIZ / "diccionario_nichos.json"
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    terms = set()
    for nicho, info in data.items():
        if isinstance(info, dict):
            terms.update(info.get("terminos", []))
            terms.update(info.get("keywords", []))
            for lang in ("es", "en"):
                terms.update(info.get(lang, []))
        elif isinstance(info, list):
            terms.update(info)
    guardar("nichos", terms)
else:
    print(f"⚠️  No existe: {p}")


# ─── 3. terminos_tecnicos.json ───
p = RAIZ / "terminos_tecnicos.json"
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    terms = set()
    for lang in ("es", "en"):
        terms.update(data.get(lang, []))
    guardar("tecnicos", terms)
else:
    print(f"⚠️  No existe: {p}")


# ─── 4. NICHO_KEYWORDS de detectar_nicho.py ───
try:
    sys.path.insert(0, str(RAIZ))
    from modulos.detectar_nicho import NICHO_KEYWORDS
    terms = set()
    for nicho, kws in NICHO_KEYWORDS.items():
        terms.update(kws)
    guardar("nicho_keywords", terms)
except Exception as e:
    print(f"⚠️  NICHO_KEYWORDS: {e}")


# ─── 5. terminos_vacios.json ───
p = RAIZ / "terminos_vacios.json"
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    terms = set()
    for lang in ("es", "en"):
        terms.update(data.get(lang, []))
    guardar("vacios", terms)


# ─── 6. stopwords.json (para auditoría) ───
p = RAIZ / "stopwords.json"
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    terms = set()
    for lang in ("es", "en"):
        terms.update(data.get("base", {}).get(lang, []))
    for nicho in data.get("nichos", {}).values():
        for lang in ("es", "en"):
            terms.update(nicho.get(lang, []))
    guardar("stopwords_full", terms)


# ─── Resumen ───
print()
print(f"📂 CSVs en: {OUT}")
total = 0
for f in sorted(OUT.glob("*.csv")):
    n = len(f.read_text(encoding="utf-8").strip().split("\n"))
    total += n
    print(f"  {f.name}: {n}")
print(f"  ─────")
print(f"  Total (con duplicados entre fuentes): {total}")
