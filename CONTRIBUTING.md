# Contribuir a BrainHub

¡Gracias por tu interés en BrainHub! Este documento explica cómo aportar.

## Filosofía del proyecto

Antes de contribuir, entendé la filosofía:

> **"El sistema falla antes de fallar."**

BrainHub prioriza **robustez sobre velocidad**. Cada PR debe:
1. **No romper tests existentes** (112 passing)
2. **Agregar tests** para nueva funcionalidad
3. **Respetar las 8 guardias** existentes
4. **Mantener idempotencia** (DELETE antes de INSERT)

## Tipos de contribución

### 🐛 Reportar bugs

**Buen reporte incluye:**
- Descripción del bug
- Comando exacto que lo reproduce
- Output esperado vs output real
- Versión de Python y SO
- (Opcional) Análisis del contenido que falló

### 💡 Sugerir features

**Antes de sugerir:**
1. Verificá que no esté en [ROADMAP.md](ROADMAP.md)
2. Buscá en issues existentes
3. Pensá si respeta la filosofía del proyecto

**Buen feature request:**
- Problema que resuelve
- Propuesta de solución
- Alternativas consideradas

### 📝 Mejorar documentación

**Siempre bienvenido:**
- Typos
- Ejemplos faltantes
- Traducciones (inglés principalmente)
- Tutoriales específicos

### 🔧 Pull Requests

**Antes de empezar:**
1. Creá un issue describiendo el cambio
2. Esperá aprobación (evita trabajo duplicado)
3. Hacé fork del repo
4. Creá una rama descriptiva

**Nombre de rama:**
- `fix/nombre-del-bug`
- `feat/nombre-de-la-feature`
- `docs/nombre-del-doc`

## Setup de desarrollo

### 1. Clonar el repo

```bash
git clone https://github.com/hectory2k/Brainhub.git
cd Brainhub
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Instalar DuckDB CLI

Ver [TUTORIAL.md](TUTORIAL.md#duckdb-cli) para instrucciones por SO.

### 4. Descargar NLTK WordNet

```bash
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### 5. Verificar setup

```bash
# Correr guardias (deben pasar las 8)
bash guardias/startup_completo.sh

# Correr tests (112 passing)
pytest tests/ -q
```

## Estructura del proyecto

```
brainhub/
├── analisis_completo_v6.5.py   # Pipeline principal (activo)
├── api.py                       # API Flask
├── modulos/                     # 47+ módulos
├── brainhub/                    # Módulos nuevos (v7.0)
├── guardias/                    # 8 guardias
├── tests/                       # 112 tests
├── stopwords.json               # Stopwords por nicho
├── terminos_vacios.json         # Términos genéricos
├── terminos_tecnicos.json       # Términos técnicos
└── diccionario_nichos.json      # Nichos
```

## Convenciones de código

### Python

- **Python 3.10+**
- **PEP 8** (líneas < 100 caracteres)
- **Type hints** cuando sea posible
- **Docstrings** en español para funciones públicas

### Bash

- **`set -e`** al inicio de scripts
- **Rutas absolutas** o `$HOME` (no relativas)
- **`echo -e`** para caracteres especiales
- **Comillas dobles** en variables

### Commits

Formato **Conventional Commits:**

```
tipo(scope): descripción corta

Descripción larga opcional.

Refs: #issue
```

**Tipos:**
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` documentación
- `test:` tests
- `chore:` mantenimiento
- `refactor:` refactorización

## Tests

### Antes de cada PR

```bash
# Correr todos los tests
pytest tests/ -q

# Correr guardias
bash guardias/startup_completo.sh
```

### Agregar tests

**Nuevo módulo** → `tests/test_nombre_del_modulo.py`
**Bug fix** → test de regresión
**Feature** → tests unitarios + integración

## Guardias

**Las guardias previenen regresiones.** No las saltees.

### 8 guardias actuales

1. `identidad.sh` — content_id + hash
2. `schema_duckdb.sh` — tablas DB
3. `stopwords.sh` — JSON cargado
4. `diccionarios.sh` — diccionarios
5. `normalizacion.sh` — ñ/Ñ
6. `descolumnado.sh` — integridad
7. `validador.sh` — validador federado
8. `terminos_raw.sh` — duplicados

## Contacto

- **GitHub Issues:** https://github.com/hectory2k/Brainhub/issues
- **Email:** beat006@gmail.com
- **LinkedIn:** [Héctor](https://www.linkedin.com/in/TU_USUARIO)

---

**¿Listo para contribuir?** Abrí un issue o mandá un PR.

**"El sistema falla antes de fallar."** 🏥
