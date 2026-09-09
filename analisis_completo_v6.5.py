#!/usr/bin/env python3
"""
Análisis completo de documentales/entrevistas V6.4
- Elimina stopwords hardcodeadas
- Usa exclusivamente JSON para stopwords
- Fallback a set vacío si no hay JSON
Uso: python3 analisis_completo_v6.4.py archivo_transcripcion.txt
"""

import sys
import os
import re
import json
import sqlite3
import csv
from collections import Counter, defaultdict
from textblob import TextBlob

sys.path.insert(0, os.path.expanduser('~/proyectos/nlp'))

# Importar módulos
try:
    from modulos.detector_hablantes import DetectorHablantes
except ImportError:
    DetectorHablantes = None

try:
    from modulos.detectar_nicho import detectar_nicho
except ImportError:
    def detectar_nicho(texto):
        return 'GENERAL'

try:
    from modulos.generar_abstract import GeneradorAbstract
except ImportError:
    GeneradorAbstract = None

try:
    from modulos.metricas import MetricasPipeline
except ImportError:
    MetricasPipeline = None

try:
    from modulos.stopwords_manager import get_stopwords
except ImportError:
    def get_stopwords(nicho='GENERAL', lang='es'):
        return set()

# ========================================================================
# CONCEPTOS POR NICHO
# ========================================================================

CONCEPTOS_POR_NICHO = {
    'LEGAL': {
        "AUTORIDAD_JUDICIAL": [
            "judge", "court", "court order", "hearing", "civil law",
            "article 206", "custody", "legal", "law", "tribunal", "juez"
        ],
        "DENUNCIA": [
            "police", "police station", "complaint", "prosecutor",
            "file a complaint", "criminal", "fiscal", "denuncia"
        ],
        "CONFLICTO_FAMILIAR": [
            "mother", "father", "children", "daughter", "son", "parents",
            "custody", "visitation", "contact"
        ],
        "VIOLENCIA_PSICOLOGICA": [
            "psychological violence", "violence", "hatred", "harm",
            "sad", "afraid", "unpleasant", "trauma", "abuse", "manipulation"
        ]
    },
    'SALUD': {
        "LESION_DEPORTIVA": [
            "ligamento", "cruzado", "rodilla", "lesion", "anterior",
            "menisco", "tendon", "musculo", "fractura", "esguince",
            "ligament", "knee", "injury", "acl", "meniscus"
        ],
        "TRATAMIENTO_MEDICO": [
            "cirugia", "operacion", "rehabilitacion", "fisioterapia",
            "dolor", "inflamacion", "recuperacion", "surgery",
            "recovery", "physical therapy", "pain", "inflammation"
        ],
        "DIAGNOSTICO": [
            "diagnostico", "resonancia", "radiografia", "examen",
            "prueba", "diagnosis", "mri", "x-ray", "scan", "test"
        ],
        "IMPACTO_FUNCIONAL": [
            "caminar", "correr", "mover", "funcion", "movilidad",
            "walk", "run", "move", "function", "mobility"
        ],
        "INTERVENCION_QUIRURGICA": [
            "operar", "cirujano", "anestesia", "incision", "postoperatorio",
            "surgeon", "anesthesia", "incision", "postoperative"
        ]
    },
    'CIBERSEGURIDAD': {
        "AMENAZAS": [
            "malware", "phishing", "ransomware", "virus", "trojan",
            "attack", "breach", "exploit", "amenaza", "ataque"
        ],
        "DEFENSAS": [
            "firewall", "antivirus", "encryption", "security", "protection",
            "seguridad", "proteccion", "defensa", "backup"
        ],
        "VULNERABILIDADES": [
            "vulnerability", "weakness", "flaw", "bug", "exploit",
            "vulnerabilidad", "debilidad", "falla", "error"
        ],
        "ACCESO_NO_AUTORIZADO": [
            "hack", "unauthorized access", "breach", "intrusion",
            "hackeo", "acceso no autorizado", "intrusion", "brecha"
        ],
        "PROTECCION_DATOS": [
            "encryption", "privacy", "data protection", "gdpr",
            "encriptacion", "privacidad", "proteccion de datos"
        ]
    },
    'TECNOLOGIA': {
        "DESARROLLO_SOFTWARE": [
            "software", "programming", "code", "developer", "api",
            "database", "server", "cloud", "devops", "git"
        ],
        "DATA_SCIENCE": [
            "machine learning", "ai", "data science", "analytics",
            "python", "pandas", "scikit-learn", "model", "training"
        ]
    },
    'FINANZAS': {
        "MERCADOS": [
            "stock", "market", "trading", "investment", "portfolio",
            "accion", "mercado", "inversion", "portafolio", "bolsa"
        ],
        "CRIPTO": [
            "bitcoin", "cryptocurrency", "crypto", "blockchain",
            "ethereum", "defi", "nft", "wallet", "exchange"
        ]
    },
    'GENERAL': {
        "TESTIMONIO_PERSONAL": [
            "i remember", "i felt", "my experience", "when i",
            "yo recuerdo", "yo sentí", "mi experiencia", "cuando yo"
        ],
        "OPINION_PROFESIONAL": [
            "in my opinion", "i believe", "according to", "the evidence",
            "en mi opinión", "yo creo", "de acuerdo a", "la evidencia"
        ]
    }
}

