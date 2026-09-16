"""Cliente Ollama para BrainHub.

Uso:
    from brainhub.llm.ollama_client import OllamaClient

    cliente = OllamaClient(model='phi3:mini')
    abstract = cliente.resumir(texto)
"""
import requests
from typing import Optional


class OllamaClient:
    """Cliente simple para Ollama."""

    def __init__(
        self,
        model: str = 'gemma:2b',
        url: str = 'http://localhost:11434',
        timeout: int = 300,
        num_predict: int = 150,
    ):
        self.model = model
        self.url = url
        self.timeout = timeout
        self.num_predict = num_predict

    def disponible(self) -> bool:
        try:
            r = requests.get(f'{self.url}/api/tags', timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def modelos(self) -> list:
        try:
            r = requests.get(f'{self.url}/api/tags', timeout=5)
            return [m['name'] for m in r.json().get('models', [])]
        except Exception:
            return []

    def generar(self, prompt: str, system: Optional[str] = None, keep_alive: int = 0) -> str:
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'keep_alive': keep_alive,
            'options': {
                'num_predict': self.num_predict,
            },
        }
        if system:
            payload['system'] = system

        r = requests.post(
            f'{self.url}/api/generate',
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json().get('response', '')

    def resumir(self, texto: str, max_oraciones: int = 3) -> str:
        prompt = f"Responde en español. Resume en {max_oraciones} oraciones: {texto[:3000]}"
        return self.generar(prompt)

    def responder_con_contexto(self, consulta: str, contexto: str) -> str:
        prompt = f"""Contexto:
{contexto[:3000]}

Consulta: {consulta}

Respondé usando SOLO el contexto. Si no está, decí "No tengo esa información"."""
        return self.generar(prompt)


if __name__ == '__main__':
    cliente = OllamaClient()

    if not cliente.disponible():
        print("❌ Ollama no está corriendo")
        print("   Arrancar: ollama serve &")
        exit(1)

    print(f"✅ Ollama disponible")
    print(f"   Modelos: {cliente.modelos()}")
    print()

    # Test de resumen
    texto = "Kubernetes es un orquestador de contenedores. Permite desplegar, escalar y gestionar aplicaciones en clusters."
    print("Test de resumen:")
    print(f"  {cliente.resumir(texto)}")


# ==============================================
# Métodos agregados 2026-09-15 para fallback
# ==============================================

def descargar(self):
    """Descarga el modelo de RAM (keep_alive=0)."""
    import urllib.request as _url
    try:
        data = json.dumps({
            "model": self.model,
            "keep_alive": 0
        }).encode()
        req = _url.Request(
            f"{self.url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with _url.urlopen(req, timeout=5):
            pass
        return True
    except Exception:
        return False


def hay_ram_suficiente(min_gb: float = 3.0) -> tuple:
    """Verifica si hay RAM suficiente.
    
    Returns:
        (hay_ram, gb_disponibles, razon)
    """
    try:
        with open('/proc/meminfo') as f:
            for linea in f:
                if linea.startswith('MemAvailable:'):
                    kb = int(linea.split()[1])
                    gb = kb / 1024 / 1024
                    hay = gb >= min_gb
                    razon = f"{gb:.1f} GB disponibles (min: {min_gb} GB)"
                    return hay, gb, razon
    except Exception as e:
        return False, 0.0, f"Error leyendo /proc/meminfo: {e}"
    return False, 0.0, "No se pudo leer MemAvailable"


# Agregar métodos a la clase
OllamaClient.descargar = descargar
