from datetime import datetime, timezone, timedelta

# Importaciones corregidas con la nueva ruta "Tools"
from shared.Tools.openrouter.models.api_balance import ApiBalance
from shared.Tools.openrouter.tools.openrouter_api import fetch_openrouter_credits

def get_balance_data() -> ApiBalance:
    """Obtiene los datos y los mapea al dataclass."""
    data = fetch_openrouter_credits()
    
    total = data.get("total_credits", 0)
    used = data.get("total_usage", 0)
    remaining = total - used

    # FIX: Redondeamos a 2 decimales a nivel de datos
    return ApiBalance(
        total=round(total, 2),
        used=round(used, 2),
        remaining=round(remaining, 2)
    )

def check_openrouter_balance(args=None) -> str:
    """
    Función principal expuesta para los agentes. 
    Acepta 'args' para mantener compatibilidad con el router de herramientas.
    """
    try:
        # Zona horaria fijada correctamente para CDMX
        mx_tz = timezone(timedelta(hours=-6))
        timestamp = datetime.now(timezone.utc).astimezone(mx_tz).strftime("%d/%m/%Y %H:%M")
        
        bal = get_balance_data()
        
        # FIX: Formateamos a .2f para asegurar que siempre muestre los dos ceros (Ej: $12.80)
        report = (
            f"💎 Reporte de Saldo OpenRouter\n"
            f"📅 {timestamp} (CDMX)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Comprados:   ${bal.total:.2f}\n"
            f"📊 Utilizados:  ${bal.used:.2f}\n"
            f"💵 Remanentes:  ${bal.remaining:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        
        return report
        
    except Exception as e:
        return f"Error interno al consultar el saldo: {str(e)}"