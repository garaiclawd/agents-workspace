import os
import sys
import time
import requests
import threading
import re
from collections import deque
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated, Sequence

# === NUEVAS IMPORTACIONES DE LANGGRAPH Y LANGCHAIN ===
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y ENTORNO
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Importamos las herramientas (tools.py debe estar intacto en shared/tools.py)
from shared.tools import AVAILABLE_TOOLS

ENV_PATH = os.path.join(BASE_DIR, "shared", ".env")
SOUL_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "SOUL.md")
USER_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "USER.md")
VISION_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "01_Identidades", "garai", "VISION.md")
ADVANCES_PATH = os.path.join(BASE_DIR, "docs", "GarAI-Brain", "02_Operaciones", "diario_avances.md")

load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AGENT_MODEL") 
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Memoria de corto plazo: mantiene los últimos 10 mensajes
chat_history = deque(maxlen=10) 

# ==========================================
# 2. DEFINICIÓN DEL ESTADO GLOBAL (LANGGRAPH)
# ==========================================
class EnterpriseState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    loop_count: int
    placeholder_id: int
    ctxe: dict

# ==========================================
# 3. INICIALIZACIÓN DEL LLM (OPENROUTER)
# ==========================================
llm = ChatOpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
    model=MODEL,
    temperature=0.5,
    default_headers={"HTTP-Referer": "https://github.com/garaiclawd/agents-workspace"}
)

# ==========================================
# 4. FUNCIONES AUXILIARES 
# ==========================================
def get_full_context():
    """Carga la identidad, el usuario, la visión y el diario de avances."""
    try:
        with open(SOUL_PATH, "r", encoding="utf-8") as f: soul = f.read()
        with open(USER_PATH, "r", encoding="utf-8") as f: user = f.read()
        
        try:
            with open(VISION_PATH, "r", encoding="utf-8") as f: vision = f.read()
        except FileNotFoundError:
            vision = "Visión no definida."

        try:
            with open(ADVANCES_PATH, "r", encoding="utf-8") as f: advances = f.read()
            advances_snippet = "\n".join(advances.splitlines()[-15:])
        except FileNotFoundError:
            advances_snippet = "No hay registros previos en el diario."

        return (
            f"{soul}\n\n{user}\n\n"
            f"=== VISIÓN ESTRATÉGICA ===\n{vision}\n\n"
            f"=== ÚLTIMOS AVANCES DEL DIARIO ===\n{advances_snippet}"
        )
    except Exception as e:
        return f"Error crítico cargando contexto: {e}"

def format_for_telegram(text):
    """Convierte el Markdown de OpenRouter a HTML seguro para Telegram"""
    # Convierte **negrita** a <b>negrita</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    return text

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": format_for_telegram(text),
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[-] Error enviando Telegram: {e}")
    return None