# ========================================================================
# FUNCIONES DE ANÁLISIS
# ========================================================================

def limpiar_texto(texto):
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = re.sub(r'&[a-z]+;', '', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

def es_segmento_valido(segmento):
    limpio = re.sub(r'[^\w\s]', '', segmento).strip()
    if len(limpio) < 10:
        return False
    if re.match(r'^[\.\s]+$', limpio):
        return False
    return True

def filtrar_stopwords(texto, nicho='GENERAL'):
    """Filtra stopwords usando exclusivamente JSON (sin hardcode)."""
    texto_norm = texto.lower()
    texto_norm = re.sub(r'[áàäâ]', 'a', texto_norm)
    texto_norm = re.sub(r'[éèëê]', 'e', texto_norm)
    texto_norm = re.sub(r'[íìïî]', 'i', texto_norm)
    texto_norm = re.sub(r'[óòöô]', 'o', texto_norm)
    texto_norm = re.sub(r'[úùüû]', 'u', texto_norm)
    texto_norm = re.sub(r'ñ', 'n', texto_norm)
    
    palabras = re.findall(r'\b[a-z]{3,}\b', texto_norm)
    
    # Detectar idioma
    ingles = sum(1 for p in palabras if p in {'the', 'this', 'that', 'with', 'from', 'have', 'will', 'your'})
    espanol = sum(1 for p in palabras if p in {'que', 'para', 'por', 'con', 'sin', 'sobre', 'entre'})
    lang = 'en' if ingles > espanol else 'es'
    
    # Obtener stopwords exclusivamente desde JSON
    try:
        stopwords = set()
        for idioma in ['es', 'en', 'cs']:
            sw = get_stopwords(nicho, idioma)
            if sw:
                stopwords.update(sw)
    except:
        stopwords = set()
    
    # Si no hay stopwords en JSON, usar set vacío (sin fallback hardcodeado)
    # Esto obliga a mantener el JSON actualizado
    
    filtradas = [p for p in palabras if p not in stopwords]
    
    return filtradas

def extraer_nombres_propios(texto):
    nombres = {}
    patron = r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)\b'
    for match in re.findall(patron, texto):
        if len(match) > 3:
            palabras = match.split()
            if not any(p.lower() in {'the','this','that','with','from','have','will','your'} for p in palabras):
                nombres[match] = 'PERSONA'
    return nombres

    frases_nino = [
        'daddy you are so nice', 'thank you for being my daddy',
        'i want to go with daddy', 'say hi to your daddy',
        'i wanna go with daddy'
    ]
    if any(f in combinado for f in frases_nino):
        return 'NIÑO/A'

    if 'family psychologist' in combinado or 'psychologist' in combinado:
        return 'PSICÓLOGO/A'
    if 'attorney' in combinado or 'lawyer' in combinado:
        return 'ABOGADO/A'
    if 'judge' in combinado or 'court order' in combinado:
        return 'JUEZ / AUTORIDAD'
    if 'police station' in combinado or 'prosecutor' in combinado:
        return 'POLICÍA / FISCAL'

    if 'my mother' in combinado or 'my mum' in combinado:
        return 'TESTIGO (HIJO/A)'
    if 'my father' in combinado or 'my dad' in combinado:
        return 'TESTIGO (HIJO/A)'

    return 'DESCONOCIDO'

