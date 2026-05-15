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

load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AGENT_MODEL") 
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Memoria de corto plazo: mantiene los últimos 10 mensajes (BaseMessage)
chat_history = deque(maxlen=10) 

# ==========================================
# 2. DEFINICIÓN DEL ESTADO GLOBAL (LANGGRAPH)
# ==========================================
class EnterpriseState(TypedDict):
    # Acumulador de mensajes estándar de LangChain
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Contador para evitar bucles infinitos en ejecución de herramientas
    loop_count: int
    # ID del mensaje en Telegram para actualizar estados en vivo
    placeholder_id: int
    # Espacio preparado para inyectar contexto futuro de otros agentes
    ctxe: dict

# ==========================================
# 3. INICIALIZACIÓN DEL LLM (OPENROUTER)
# ==========================================
llm = ChatOpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
    model=MODEL,
    temperature=0.3,
    default_headers={"HTTP-Referer": "https://github.com/garaiclawd/agents-workspace"}
)

# ==========================================
# 4. FUNCIONES AUXILIARES 
# ==========================================
def get_full_context():
    """Carga la identidad, el usuario y la visión estratégica en cada prompt."""
    try:
        with open(SOUL_PATH, "r", encoding="utf-8") as f: soul = f.read()
        with open(USER_PATH, "r", encoding="utf-8") as f: user = f.read()
        
        # Agregamos la lectura de la visión
        try:
            with open(VISION_PATH, "r", encoding="utf-8") as f: vision = f.read()
        except FileNotFoundError:
            vision = "La visión aún no está definida o el archivo no se encuentra."

        return f"{soul}\n\n{user}\n\n=== VISIÓN A LARGO PLAZO ===\n{vision}"
    except Exception as e:
        return f"Error crítico cargando identidad base: {e}"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
        if res.status_code == 200:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"[-] Error enviando Telegram: {e}")
    return None

def edit_telegram(message_id, text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/editMessageText"
    try:
        res = requests.post(url, json={"chat_id": TG_CHAT_ID, "message_id": message_id, "text": text}, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[-] Error editando Telegram: {e}")
        return False

def get_system_message():
    ctx = get_full_context()
    herramientas_disponibles = ", ".join(AVAILABLE_TOOLS.keys())
    msg = (
        f"{ctx}\n\n"
        "=== PROTOCOLO DE HERRAMIENTAS ===\n"
        f"Herramientas nativas disponibles: {herramientas_disponibles}\n"
        "Para usar herramientas responde: TOOL: funcion(argumento)\n"
        "NO uses comillas triples ni bloques de código para la TOOL.\n"
        "Si vas a usar run_command, no pongas paréntesis extra dentro del comando.\n"
    )
    return SystemMessage(content=msg)

# ==========================================
# 5. NODOS DEL GRAFO (LANGGRAPH)
# ==========================================
def nodo_garai(state: EnterpriseState):
    """Nodo central de razonamiento y toma de decisiones."""
    messages = state.get("messages", [])
    
    # Inyectamos el System Prompt fresco al inicio del bloque de mensajes
    full_messages = [get_system_message()] + messages
    
    # Invocar al LLM
    try:
        response = llm.invoke(full_messages)
    except Exception as e:
        response = AIMessage(content=f"ERROR_CONEXION: {e}")

    new_count = state.get("loop_count", 0) + 1
    return {"messages": [response], "loop_count": new_count}

def nodo_herramientas(state: EnterpriseState):
    """Nodo extractor y ejecutor seguro de herramientas."""
    last_message = state["messages"][-1].content
    placeholder_id = state.get("placeholder_id")
    
    match = re.search(r"TOOL:\s*([a-zA-Z0-9_]+)\((.*?)\)", last_message, re.DOTALL)
    
    if match:
        func = match.group(1).strip()
        arg_raw = match.group(2).strip()
        
        # Limpieza de ruido heredada de tu código anterior
        for noise in ["comando=", "ruta="]:
            if arg_raw.startswith(noise): arg_raw = arg_raw.replace(noise, "", 1).strip()
        if arg_raw.startswith(('"', "'")) and arg_raw.endswith(('"', "'")):
            arg_raw = arg_raw[1:-1]
        
        print(f"[*] Ejecutando Tool: {func} | Args: {arg_raw}")
        
        if placeholder_id:
            edit_telegram(placeholder_id, f"⚙️ Ejecutando herramienta: {func}...")
        
        try:
            tool_result = AVAILABLE_TOOLS.get(func, lambda x: "Error: Herramienta no existe")(arg_raw)
        except Exception as e:
            tool_result = f"Error interno al ejecutar herramienta: {e}"
            
        return {"messages": [HumanMessage(content=f"RESULTADO: {tool_result}")]}
    else:
        return {"messages": [HumanMessage(content="Error de parseo: Usa exactamente el formato TOOL: funcion(argumento)")]}

def enrutador(state: EnterpriseState):
    """Evalúa la respuesta de GarAI y decide si ir a una herramienta o terminar."""
    last_message = state["messages"][-1].content
    loop_count = state.get("loop_count", 0)
    
    # Límite estricto de ciclos para evitar loops infinitos (equivalente a tu range(6))
    if "TOOL:" in last_message and loop_count < 6:
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

# Compilamos la aplicación de LangGraph
app = workflow.compile()

# ==========================================
# 7. MOTOR PRINCIPAL
# ==========================================
def procesar_y_responder(user_text, placeholder_id, current_history):
    print(f"[*] Procesando en hilo secundario: {user_text[:20]}...")
    
    # Preparamos el historial + nuevo mensaje usando los objetos nativos
    initial_messages = list(current_history) + [HumanMessage(content=user_text)]
    
    inputs = {
        "messages": initial_messages,
        "placeholder_id": placeholder_id,
        "loop_count": 0,
        "ctxe": {}
    }
    
    # Invocamos el Grafo (recursion_limit es una barrera de seguridad extra de LangGraph)
    final_state = app.invoke(inputs, {"recursion_limit": 15})
    
    # La respuesta final es el último mensaje en el estado
    ai_res = final_state["messages"][-1].content
    
    # Memoria transaccional: Actualizar Telegram y guardar solo si fue exitoso
    exito_envio = edit_telegram(placeholder_id, ai_res)
    
    if exito_envio:
        chat_history.append(HumanMessage(content=user_text))
        chat_history.append(AIMessage(content=ai_res))
        print("[+] Memoria de la sesión actualizada exitosamente.")
    else:
        edit_telegram(placeholder_id, "❌ Error de conexión al entregar el mensaje. La memoria está intacta, puedes repetir la pregunta.")
        print("[-] Fallo crítico de entrega. Prevención de Contexto Fantasma activada.")

def listen():
    last_update_id = 0
    print(f"[*] GarAI CEO operativo. Escuchando a Sebastian... (Modelo: {MODEL} via LangGraph)")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            try:
                updates_res = requests.get(url, timeout=35)
                updates = updates_res.json()
            except Exception:
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
                    
                    placeholder_id = send_telegram("⏳ Procesando solicitud (LangGraph Orquestando)...")
                    
                    if placeholder_id:
                        snapshot_historia = list(chat_history) 
                        hilo = threading.Thread(target=procesar_y_responder, args=(user_text, placeholder_id, snapshot_historia))
                        hilo.start()
                    
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    listen()