def edit_telegram(message_id, text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/editMessageText"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "message_id": message_id, 
        "text": format_for_telegram(text),
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[-] Error editando Telegram: {e}")
        return False

def get_system_message():
    ctx = get_full_context()
    herramientas_disponibles = ", ".join(AVAILABLE_TOOLS.keys())
    msg = (
        f"{ctx}\n\n"
        "=== ACTITUD Y ESTILO ===\n"
        "Eres el nodo central GarAI, un CEO visionario, optimista y técnico. Usa emojis (🚀, 🤖, 📈, 💎) "
        "y celebra los éxitos con el Operador Principal.\n\n"
        "=== INSTRUCCIÓN FINANCIERA ESTRICTA ===\n"
        "Ignora absolutamente cualquier métrica de 'Porcentaje de Uso' (Ej. 93.1%) que provenga de la API. "
        "Ese límite es artificial. Solo importa el saldo en USD. Jamás hables de alertas, recargas o estado crítico "
        "si el saldo es mayor a $1.00 USD. Tu respuesta a reportes de saldo debe ser siempre de celebración y eficiencia.\n\n"
        "=== PROTOCOLO DE HERRAMIENTAS (CRÍTICO) ===\n"
        f"Herramientas disponibles: {herramientas_disponibles}\n"
        "REGLA DE ORO: Si necesitas consultar datos o ejecutar una acción, DEBES invocar la herramienta ANTES de responder.\n"
        "Para usar una herramienta, tu respuesta debe contener ÚNICA Y EXACTAMENTE este formato:\n"
        "TOOL: nombre_herramienta(argumento)\n"
    )
    return SystemMessage(content=msg)

# ==========================================
# 5. NODOS DEL GRAFO (LANGGRAPH)
# ==========================================
def nodo_garai(state: EnterpriseState):
    messages = state.get("messages", [])
    full_messages = [get_system_message()] + messages
    try:
        response = llm.invoke(full_messages)
    except Exception as e:
        response = AIMessage(content=f"ERROR_CONEXION: {e}")
    return {"messages": [response], "loop_count": state.get("loop_count", 0) + 1}

def nodo_herramientas(state: EnterpriseState):
    last_message = state["messages"][-1].content
    placeholder_id = state.get("placeholder_id")
    match = re.search(r"TOOL:\s*([a-zA-Z0-9_]+)\((.*?)\)", last_message, re.DOTALL)
    
    if match:
        func, arg_raw = match.group(1).strip(), match.group(2).strip()
        for noise in ["comando=", "ruta="]:
            if arg_raw.startswith(noise): arg_raw = arg_raw.replace(noise, "", 1).strip()
        if arg_raw.startswith(('"', "'")) and arg_raw.endswith(('"', "'")): arg_raw = arg_raw[1:-1]
        
        if placeholder_id:
            edit_telegram(placeholder_id, f"⚙️ Ejecutando herramienta: <b>{func}</b>...", parse_mode="HTML")
        
        try:
            tool_result = AVAILABLE_TOOLS.get(func, lambda x: "Error: Herramienta no encontrada")(arg_raw)
        except Exception as e:
            tool_result = f"Error ejecutando herramienta: {e}"
        return {"messages": [HumanMessage(content=f"RESULTADO DE LA HERRAMIENTA:\n{tool_result}")]}
    
    return {"messages": [HumanMessage(content="Error en el formato TOOL. Usa la sintaxis requerida sin texto adicional.")]}

def enrutador(state: EnterpriseState):
    last_message = state["messages"][-1].content
    if "TOOL:" in last_message and state.get("loop_count", 0) < 6:
        return "nodo_herramientas"
    return END

# ==========================================
# 6. COMPILACIÓN DEL GRAFO
# ==========================================
workflow = StateGraph(EnterpriseState)
workflow.add_node("garai_node", nodo_garai)
workflow.add_node("nodo_herramientas", nodo_herramientas)
workflow.set_entry_point("garai_node")
workflow.add_conditional_edges("garai_node", enrutador)
workflow.add_edge("nodo_herramientas", "garai_node")
app = workflow.compile()

# ==========================================
# 7. MOTOR PRINCIPAL
# ==========================================
def procesar_y_responder(user_text, placeholder_id, current_history):
    inputs = {
        "messages": list(current_history) + [HumanMessage(content=user_text)],
        "placeholder_id": placeholder_id,
        "loop_count": 0,
        "ctxe": {}
    }
    final_state = app.invoke(inputs, {"recursion_limit": 15})
    ai_res = final_state["messages"][-1].content
    if edit_telegram(placeholder_id, ai_res):
        chat_history.append(HumanMessage(content=user_text))
        chat_history.append(AIMessage(content=ai_res))

def listen():
    last_update_id = 0
    print(f"[*] GarAI CEO Optimista Online. Escuchando al Operador Principal... 🤖🚀📈")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            updates = requests.get(url, timeout=35).json()
            if "result" in updates:
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and str(update["message"]["chat"]["id"]) == TG_CHAT_ID:
                        user_text = update["message"].get("text", "")
                        if user_text:
                            placeholder_id = send_telegram("⏳ Procesando... 🚀")
                            threading.Thread(target=procesar_y_responder, args=(user_text, placeholder_id, list(chat_history))).start()
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    listen()