def segmentar_por_oraciones(texto, max_caracteres=300):
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    segmentos = []
    actual = ""

    for oracion in oraciones:
        if len(actual) + len(oracion) + 1 <= max_caracteres:
            actual += " " + oracion if actual else oracion
        else:
            if actual and es_segmento_valido(actual):
                segmentos.append(actual.strip())
            actual = oracion

    if actual and es_segmento_valido(actual):
        segmentos.append(actual.strip())

    return segmentos

def analizar_sentimiento(texto):
    blob = TextBlob(texto)
    return {
        'polaridad': blob.sentiment.polarity,
        'subjetividad': blob.sentiment.subjectivity
    }

def clasificar_contexto(texto, nicho='GENERAL'):
    texto_lower = texto.lower()
    conceptos_nicho = CONCEPTOS_POR_NICHO.get(nicho, CONCEPTOS_POR_NICHO['GENERAL'])
    for concepto, patrones in conceptos_nicho.items():
        if any(p in texto_lower for p in patrones):
            return concepto
    return 'TESTIMONIO_GENERAL'

def extraer_dialogos(texto):
    patron = r'"([^"]+)"'
    matches = re.findall(patron, texto)

    dialogos = []
    for dialogo in matches:
        dialogo_limpio = dialogo.strip()
        if len(dialogo_limpio) < 20:
            continue
        if any(nota in dialogo_limpio.lower() for nota in ['hidden camera', 'segment', '---', '...', 'transcript', 'video', 'audio', 'recording']):
            continue

        inicio = max(0, texto.find(dialogo) - 200)
        contexto = texto[inicio:inicio + 400]
        hablante = 'DESCONOCIDO'

        if es_segmento_valido(dialogo):
            dialogos.append({
                'hablante': hablante,
                'texto': dialogo_limpio,
                'contexto': contexto[:150].strip(),
                'longitud': len(dialogo_limpio)
            })

    return dialogos

def analizar_por_hablante(segmentos_analizados):
    hablantes = defaultdict(list)

    for seg in segmentos_analizados:
        hablante = seg.get('hablante', 'DESCONOCIDO')
        polaridad = seg.get('polaridad', 0.0)
        hablantes[hablante].append(polaridad)

    resultados = {}
    for hablante, polaridades in hablantes.items():
        if polaridades:
            resultados[hablante] = {
                'promedio': round(sum(polaridades) / len(polaridades), 3),
                'min': round(min(polaridades), 3),
                'max': round(max(polaridades), 3),
                'n_segmentos': len(polaridades),
                'confianza': 'alta' if len(polaridades) >= 5 else 'media' if len(polaridades) >= 2 else 'baja'
            }
    return resultados

def calcular_coocurrencias(segmentos, terminos_clave):
    coocurrencias = defaultdict(int)
    for seg in segmentos:
        texto = seg['texto'].lower()
        for i, t1 in enumerate(terminos_clave):
            for t2 in terminos_clave[i+1:]:
                if t1 in texto and t2 in texto:
                    coocurrencias[(t1, t2)] += 1
    return sorted(coocurrencias.items(), key=lambda x: -x[1])[:15]

def analisis_conceptos(segmentos, nicho='GENERAL'):
    conceptos = CONCEPTOS_POR_NICHO.get(nicho, CONCEPTOS_POR_NICHO['GENERAL'])
    contador_conceptos = defaultdict(int)
    for seg in segmentos:
        conceptos_encontrados = []
        for concepto, patrones in conceptos.items():
            if any(p in seg['texto'].lower() for p in patrones):
                conceptos_encontrados.append(concepto)
        for c in conceptos_encontrados:
            contador_conceptos[c] += 1
    return sorted(contador_conceptos.items(), key=lambda x: -x[1])

