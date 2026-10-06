# Aprendizajes acumulados (auditoría V6.5)

1. **Output confuso != bug funcional** (#3b)
   El dato puede estar bien y la presentación engañar.
   Primero verificar la capa donde se manifiesta el síntoma.

2. **Default silencioso != clasificación real** (#4)
   Una categoría de fallback disfrazada de categoría legítima
   contamina agregaciones por votación (ej. most_common).
   Un default honesto ("NO_CLASIFICADO") señala el bug en vez
   de enmascararlo.

3. **Verificar la capa antes de tocar** (#3b, #4)
   grep + snippet + output real, en ese orden, antes de cualquier fix.
   Los dos bugs se resolvieron con 3 líneas porque el diagnóstico previo
   fue correcto.
