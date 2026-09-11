import unicodedata
import re

# Palabras clave para cada nicho (usado por otros módulos)
NICHO_KEYWORDS = {
    'SALUD': [
        'salud', 'epidemiologia', 'hospital', 'paciente', 'medicina',
        'medico', 'clinico', 'enfermedad', 'brote', 'diagnostico',
        'mortalidad', 'morbilidad', 'ligamento', 'cruzado', 'rodilla',
        'lesion', 'cirugia', 'tratamiento'
    ],
    'TECNOLOGIA': [
        'python', 'pytorch', 'machine learning', 'deep learning',
        'software', 'hardware', 'programming', 'code', 'developer',
        'api', 'database', 'server', 'cloud', 'devops'
    ],
    'LEGAL': [
        'judge', 'court', 'custody', 'law', 'attorney', 'legal', 'lawyer',
        'tribunal', 'juez', 'abogado', 'demanda', 'fiscal', 'sentencia'
    ],
    'CIBERSEGURIDAD': [
        'hack', 'security', 'breach', 'malware', 'phishing', 'firewall',
        'encryption', 'vulnerability', 'exploit', 'attack', 'network',
        'hacker', 'seguridad', 'ataque'
    ],
    'FINANZAS': [
        'investment', 'stock', 'market', 'trading', 'portfolio',
        'bitcoin', 'cryptocurrency', 'forex', 'bonds', 'etf'
    ]
}


# Cargar diccionario externo si existe
try:
    import json
    from pathlib import Path
    ruta_nichos = Path.home() / 'proyectos/nlp/diccionario_nichos.json'
    if ruta_nichos.exists():
        with open(ruta_nichos, 'r', encoding='utf-8') as f:
            DICCIONARIO_EXTERNO = json.load(f)
        # Fusionar con keywords hardcodeados
        for nicho, info in DICCIONARIO_EXTERNO.items():
            if nicho not in NICHO_KEYWORDS:
                NICHO_KEYWORDS[nicho] = info.get('terminos', [])
            else:
                NICHO_KEYWORDS[nicho].extend(info.get('terminos', []))
except Exception:
    pass

PALABRAS_SALUD = set(NICHO_KEYWORDS['SALUD'])
PALABRAS_TECNOLOGIA = set(NICHO_KEYWORDS['TECNOLOGIA'])

def normalizar_texto(texto: str) -> str:
    """Normaliza preservando ñ/Ñ.

    FIX 2026-09-10: antes usaba NFD directo, que descompone ñ → n + ~
    y eliminaba la tilde, dejando "anos". Ahora delega en el módulo
    centralizado brainhub/texto/normalizar.py
    """
    import sys
    from pathlib import Path
    # Asegurar que el import funcione desde cualquier CWD
    raiz = Path(__file__).resolve().parent.parent
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    from brainhub.texto.normalizar import normalizar_preservando_enie
    return normalizar_preservando_enie(texto.lower())

def detectar_nicho(texto: str) -> str:
    texto_normalizado = normalizar_texto(texto)
    if not texto_normalizado:
        return "GENERAL"

    # Scoring por densidad con match por palabra completa
    # FIX 2026-09-11: usar \b para evitar falsos positivos
    # (antes 'ia' matcheaba en 'memoria', 'agi' en 'imagen')
    import re as _re
    scores = {}
    for nicho, terminos in NICHO_KEYWORDS.items():
        score = 0
        for p in terminos:
            patron = r'\b' + _re.escape(p) + r'\b'
            if _re.search(patron, texto_normalizado):
                score += 1
        if score > 0:
            scores[nicho] = score
    
    if not scores:
        return "GENERAL"
    
    # Si AI_SAFETY tiene score significativo, priorizarlo
    if 'AI_SAFETY' in scores and scores['AI_SAFETY'] >= 3:
        return 'AI_SAFETY'
    
    # Buscar N-gramas (frases compuestas)
    n_gramas_ai_safety = [
        'value alignment', 'goal alignment', 'recursive self-improvement',
        'chain-of-thought', 'chain of thought', 'cot monitoring',
        'machine intelligence', 'reasoning models', 'reasoning process',
        'pretraining data', 'training distribution', 'supervision pressure'
    ]
    
    for frase in n_gramas_ai_safety:
        if frase in texto_normalizado:
            if 'AI_SAFETY' not in scores:
                scores['AI_SAFETY'] = 0
            scores['AI_SAFETY'] += 5  # N-gramas pesan más
    
    # FIX 2026-09-10: desempate por prioridad de nicho
    # Sin esto, TECNOLOGIA ganaba empates contra FINANZAS por orden de dict
    PRIORIDAD_NICHO = {
        'ECONOMIA': 10,
        'FINANZAS': 9,
        'SALUD': 8,
        'LEGAL': 8,
        'EDUCACION': 7,
        'CIBERSEGURIDAD': 7,
        'COMPRAS_PUBLICAS': 6,
        'AI_SAFETY': 7,
        'TECNOLOGIA': 6,   # subida: con \b ya no hay falsos positivos
        'GENERAL': 0,
    }
    
    ganador = max(
        scores.keys(),
        key=lambda n: (scores[n], PRIORIDAD_NICHO.get(n, 0))
    )
    return ganador