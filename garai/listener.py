import os
import sys
import time
import requests
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y ENTORNO
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from shared.tools import AVAILABLE_TOOLS

ENV_PATH = os.path.join(BASE_DIR, "shared", ".env")
SOUL_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "SOUL.md.md")
USER_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "USER.md.md")

load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AGENT_MODEL") 
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_full_context():
    try:
        with open(SOUL_PATH, "r", encoding="utf-8") as f: soul = f.read()
        with open(USER_PATH, "r", encoding="utf-8") as f: user = f.read()
        return f"{soul}\n\n{user}"
    except Exception as e:
        return f"Error cargando identidad: {e}"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"[-] Error enviando Telegram: {e}")

def ask_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/garaiclawd/agents-workspace"
    }
    payload = {"model": MODEL, "messages": messages, "temperature": 0.3}
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return f"ERROR_API_{response.status_code}"
        res_json = response.json()
        content = res_json.get('choices', [{}])[0].get('message', {}).get('content')
        return str(content) if content else "ERROR_VACIO"
    except Exception as e:
        return "ERROR_CONEXION"

def listen():
    last_update_id = 0
    print(f"[*] GarAI CEO operativo. Escuchando a Sebastian... (Modelo: {MODEL})")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            # --- MEJORA DE ESTABILIDAD ---
            try:
                updates_res = requests.get(url, timeout=35)
                updates_res.raise_for_status()
                updates = updates_res.json()
            except requests.exceptions.RequestException as e:
                print(f"[-] Error de red en Telegram: {e}")
                time.sleep(5)
                continue
            # -----------------------------

            if "result" in updates:
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" not in update or str(update["message"]["chat"]["id"]) != TG_CHAT_ID:
                        continue
                    user_text = update["message"].get("text", "")
                    if not user_text: continue

                    print(f"\n[+] Sebastian: {user_text}")
                    system_msg = (
                        f"{get_full_context()}\n\n"
                        "=== PROTOCOLO DE HERRAMIENTAS Y ENTORNO ===\n"
                        f"Ruta raíz del workspace: {BASE_DIR}\n"
                        "Eres el CEO de este servidor Linux. Tienes acceso completo a la infraestructura.\n\n"
                        "Para usar herramientas, DEBES incluir el formato: TOOL: funcion(argumento)\n"
                        "REGLA DE ORO: Solo una herramienta por mensaje. Si necesitas varios comandos, únelos con '&&'.\n"
                        "Herramientas: list_files, read_file, write_file, run_command.\n"
                        f"Si necesitas gestionar infra, lee tu manual en: {os.path.join(BASE_DIR, 'docs', 'GarAI-Brain', '02_Operaciones', 'SYSADMIN.md')}"
                    )
                    
                    messages = [{"role": "system", "content": system_msg}, {"role": "user", "content": user_text}]

                    for i in range(6):
                        ai_res = ask_openrouter(messages)
                        if "ERROR" in ai_res:
                            send_telegram(f"❌ Error cerebral: {ai_res}")
                            break

                        if "TOOL:" in ai_res:
                            try:
                                tool_index = ai_res.find("TOOL:")
                                call = ai_res[tool_index:].replace("TOOL:", "").strip()
                                func = call.split("(")[0].strip()
                                arg_raw = call[call.find("(")+1 : call.rfind(")")].strip()
                                
                                # Limpieza de ruidos de la IA
                                for noise in ["comando=", "ruta="]:
                                    if arg_raw.startswith(noise): arg_raw = arg_raw.replace(noise, "", 1).strip()
                                if arg_raw.startswith(('"', "'")) and arg_raw.endswith(('"', "'")):
                                    arg_raw = arg_raw[1:-1]
                                
                                tool_result = AVAILABLE_TOOLS.get(func, lambda x: "Error")(arg_raw if arg_raw else ".")
                                messages.append({"role": "assistant", "content": ai_res})
                                messages.append({"role": "user", "content": f"RESULTADO: {tool_result}\n\nAnaliza y responde o sigue con otra TOOL."})
                                continue 
                            except Exception: continue
                        else:
                            send_telegram(ai_res)
                            break
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    listen()