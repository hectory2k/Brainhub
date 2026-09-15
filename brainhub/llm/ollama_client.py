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

    def __init__(self, model: str = 'gemma:2b', url: str = 'http://localhost:11434', timeout: int = 300):
        self.model = model
        self.url = url
        self.timeout = timeout

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

    def generar(self, prompt: str, system: Optional[str] = None) -> str:
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
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
        prompt = f"Resume en {max_oraciones} oraciones:\n\n{texto[:3000]}"
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
