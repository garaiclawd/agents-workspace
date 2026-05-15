from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class EnterpriseState(TypedDict):
    # 1. El canal de comunicación: Acumula los prompts y las respuestas de los modelos.
    # El 'operator.add' asegura que los mensajes nuevos se sumen al historial, no que lo sobrescriban.
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # 2. CTXE Real: El "Cerebro Vivo". 
    # Aquí puedes inyectar partes de VISION.md, el uso de CPU de Hetzner o cotizaciones de Polymarket.
    # Los agentes pueden leer y actualizar este diccionario sin ensuciar el historial de chat.
    ctxe: dict
    
    # 3. Control de Flujo: Indica quién debe tomar la siguiente acción (ej. "sudo", "roi-berto", "end").
    next_agent: str