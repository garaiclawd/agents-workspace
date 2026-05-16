import os
import requests
from dotenv import load_dotenv

# Subimos 4 niveles: tools -> openrouter -> Tools -> shared
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"

def fetch_openrouter_credits() -> dict:
    """Consulta la API de OpenRouter y devuelve el JSON crudo."""
    if not OPENROUTER_API_KEY:
        raise ValueError("Error: OPENROUTER_API_KEY no encontrada en el archivo .env")

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    
    resp = requests.get(OPENROUTER_CREDITS_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    
    return resp.json().get("data", {})