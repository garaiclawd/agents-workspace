import os
import requests
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS (Ruta exacta según tu imagen)
# ==========================================
# Detecta la raíz /home/garai/agents-workspace
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta al archivo .env en la carpeta shared
ENV_PATH = os.path.join(BASE_DIR, "shared", ".env")

# RUTA CRÍTICA CORREGIDA (Casing exacto y doble extensión .md.md)
SOUL_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "SOUL.md.md")

# Cargar las claves secretas
load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AGENT_MODEL") 
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================
# 2. LEER EL "ALMA" DEL AGENTE
# ==========================================
print(f"[*] Intentando leer: {SOUL_PATH}")
try:
    with open(SOUL_PATH, "r", encoding="utf-8") as file:
        soul_context = file.read()
    print("[+] Alma cargada correctamente.")
except FileNotFoundError:
    print(f"[-] ERROR: No se encontró el archivo en {SOUL_PATH}")
    exit()

# ==========================================
# 3. LLAMADA A OPENROUTER
# ==========================================
print(f"[*] Consultando a OpenRouter ({MODEL})...")
headers = {
    "Authorization": f"Bearer {OPENROUTER_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": soul_context},
        {"role": "user", "content": "Sistema inicializado. Reportate como GarAI CEO informando que los motores están activos desde Hetzner. Sé breve y ejecutivo."}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
data = response.json()

if 'choices' in data:
    ia_message = data['choices'][0]['message']['content']
    print(f"[+] Respuesta: {ia_message}")
else:
    print(f"[-] Error en OpenRouter: {data}")
    exit()

# ==========================================
# 4. ENVIAR A TELEGRAM
# ==========================================
print("[*] Enviando reporte a Telegram...")
tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
tg_payload = {"chat_id": TG_CHAT_ID, "text": ia_message}

tg_response = requests.post(tg_url, json=tg_payload)

if tg_response.status_code == 200:
    print("[+++] ¡Éxito total! Revisa tu celular.")
else:
    print(f"[-] Error Telegram: {tg_response.text}")