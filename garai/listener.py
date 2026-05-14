import os
import sys
import time
import requests
import threading
import re
from collections import deque
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y ENTORNO
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Importamos las herramientas (tools.py debe estar intacto en shared/tools.py)
from shared.tools import AVAILABLE_TOOLS

ENV_PATH = os.path.join(BASE_DIR, "shared", ".env")
SOUL_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "SOUL.md.md")
USER_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "USER.md.md")

load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AGENT_MODEL") 
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Memoria de corto plazo: mantiene los últimos 10 mensajes (5 intercambios)
chat_history = deque(maxlen=10) 

def get_full_context():
    try:
        with open(SOUL_PATH, "r", encoding="utf-8") as f: soul = f.read()
        with open(USER_PATH, "r", encoding="utf-8") as f: user = f.read()
        return f"{soul}\n\n{user}"
    except Exception as e:
        return f"Error cargando identidad: {e}"

def send_telegram(text):
    """Envía un mensaje nuevo y devuelve su ID para poder editarlo luego."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
        if res.status_code == 200:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[-] Error enviando Telegram: {e}")
    return None

def edit_telegram(message_id, text):
    """Edita un mensaje existente."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/editMessageText"
    try:
        res = requests.post(url, json={"chat_id": TG_CHAT_ID, "message_id": message_id, "text": text}, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[-] Error editando Telegram: {e}")
        return False

def ask_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/garaiclawd/agents-workspace"
    }
    payload = {"model": MODEL, "messages": messages, "temperature": 0.3}
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res_json = response.json()
        content = res_json.get('choices', [{}])[0].get('message', {}).get('content')
        return str(content) if content else "ERROR_VACIO"
    except Exception as e:
        return "ERROR_CONEXION"

def procesar_y_responder(user_text, placeholder_id, current_history):
    print(f"[*] Procesando en hilo secundario: {user_text[:20]}...")
    
    system_msg = (
        f"{get_full_context()}\n\n"
        "=== PROTOCOLO DE HERRAMIENTAS ===\n"
        "Para usar herramientas responde: TOOL: funcion(argumento)\n"
        "NO uses comillas triples ni bloques de código para la TOOL.\n"
        "Si vas a usar run_command, no pongas paréntesis extra dentro del comando.\n"
    )
    
    messages = [{"role": "system", "content": system_msg}]
    for msg in current_history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    ai_res = "ERROR_INTERNO"
    
    # Bucle de herramientas (máximo 6 encadenamientos)
    for i in range(6):
        ai_res = ask_openrouter(messages)
        
        if "TOOL:" in ai_res:
            try:
                # [FIX REGEX]: Extracción limpia de la herramienta ignorando texto basura
                match = re.search(r"TOOL:\s*([a-zA-Z0-9_]+)\((.*?)\)", ai_res, re.DOTALL)
                
                if match:
                    func = match.group(1).strip()
                    arg_raw = match.group(2).strip()
                    
                    # Limpiamos basura común que el modelo a veces inyecta
                    for noise in ["comando=", "ruta="]:
                        if arg_raw.startswith(noise): arg_raw = arg_raw.replace(noise, "", 1).strip()
                    if arg_raw.startswith(('"', "'")) and arg_raw.endswith(('"', "'")):
                        arg_raw = arg_raw[1:-1]
                    
                    print(f"[*] Ejecutando Tool: {func} | Args: {arg_raw}")
                    
                    # Llamada a la herramienta de tools.py
                    tool_result = AVAILABLE_TOOLS.get(func, lambda x: "Error: Herramienta no existe")(arg_raw)
                    
                    # Agregamos los pasos al historial del modelo para que siga razonando
                    messages.append({"role": "assistant", "content": ai_res})
                    messages.append({"role": "user", "content": f"RESULTADO: {tool_result}"})
                    
                    edit_telegram(placeholder_id, f"⚙️ Ejecutando herramienta: {func}...")
                    continue 
                else:
                    # Si detecta "TOOL:" pero el formato está mal
                    messages.append({"role": "user", "content": "Error de parseo: Usa exactamente el formato TOOL: funcion(argumento)"})
                    continue
                    
            except Exception as e:
                messages.append({"role": "user", "content": f"Error interno en parser: {e}"})
                continue
        else:
            # Si no hay herramienta, es la respuesta final de texto
            break

    # [MEMORIA TRANSACCIONAL]: Solo guardamos si Telegram confirma la entrega
    exito_envio = edit_telegram(placeholder_id, ai_res)
    
    if exito_envio:
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": ai_res})
        print("[+] Memoria de la sesión actualizada exitosamente.")
    else:
        edit_telegram(placeholder_id, "❌ Error de conexión al entregar el mensaje. La memoria está intacta, puedes repetir la pregunta.")
        print("[-] Fallo crítico de entrega. Prevención de Contexto Fantasma activada.")


def listen():
    last_update_id = 0
    print(f"[*] GarAI CEO operativo. Escuchando a Sebastian... (Modelo: {MODEL})")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            try:
                updates_res = requests.get(url, timeout=35)
                updates = updates_res.json()
            except Exception as e:
                time.sleep(5)
                continue

            if "result" in updates:
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" not in update or str(update["message"]["chat"]["id"]) != TG_CHAT_ID:
                        continue
                    
                    user_text = update["message"].get("text", "")
                    if not user_text: continue

                    print(f"\n[+] Sebastian: {user_text}")
                    
                    # 1. RESPUESTA PROVISIONAL instantánea para evitar timeouts
                    placeholder_id = send_telegram("⏳ Procesando solicitud...")
                    
                    # 2. Hilo secundario para trabajo pesado
                    if placeholder_id:
                        snapshot_historia = list(chat_history) 
                        hilo = threading.Thread(target=procesar_y_responder, args=(user_text, placeholder_id, snapshot_historia))
                        hilo.start()
                    
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    listen()