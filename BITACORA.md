# Bitácora de BrainHub

Registro cronológico de bugs, fixes, descubrimientos y lecciones.

> **Filosofía:** El contenido real revela lo que los tests no ven.

---

## 2026-09-15 — Video industrial revela 5 bugs

### Contexto

Procesé un video de ciberseguridad industrial:
- **Transcript:** ME_lJOHAPUo_ES
- **Tamaño:** 453,628 caracteres (8.7x más grande que el de Kubernetes)
- **Segmentos:** 1,829
- **Tiempo de análisis:** 1.7s

### Bugs descubiertos

#### 1. HABLA incompleto

- **Síntoma:** `cierto: 512` y `muchas: 124` como términos top
- **Causa:** muletillas no estaban en `stopwords.json`
- **Fix:** +20 términos al nicho HABLA

#### 2. Scoring por presencia (no frecuencia)

- **Síntoma:** `malware (18x)` pesaba igual que `bitcoin (1x)`
- **Causa:** `score += 1` por keyword (0/1, sin frecuencia)
- **Fix:** `score += min(matches, 5)`
- **Impacto:** CIBERSEGURIDAD pasó de 18 a 140 puntos

#### 3. CIBERSEGURIDAD desbalanceada

- **Síntoma:** Solo 9 términos, sin `ciberseguridad`, `industrial`, `planta`
- **Fix:** ampliada a 34 términos (scada, ics, ot, ransomware, ...)

#### 4. FINANZAS con falsos positivos

- **Síntoma:** `banco` matcheaba en "banco de batería"
- **Síntoma:** `mercado` matcheaba en "mercado de herramientas"
- **Síntoma:** `precios` matcheaba en cualquier contexto
- **Fix:** quitados los 3 términos ambiguos

#### 5. AI_SAFETY retorno temprano

- **Síntoma:** CIBERSEGURIDAD=140 perdía contra AI_SAFETY=6
- **Causa:** `if scores['AI_SAFETY'] >= 3: return 'AI_SAFETY'`
- **Historia:** este bug ya se había arreglado el 2026-09-10 para el video de Kubernetes, pero volvió al recuperar el validador desde git (commit 2dfb79c)
- **Fix:** eliminado el retorno temprano + test de regresión

### Resultado

| Métrica | Antes | Después |
|---------|-------|---------|
| Nicho industrial | TECNOLOGIA | **CIBERSEGURIDAD** ✅ |
| SQLite re-análisis | UNIQUE constraint | ✅ OK |
| Tests | 112 | **116** (+4 regresión) |
| Términos top | cierto, muchas | ciberseguridad, planta, industrial |

### Lección

> Sin test de regresión, los fixes no son permanentes.
>
> El retorno temprano de AI_SAFETY había vuelto al recuperar el validador desde git (commit 2dfb79c), sin que nadie lo notara. Solo lo detectamos con un video industrial real.
>
> **Por eso:** `tests/test_nicho_regresion.py` previene regresión.

### Commits

- `f582bc5` — fix(nicho): scoring ponderado + SQLite idempotente + AI_SAFETY

---

## 2026-09-14 — Limpieza + Documentación + Ollama

### Logros

- ✅ 29 symlinks (scripts unificados en `~/proyectos/nlp/scripts/`)
- ✅ `duckdb/` borrado (3.8 GB recuperados)
- ✅ README v7.0.0 completo (11 secciones)
- ✅ TUTORIAL.md (2 flujos: YouTube + Papers)
- ✅ ROADMAP.md público
- ✅ CONTRIBUTING.md
- ✅ Cross-promo: VigiSalud + Argentina Hub + denoise
- ✅ Ollama verificado: 4 modelos (phi3:mini, llama3.2:3b, gemma:2b, tinyllama)

### Decisión

No integrar Ollama todavía — esperar sesión dedicada.

---

## 2026-09-13 — Networking + Demo

### Logros

- ✅ Alianza con Cristian Rojas (autor de denoise)
- ✅ Contacto con Dardo Valdez (MCP + RAG + 20 PDFs)
- ✅ Video asciinema grabado y online
- ✅ Demo reproducible (`demo.sh`)
- ✅ README con Autor + LinkedIn

### Contexto

Compartí BrainHub en el grupo de Cristian. Respondió con estrella en GitHub y me pidió un tutorial corto. Grabé video con `asciinema`.

### Links

- Video: https://asciinema.org/a/EqWi4xkuVw3Bvsp0
- Repo: https://github.com/hectory2k/Brainhub

---

## 2026-09-11 — Fix ñ + Guardias + Validador federado

### Bugs resueltos

| # | Bug | Fix |
|---|-----|-----|
| 1 | `años` → `anos` en 3 lugares | `normalizar_preservando_enie()` |
| 2 | `TECNOLOGIA` cuando era `FINANZAS` | Regex `\b` + `PRIORIDAD_NICHO` |
| 3 | `word`/`paper` en preguntas | Validador federado |

### Logros

- ✅ 6 guardias orquestadas (2 nuevas + 2 refactor)
- ✅ Validador federado (5 fuentes de conocimiento)
- ✅ 112 tests (antes 60)
- ✅ Fixture de regresión en `tests/fixtures/regresion_economia/`

### Lección

> Un output bugueado es oro.
>
> El fixture de `informe_deudores` capturó 3 bugs que se fueron arreglando en 2 días.

---

## Cómo usar esta bitácora

**Buscar bugs por nombre:**
```bash
grep -i "AI_SAFETY" BITACORA.md
grep -i "scoring" BITACORA.md
```

**Ver qué pasó un día:**
```bash
grep -A 20 "## 2026-09-15" BITACORA.md
```

**Ver todos los bugs resueltos:**
```bash
grep -E "^### Bug|^#### [0-9]" BITACORA.md
```

---

**Filosofía:** Documentar el "por qué", no solo el "qué".
