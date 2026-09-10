import nltk
from nltk.stem import WordNetLemmatizer

# Inicializar lematizador
lemmatizer = WordNetLemmatizer()

# Diccionario de normalización manual para español
MAPA_ES = {
    "deudores": "deuda",
    "deudoras": "deuda",
    "deudas": "deuda",
    "años": "año",   # evita el bug de "anos"
}

def lematizar_termino(termino: str) -> str:
    t = termino.lower()
    if t in MAPA_ES:
        return MAPA_ES[t]
    try:
        return lemmatizer.lemmatize(t)
    except LookupError:
        return t  # fallback seguro si falta wordnet

def validar_conceptos(terminos):
    normalizados = [lematizar_termino(t) for t in terminos]
    # Aquí deberías enganchar tus funciones es_tecnico / es_generico reales
    return [t for t in normalizados if t not in ["head","main","nivel","estructura","sistema","preguntas"]]
