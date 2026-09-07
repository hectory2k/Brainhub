#!/bin/bash
# Genera documento 80/20 con jerarquía automática de nichos

if [ -z "$1" ]; then
    echo "❌ Uso: documento_8020.sh archivo_analisis.json"
    exit 1
fi

python3 << PYEOF
import sys
import json
sys.path.insert(0, '/data/data/com.termux/files/home/proyectos/nlp')

from modulos.generar_abstract import GeneradorAbstract
from modulos.preguntas_debate import GeneradorPreguntas
from modulos.generar_documento import GeneradorDocumento
from modulos.ponderacion_nichos import PonderacionNichos
from modulos.coherencia_nichos import CoherenciaNichos
from modulos.reflexion import ReflexionPostAnalisis
from modulos.self_rag import SelfRAG
from modulos.rag_simple import RAGSimple
from modulos.nichos_manager import NichosManager

with open('$1', 'r') as f:
    datos = json.load(f)

terminos = [t for t, _ in datos.get('terminos_clave', [])[:10]]

manager = NichosManager()
diccionario = manager.get_todos_terminos()

texto_completo = ' '.join(terminos)
texto_lower = texto_completo.lower()

herramienta_especifica = None
if 'rag' in texto_lower or 'retrieval' in texto_lower:
    herramienta_especifica = 'RAG'
elif 'machine learning' in texto_lower:
    herramienta_especifica = 'MACHINE_LEARNING'

ponderador = PonderacionNichos(diccionario)
resultado = ponderador.analizar(texto_completo)

# Usar nicho original del JSON si existe
nicho_original = datos.get('nicho', 'GENERAL')

jerarquia = {
    'recurso_id': datos.get('content_id', 'sin_id'),
    'nicho_principal': nicho_original,
    'secundarios': resultado.get('secundarios', {})
}

if herramienta_especifica:
    jerarquia['secundarios']['herramienta'] = herramienta_especifica

# Aplicar coherencia
coherencia = CoherenciaNichos()
jerarquia = coherencia.corregir_jerarquia(jerarquia, texto_completo)

print(f"📊 Jerarquía: {jerarquia['nicho_principal']} + {jerarquia['secundarios']}")

abstract_gen = GeneradorAbstract()
abstract = abstract_gen.generar(jerarquia, terminos)

preguntas_gen = GeneradorPreguntas()
coocurrencias = datos.get('coocurrencias', [])
preguntas = preguntas_gen.generar(jerarquia, terminos, coocurrencias, texto_completo)

# Self-RAG: evaluar evidencia de los términos
if terminos:
    rag = RAGSimple()
    rag.indexar([t for t, _ in datos.get('terminos_clave', [])[:10]])
    self_rag = SelfRAG(rag)
    evaluacion = self_rag.buscar_con_reflexion(terminos[0][0] if isinstance(terminos[0], (list, tuple)) else terminos[0])
    print(f"🧠 Self-RAG: {evaluacion['accion']} (confianza: {evaluacion['confianza']})")

reflexion_gen = ReflexionPostAnalisis()
reflexiones = reflexion_gen.reflexionar(datos)

doc_gen = GeneradorDocumento()
doc_gen.cargar_datos(jerarquia, terminos, abstract, preguntas)
doc_gen.reflexiones = reflexiones  # agregar reflexiones

doc_gen.cargar_datos(jerarquia, terminos, abstract, preguntas)

ruta = '$1'.replace('_analisis_completo.json', '_documento_8020.md')
doc_gen.generar_markdown(ruta)
print(f"✅ {ruta}")
PYEOF