def analisis_temporal(segmentos_analizados, n_secciones=5):
    if not segmentos_analizados:
        return []
    tamaño_seccion = max(1, len(segmentos_analizados) // n_secciones)
    resultados = []

    for i in range(n_secciones):
        inicio = i * tamaño_seccion
        fin = (i + 1) * tamaño_seccion if i < n_secciones - 1 else len(segmentos_analizados)
        seccion = segmentos_analizados[inicio:fin]
        if not seccion:
            continue
        polaridades = [s.get('polaridad', 0.0) for s in seccion]
        contextos = [s.get('contexto', 'TESTIMONIO_GENERAL') for s in seccion]
        contexto_predominante = Counter(contextos).most_common(1)[0][0] if contextos else 'TESTIMONIO_GENERAL'

        resultados.append({
            'seccion': i + 1,
            'segmentos': len(seccion),
            'polaridad_promedio': round(sum(polaridades) / len(polaridades), 3),
            'polaridad_min': round(min(polaridades), 3),
            'polaridad_max': round(max(polaridades), 3),
            'contexto_predominante': contexto_predominante
        })
    return resultados

def exportar_json(datos, archivo_salida):
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON exportado: {archivo_salida}")
    except Exception as e:
        print(f"⚠️ Error exportando JSON: {e}")

def exportar_resumen_txt(analisis, archivo_salida):
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("🧠 ANÁLISIS COMPLETO V6.5\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"📄 Documento: {analisis['documento']}\n")
            f.write(f"📊 Segmentos válidos: {analisis['total_segmentos']}\n")
            f.write(f"💬 Diálogos extraídos: {analisis['total_dialogos']}\n")
            f.write(f"🔍 Nicho detectado: {analisis['nicho']}\n\n")

            f.write("📌 Términos clave (sin stopwords):\n")
            for term, freq in analisis['terminos_clave'][:10]:
                f.write(f"  {term}: {freq}\n")

            f.write("\n📊 SENTIMIENTO POR HABLANTE:\n")
            for hablante, datos in sorted(analisis['sentimiento_por_hablante'].items(), key=lambda x: -x[1]['n_segmentos']):
                if hablante != 'DESCONOCIDO' or datos['n_segmentos'] > 10:
                    emoji = "🟢" if datos['promedio'] > 0.1 else "🔴" if datos['promedio'] < -0.1 else "⚪"
                    confianza = f" ({datos['confianza']})" if datos['confianza'] != 'alta' else ""
                    f.write(f"  {emoji} {hablante}: {datos['promedio']:.2f}{confianza} ({datos['n_segmentos']} segmentos)\n")

            f.write("\n🔗 RELACIONES TEMÁTICAS:\n")
            for (t1, t2), freq in analisis['coocurrencias'][:10]:
                f.write(f"  {t1} ↔ {t2}: {freq}\n")

            f.write("\n📈 ANÁLISIS TEMPORAL:\n")
            for seg in analisis['analisis_temporal']:
                emoji = "🟢" if seg['polaridad_promedio'] > 0.1 else "🔴" if seg['polaridad_promedio'] < -0.1 else "⚪"
                f.write(f"  Sección {seg['seccion']}: {emoji} {seg['polaridad_promedio']:.2f} ({seg['contexto_predominante']})\n")

            f.write("\n💬 CITAS CLAVE:\n")
            for dialogo in analisis['citas_clave'][:5]:
                f.write(f"  [{dialogo['hablante']}]: {dialogo['texto'][:100]}...\n")

            f.write("\n🔍 CONCEPTOS DOMINANTES:\n")
            for concepto, freq in analisis['conceptos']:
                f.write(f"  {concepto}: {freq}\n")
        print(f"✅ Resumen TXT exportado: {archivo_salida}")
    except Exception as e:
        print(f"⚠️ Error exportando TXT: {e}")

def exportar_reporte_md(analisis, archivo_salida):
    try:
        reporte = f"""# 📊 Análisis de Transcripción

## 📄 Resumen Ejecutivo
- **Documento**: `{analisis['documento']}`
- **Segmentos válidos**: {analisis['total_segmentos']}
- **Diálogos extraídos**: {analisis['total_dialogos']}
- **Nicho detectado**: **{analisis['nicho']}**

---

## 📌 Términos clave (top 10)
"""
        for term, freq in analisis['terminos_clave'][:10]:
            reporte += f"- `{term}`: {freq}\n"

        reporte += "\n## 📊 Sentimiento por Hablante\n"
        reporte += "| Hablante | Polaridad | Segmentos | Confianza |\n"
        reporte += "|----------|-----------|-----------|-----------|\n"
        for hablante, datos in sorted(analisis['sentimiento_por_hablante'].items(), key=lambda x: -x[1]['n_segmentos']):
            if hablante != 'DESCONOCIDO' or datos['n_segmentos'] > 10:
                emoji = '🟢' if datos['promedio'] > 0.1 else '🔴' if datos['promedio'] < -0.1 else '⚪'
                reporte += f"| {emoji} {hablante} | {datos['promedio']:.2f} | {datos['n_segmentos']} | {datos['confianza']} |\n"

        reporte += "\n## 🔗 Relaciones Temáticas (Co-ocurrencias)\n"
        for (t1, t2), freq in analisis['coocurrencias']:
            reporte += f"- `{t1}` ↔ `{t2}`: {freq}\n"

        reporte += "\n## 🔍 Conceptos Dominantes\n"
        for concepto, freq in analisis['conceptos']:
            reporte += f"- **{concepto}**: {freq} menciones\n"

        reporte += "\n## 📈 Análisis Temporal\n"
        reporte += "| Sección | Segmentos | Polaridad | Contexto |\n"
        reporte += "|---------|-----------|-----------|----------|\n"
        for seg in analisis['analisis_temporal']:
            emoji = '🟢' if seg['polaridad_promedio'] > 0.1 else '🔴' if seg['polaridad_promedio'] < -0.1 else '⚪'
            reporte += f"| {seg['seccion']} | {seg['segmentos']} | {emoji} {seg['polaridad_promedio']:.2f} | {seg['contexto_predominante']} |\n"

        reporte += "\n## 💬 Citas Clave\n"
        for dialogo in analisis['citas_clave'][:5]:
            reporte += f"- **{dialogo['hablante']}**: {dialogo['texto'][:150]}...\n"

        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(reporte)
        print(f"✅ Reporte MD exportado: {archivo_salida}")
    except Exception as e:
        print(f"⚠️ Error exportando MD: {e}")

def exportar_sqlite_desde_json(json_path, db_path=None):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON no encontrado: {json_path}")
    
    if db_path is None:
        db_path = json_path.replace('_analisis_completo.json', '_analisis.db')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            term TEXT,
            frequency INTEGER
        )
    ''')
    
    terminos = data.get('terminos_clave', [])
    for i, (term, freq) in enumerate(terminos, 1):
        cursor.execute('''
            INSERT INTO keywords (id, analysis_id, term, frequency)
            VALUES (?, ?, ?, ?)
        ''', (i, 1, term, freq))
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            language TEXT,
            analyzed_at TEXT,
            total_lines INTEGER,
            total_words INTEGER,
            sentiment_polarity REAL,
            sentiment_subjectivity REAL,
            nicho TEXT
        )
    ''')
    
    sentiment = data.get('sentimiento_global', {})
    cursor.execute('''
        INSERT INTO analysis (
            id, filename, language, analyzed_at,
            total_lines, total_words,
            sentiment_polarity, sentiment_subjectivity,
            nicho
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        1,
        data.get('documento', 'desconocido'),
        'ES' if 'es' in data.get('documento', '').lower() else 'EN',
        '2026-08-31',
        data.get('total_segmentos', 0),
        len(' '.join([s.get('texto', '') for s in data.get('segmentos', [])])),
        sentiment.get('polaridad', 0),
        sentiment.get('subjetividad', 0),
        data.get('nicho', 'GENERAL')
    ))
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite exportado: {db_path}")
    return db_path

def consolidar_en_duckdb(csv_path, video_id, db_path_duckdb=os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')):
    """Consolida datos en DuckDB usando CLI (compatible con Termux)."""
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV no encontrado: {csv_path}")
        return False

    try:
        import subprocess
        import csv as csv_module
        
        # Verificar que el CLI existe
        result = subprocess.run(['duckdb', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("⚠️ DuckDB CLI no disponible")
            return False
        
        # Verificar la estructura del CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_module.reader(f)
            headers = next(reader, [])
        
        # Determinar las columnas correctas
        if 'term' in headers and 'frequency' in headers:
            # Estructura esperada
            term_col = 'term'
            freq_col = 'frequency'
        elif 'keyword' in headers and 'frecuencia' in headers:
            # Estructura alternativa 1
            term_col = 'keyword'
            freq_col = 'frecuencia'
        elif 'termino' in headers and 'frecuencia' in headers:
            # Estructura alternativa 2
            term_col = 'termino'
            freq_col = 'frecuencia'
        elif len(headers) >= 2:
            # Usar las primeras dos columnas
            term_col = headers[0]
            freq_col = headers[1]
            print(f"⚠️ Usando columnas: {term_col}, {freq_col}")
        else:
            print(f"❌ CSV no tiene suficientes columnas: {headers}")
            return False
        
        # Crear tablas si no existen
        schema_sql = """
CREATE TABLE IF NOT EXISTS terminos_raw (
    video VARCHAR,
    term VARCHAR,
    frequency INTEGER
);

CREATE TABLE IF NOT EXISTS progreso (
    video VARCHAR PRIMARY KEY,
    estado VARCHAR DEFAULT 'pendiente',
    fecha_inicio DATE,
    fecha_completado DATE
);
"""
        
        # Ejecutar schema
        result = subprocess.run(
            ['duckdb', db_path_duckdb],
            input=schema_sql,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Error creando schema: {result.stderr}")
            return False
        
        # Insertar datos desde CSV con las columnas correctas
        insert_sql = f"""
INSERT INTO terminos_raw (video, term, frequency)
SELECT '{video_id}' as video, "{term_col}" as term, "{freq_col}" as frequency
FROM read_csv_auto('{csv_path}');

INSERT OR IGNORE INTO progreso (video, estado)
VALUES ('{video_id}', 'pendiente');
"""
        
        # Ejecutar inserción
        result = subprocess.run(
            ['duckdb', db_path_duckdb],
            input=insert_sql,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {video_id} consolidado en DuckDB (columnas: {term_col}, {freq_col})")
            return True
        else:
            print(f"⚠️ No se pudo consolidar en DuckDB: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️ No se pudo consolidar en DuckDB: {e}")
        return False



# ========================================================================
# FUNCIÓN PRINCIPAL
# ========================================================================

def main():
    metricas = MetricasPipeline() if MetricasPipeline else None

    if len(sys.argv) < 2:
        print("❌ Uso: python3 analisis_completo_v6.4.py archivo_transcripcion.txt")
        sys.exit(1)

    archivo = sys.argv[1]

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {archivo}")
        sys.exit(1)

    if metricas:
        with metricas.medir('detectar_nicho'):
            try:
                nicho = detectar_nicho(texto)
            except:
                nicho = 'GENERAL'
    else:
        try:
            nicho = detectar_nicho(texto)
        except:
            nicho = 'GENERAL'

    try:
        from modulos.detectar_modo import detectar_modo_automatico
        modo_hablantes = detectar_modo_automatico(texto)
    except:
        modo_hablantes = 'auto'
    
    print("🧠 ANÁLISIS COMPLETO V6.5")
    print("=" * 60)
    print(f"🔍 Nicho detectado: {nicho}")

    if metricas:
        with metricas.medir('limpiar_texto'):
            texto_limpio = limpiar_texto(texto)
    print(f"📄 Texto cargado: {len(texto)} caracteres → limpio: {len(texto_limpio)}")

    if metricas:
        with metricas.medir('segmentar_oraciones'):
            segmentos_texto = segmentar_por_oraciones(texto_limpio)
    print(f"📊 Segmentos válidos: {len(segmentos_texto)}")

    segmentos_analizados = []
    for seg_texto in segmentos_texto:
        analisis = analizar_sentimiento(seg_texto)
        segmentos_analizados.append({
            'texto': seg_texto,
            'polaridad': analisis['polaridad'],
            'subjetividad': analisis['subjetividad'],
            'contexto': clasificar_contexto(seg_texto, nicho),
            'hablante': 'DESCONOCIDO'
        })


    if DetectorHablantes is not None:
        try:
            detector = DetectorHablantes(modo=modo_hablantes)
            hablantes_detectados = detector.detectar(texto_limpio, segmentos_texto)
            print(f"\n🔊 Hablantes detectados ({modo_hablantes}): {len(hablantes_detectados)}")
            for h in hablantes_detectados:
                simbolo = '👤' if h.es_principal else '📎'
                print(f"   {simbolo} {h.nombre} ({h.rol}) - {h.segmentos} seg")
        except Exception as e:
            print(f"⚠️ Error en detección de hablantes: {e}")

    dialogos = extraer_dialogos(texto_limpio)
    print(f"💬 Diálogos extraídos: {len(dialogos)}")

    if metricas:
        with metricas.medir('filtrar_stopwords'):
            palabras = filtrar_stopwords(texto_limpio, nicho)
    # Extraer N-gramas compuestos
    n_gramas_ai = [
        'value alignment', 'goal alignment', 'recursive self-improvement',
        'chain-of-thought', 'chain of thought', 'cot monitoring',
        'machine intelligence', 'reasoning models', 'reasoning process'
    ]
    
    n_gramas_encontrados = []
    for ngrama in n_gramas_ai:
        if ngrama in texto_limpio.lower():
            frecuencia = texto_limpio.lower().count(ngrama)
            n_gramas_encontrados.append((ngrama, frecuencia))
    
    if n_gramas_encontrados:
        print(f"\n🔗 N-gramas detectados: {len(n_gramas_encontrados)}")
        for ngrama, freq in n_gramas_encontrados[:5]:
            print(f"  {ngrama}: {freq}")
    
    terminos = Counter(palabras).most_common(20)

    print("\n📌 Términos clave (sin stopwords):")
    for term, freq in terminos[:10]:
        print(f"  {term}: {freq}")

    stats_hablantes = analizar_por_hablante(segmentos_analizados)

    print("\n📊 SENTIMIENTO POR HABLANTE:")
    for hablante, datos in sorted(stats_hablantes.items(), key=lambda x: -x[1]['n_segmentos']):
        if hablante != 'DESCONOCIDO' or datos['n_segmentos'] > 10:
            emoji = "🟢" if datos['promedio'] > 0.1 else "🔴" if datos['promedio'] < -0.1 else "⚪"
            confianza = f" ({datos['confianza']})" if datos['confianza'] != 'alta' else ""
            print(f"  {emoji} {hablante}: {datos['promedio']:.2f}{confianza} ({datos['n_segmentos']} segmentos)")

    terminos_clave = [t for t, f in terminos[:10]]
    coocurrencias = calcular_coocurrencias(segmentos_analizados, terminos_clave)

    print("\n🔗 CO-OCURRENCIAS:")
    for (t1, t2), freq in coocurrencias[:10]:
        print(f"  {t1} + {t2}: {freq}")

    conceptos = analisis_conceptos(segmentos_analizados, nicho)
    print("\n🔍 CONCEPTOS DOMINANTES:")
    for concepto, freq in conceptos:
        print(f"  {concepto}: {freq}")

    temporal = analisis_temporal(segmentos_analizados)
    print("\n📈 ANÁLISIS TEMPORAL:")
    for seg in temporal:
        emoji = "🟢" if seg['polaridad_promedio'] > 0.1 else "🔴" if seg['polaridad_promedio'] < -0.1 else "⚪"
        print(f"  Sección {seg['seccion']}: {emoji} {seg['polaridad_promedio']:.2f} ({seg['contexto_predominante']})")

    print("\n💬 CITAS CLAVE:")
    for dialogo in dialogos[:5]:
        print(f"  [{dialogo['hablante']}]: {dialogo['texto'][:100]}...")

    datos_analisis = {
        'documento': archivo,
        'nicho': nicho,
        'total_segmentos': len(segmentos_analizados),
        'total_dialogos': len(dialogos),
        'sentimiento_global': {
            'polaridad': round(sum(s['polaridad'] for s in segmentos_analizados) / len(segmentos_analizados), 3) if segmentos_analizados else 0,
            'subjetividad': round(sum(s['subjetividad'] for s in segmentos_analizados) / len(segmentos_analizados), 3) if segmentos_analizados else 0
        },
        'terminos_clave': terminos,
        'sentimiento_por_hablante': stats_hablantes,
        'coocurrencias': coocurrencias,
        'conceptos': conceptos,
        'analisis_temporal': temporal,
        'citas_clave': dialogos
    }

    base = archivo.replace('.txt', '')
    exportar_json(datos_analisis, f"{base}_analisis_completo.json")
    exportar_resumen_txt(datos_analisis, f"{base}_resumen.txt")
    exportar_reporte_md(datos_analisis, f"{base}_reporte.md")

    try:
        exportar_sqlite_desde_json(f"{base}_analisis_completo.json")
    except Exception as e:
        print(f"⚠️ Error exportando SQLite: {e}")

    try:
        csv_path = f"{base}_analisis.csv"
        if not os.path.exists(csv_path):
            conn_sqlite = sqlite3.connect(f"{base}_analisis.db")
            cursor = conn_sqlite.cursor()
            cursor.execute("SELECT * FROM keywords;")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([i[0] for i in cursor.description])
                writer.writerows(cursor.fetchall())
            conn_sqlite.close()
        
        video_id = os.path.basename(base).replace('_EN_FORZADO', '').replace('_ES', '')
        # Guardar N-gramas en DuckDB
        if n_gramas_encontrados:
            import subprocess
            sql_ngramas = []
            for ngrama, freq in n_gramas_encontrados:
                sql_ngramas.append(f"INSERT INTO terminos_raw VALUES ('{video_id}', '{ngrama}', {freq});")
            
            subprocess.run(
                ['duckdb', os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')],
                input='\n'.join(sql_ngramas),
                capture_output=True, text=True, timeout=15
            )
            print(f"  🔗 {len(n_gramas_encontrados)} N-gramas guardados en DuckDB")
        
        consolidar_en_duckdb(csv_path, video_id)
    except Exception as e:
        print(f"⚠️ No se pudo consolidar en DuckDB: {e}")

    if metricas:
        metricas.imprimir()
        metricas.exportar_json(f"{base}_metricas.json")
    
    # Generar Abstract jerárquico (opcional)
    if GeneradorAbstract is not None and '--abstract' in sys.argv:
        try:
            generador = GeneradorAbstract()
            
            # Construir jerarquía simple
            jerarquia = {
                'nicho_principal': nicho,
                'secundarios': {}
            }
            
            abstract = generador.generar(
                jerarquia,
                [t for t, _ in terminos[:10]],
                timestamps=None
            )
            
            ruta_abstract = f"{base}_abstract.md"
            with open(ruta_abstract, 'w', encoding='utf-8') as f:
                f.write(abstract)
            
            print(f"  📝 Abstract: {ruta_abstract}")
        except Exception as e:
            print(f"  ⚠️ No se pudo generar Abstract: {e}")
    
    print("\n✅ Análisis completo finalizado")
    print(f"📁 Archivos generados:")
    print(f"  📊 JSON: {base}_analisis_completo.json")
    print(f"  📄 TXT:  {base}_resumen.txt")
    print(f"  📝 MD:   {base}_reporte.md")
    print(f"  🗄️ SQLite: {base}_analisis.db")

    # Integrar timestamps si existe VTT
    try:
        from modulos.timestamps import ParserVTT, TimestampsDB
        
        vtt_file = f"/sdcard/Download/Transcript_{video_id}_timestamps.vtt"
        if os.path.exists(vtt_file):
            parser = ParserVTT()
            segmentos = parser.parsear_archivo(vtt_file)
            
            db_timestamps = TimestampsDB()
            success = db_timestamps.guardar_segmentos(video_id, segmentos)
            
            if success:
                print(f"  ⏱️ Timestamps: {len(segmentos)} segmentos guardados")
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ No se pudieron guardar timestamps: {e}")

if __name__ == "__main__":
    main()
