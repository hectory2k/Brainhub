#!/usr/bin/env python3
"""
Análisis completo de documentales/entrevistas V6.3
Arquitectura modular con validación de hablantes y exportación a SQLite
Uso: python3 analisis_completo_v6.3.py archivo_transcripcion.txt
"""

import sys
import os
import re
import json
import sqlite3
import csv
from collections import Counter, defaultdict
from textblob import TextBlob

# Agregar directorio de módulos al path
sys.path.insert(0, os.path.expanduser('~/proyectos/nlp'))

# Intentar importar módulos, con fallback a funciones locales
try:
    from modulos.validar_hablantes import filtrar_hablantes_falsos
except ImportError:
    def filtrar_hablantes_falsos(segmentos, texto_completo):
        return segmentos

try:
    from modulos.detectar_nicho import detectar_nicho
except ImportError:
    def detectar_nicho(texto):
        return 'GENERAL'

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
    
    # Obtener stopwords del nicho (desde JSON o vacío)
    try:
        stopwords_nicho = get_stopwords(nicho, lang)
    except:
        stopwords_nicho = set()
    
    # Stopwords básicas
    stopwords_base = {
        'en': {'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','that','this','which','who','whom','have','has','had','do','does','did','be','is','are','was','were','been','being','there','here','when','where','why','how','all','each','every','both','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','just','can','will','should','now','i','you','he','she','it','we','they','what','if','because','as','until','while','me','him','her','us','them','my','your','his','our','their','see','want','one','don','dont','didnt','doesnt','cant','couldnt','wouldnt','im','youre','hes','shes','ive','thats','theres','said','says','say','get','got','go','come','make','made','know','think','thing','things','right','yes','no','way','well','really','actually','basically','like','even','back','take','took','give','gave','good','great','little'},
        'es': {'el','la','los','las','un','una','unos','unas','y','o','pero','en','con','por','para','de','del','al','que','quien','cual','este','esta','estos','estas','ese','esa','esos','esas','aquel','aquella','aquellos','aquellas','mi','tu','su','mis','tus','sus','me','te','se','nos','les','lo','la','le','los','las','les','yo','tu','el','ella','nosotros','nosotras','ustedes','ellos','ser','estar','tener','hacer','decir','poder','dar','saber','muy','más','menos','mucho','poco','mismo','propio','cada','todo','toda','todos','todas','algun','alguno','alguna','ningun','que','qué','si','sí','don','dont','uno','una','quiero','quieres','quiere','ver','ves','ve','visto','también','tambien','solo','solamente','ya','aún','aun','asi','así','entonces','despues','después','antes','ahora','siempre','nunca','jamas','jamás','donde','como','cómo','eso','esto','son','eres','fue','hace','hacen','fueron'}
    }
    
    stopwords = stopwords_base.get(lang, set()) | stopwords_nicho
    stopwords.update({'que', 'cual', 'quien', 'donde', 'como', 'cuando'})
    
    filtradas = [p for p in palabras if p not in stopwords]
    
    if sum(1 for p in palabras if p == 'que') > 10:
        print(f"⚠️ DEBUG: 'que' aparece {sum(1 for p in palabras if p == 'que')} veces antes de filtrar")
    
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

def identificar_hablante(texto, contexto="", nombres_globales=None):
    texto_lower = texto.lower()
    contexto_lower = contexto.lower()
    combinado = texto_lower + " " + contexto_lower

    if nombres_globales:
        for nombre in nombres_globales:
            if nombre.lower() in combinado:
                if 'bikel' in combinado or 'rosalia' in combinado:
                    return 'PSICÓLOGA (Rosalia Bikel)'
                if 'cyran' in combinado or 'glenda' in combinado:
                    return 'PSICÓLOGA (Glenda Cyran)'
                if 'brusco' in combinado or 'ana' in combinado:
                    return 'ABOGADA (Ana Brusco)'
                if 'dietze' in combinado or 'juan carlos' in combinado:
                    return 'ABOGADO (Juan Carlos Dietze)'
                if 'sergio' in combinado and 'hidden camera' in combinado:
                    return 'PADRE (Sergio)'
                return 'DESCONOCIDO'

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

def identificar_hablantes_con_contexto(segmentos, texto_completo):
    nombres_globales = extraer_nombres_propios(texto_completo)
    for idx, seg in enumerate(segmentos):
        contexto_ventana = ""
        for offset in range(-2, 3):
            if 0 <= idx + offset < len(segmentos):
                contexto_ventana += " " + segmentos[idx + offset]['texto']
        seg['hablante'] = identificar_hablante(
            seg['texto'],
            contexto_ventana,
            nombres_globales
        )
    return segmentos

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
        hablante = identificar_hablante(dialogo, contexto)

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
            f.write("🧠 ANÁLISIS COMPLETO V6.3\n")
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
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV no encontrado: {csv_path}")
        return False
    
    try:
        import duckdb
        conn = duckdb.connect(db_path_duckdb)
        conn.execute(f"""
            INSERT INTO terminos_raw (video, term, frequency)
            SELECT 
                '{video_id}' as video,
                term,
                frequency
            FROM read_csv_auto('{csv_path}')
        """)
        conn.execute(f"""
            INSERT OR IGNORE INTO progreso (video)
            VALUES ('{video_id}')
        """)
        conn.close()
        print(f"✅ {video_id} consolidado en DuckDB")
        return True
    except Exception as e:
        print(f"⚠️ No se pudo consolidar en DuckDB: {e}")
        return False

# ========================================================================
# FUNCIÓN PRINCIPAL
# ========================================================================

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 analisis_completo_v6.3.py archivo_transcripcion.txt")
        sys.exit(1)

    archivo = sys.argv[1]

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {archivo}")
        sys.exit(1)

    # Detectar nicho
    try:
        nicho = detectar_nicho(texto)
    except:
        nicho = 'GENERAL'
    
    print("🧠 ANÁLISIS COMPLETO V6.3")
    print("=" * 60)
    print(f"🔍 Nicho detectado: {nicho}")

    texto_limpio = limpiar_texto(texto)
    print(f"📄 Texto cargado: {len(texto)} caracteres → limpio: {len(texto_limpio)}")

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

    segmentos_analizados = identificar_hablantes_con_contexto(segmentos_analizados, texto_limpio)

    try:
        segmentos_analizados = filtrar_hablantes_falsos(segmentos_analizados, texto_limpio)
    except:
        pass

    dialogos = extraer_dialogos(texto_limpio)
    print(f"💬 Diálogos extraídos: {len(dialogos)}")

    palabras = filtrar_stopwords(texto_limpio, nicho)
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
        consolidar_en_duckdb(csv_path, video_id)
    except Exception as e:
        print(f"⚠️ No se pudo consolidar en DuckDB: {e}")

    print("\n✅ Análisis completo finalizado")
    print(f"📁 Archivos generados:")
    print(f"  📊 JSON: {base}_analisis_completo.json")
    print(f"  📄 TXT:  {base}_resumen.txt")
    print(f"  📝 MD:   {base}_reporte.md")
    print(f"  🗄️ SQLite: {base}_analisis.db")

if __name__ == "__main__":
    main()
