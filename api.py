#!/data/data/com.termux/files/usr/bin/python3
"""
API Flask frugal para BrainHub.
Expone consultas a DuckDB, grafos y análisis.
"""

from flask import Flask, jsonify, request
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/proyectos/nlp')

from modulos.detectar_nicho import detectar_nicho
from modulos.rag_simple import RAGSimple
from modulos.integrar_duckdb import consultar

app = Flask(__name__)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check simple."""
    return jsonify({'estado': 'ok', 'sistema': 'BrainHub', 'version': '6.5'})


@app.route('/api/nicho', methods=['GET'])
def nicho():
    """Detectar nicho de un texto."""
    texto = request.args.get('texto', '')
    if not texto:
        return jsonify({'error': 'Falta parámetro texto'}), 400
    
    resultado = detectar_nicho(texto)
    return jsonify({'nicho': resultado})


@app.route('/api/terminos', methods=['GET'])
def terminos():
    """Top términos de DuckDB."""
    limite = int(request.args.get('limite', 10))
    
    sql = f"""
    SELECT term, SUM(frequency) as total
    FROM terminos_raw
    GROUP BY term
    ORDER BY total DESC
    LIMIT {limite}
    """
    
    resultados = consultar(sql)
    return jsonify({'terminos': resultados})


@app.route('/api/buscar', methods=['GET'])
def buscar():
    """Búsqueda en segmentos reales."""
    q = request.args.get('q', '')
    if not q:
        return jsonify({'error': 'Falta parámetro q'}), 400
    
    # Buscar en segmentos_timestamp
    sql = f"""
    SELECT texto, inicio_formato
    FROM segmentos_timestamp
    WHERE LOWER(texto) LIKE '%{q.lower()}%'
    LIMIT 5
    """
    
    try:
        resultados = consultar(sql)
        
        # Si no hay segmentos, buscar en términos
        if not resultados:
            sql_terminos = f"""
            SELECT term, SUM(frequency) as total
            FROM terminos_raw
            WHERE LOWER(term) LIKE '%{q.lower()}%'
            GROUP BY term
            ORDER BY total DESC
            LIMIT 5
            """
            resultados_terminos = consultar(sql_terminos)
            
            return jsonify({
                'consulta': q,
                'total': len(resultados_terminos),
                'terminos': [
                    {'termino': r[0], 'frecuencia': r[1]} 
                    for r in resultados_terminos if r and len(r) >= 2
                ]
            })
        
        return jsonify({
            'consulta': q,
            'total': len(resultados),
            'segmentos': [
                {'texto': r[0][:200], 'inicio': r[1]} 
                for r in resultados if r and len(r) >= 2
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/perfil', methods=['GET'])
def perfil():
    """Resumen por perfil."""
    tipo = request.args.get('tipo', 'tecnico')
    
    from modulos.resumen_perfil import ResumenPorPerfil
    gen = ResumenPorPerfil()
    
    analisis = {
        'nicho': 'AI_SAFETY',
        'secundarios': {},
        'terminos_clave': [('alignment', 20), ('scaling', 10)]
    }
    
    resumen = gen.generar(perfil=tipo, analisis=analisis)
    return jsonify({'perfil': tipo, 'resumen': resumen})


if __name__ == '__main__':
    print("🚀 BrainHub API")
    print("   http://localhost:5000/api/health")
    print("   http://localhost:5000/api/nicho?texto=...")
    print("   http://localhost:5000/api/buscar?q=...")
    app.run(host='0.0.0.0', port=5000, debug=True)
