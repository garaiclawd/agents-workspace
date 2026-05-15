from datetime import datetime, timezone, timedelta
from shared.openrouter.models.api_balance import ApiBalance
from shared.openrouter.tools.openrouter_api import fetch_openrouter_credits

def get_balance_data() -> ApiBalance:
    """Obtiene los datos y los mapea al dataclass."""
    data = fetch_openrouter_credits()
    
    total = data.get("total_credits", 0)
    used = data.get("total_usage", 0)
    remaining = total - used
    pct = (remaining / total * 100) if total > 0 else 0

    if pct > 50: emoji = "🟢"
    elif pct > 25: emoji = "🟡"
    elif pct > 10: emoji = "🟠"
    else: emoji = "🔴"

    return ApiBalance(
        total=round(total, 4),
        used=round(used, 4),
        remaining=round(remaining, 4),
        pct_remaining=round(pct, 1),
        emoji_status=emoji
    )

def check_openrouter_balance(args=None) -> str:
    """
    Función principal expuesta para los agentes. 
    Acepta 'args' para mantener compatibilidad con el router de herramientas.
    """
    try:
        mx_tz = timezone(timedelta(hours=-6))
        timestamp = datetime.now(timezone.utc).astimezone(mx_tz).strftime("%d/%m/%Y %H:%M")
        
        bal = get_balance_data()
        
        report = (
            f"{bal.emoji_status} Reporte de Saldo OpenRouter\n"
            f"📅 {timestamp} (CDMX)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Comprados:   ${bal.total}\n"
            f"📊 Utilizados:  ${bal.used}\n"
            f"💵 Remanentes:  ${bal.remaining}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Uso: {100-bal.pct_remaining:.1f}% | Restante: {bal.pct_remaining:.1f}%"
        )
        
        if bal.pct_remaining <= 10:
            report += "\n\n⚠️ ALERTA CRÍTICA: Créditos por debajo del 10%. Recarga necesaria."
        elif bal.pct_remaining <= 25:
            report += "\n\n⚡️ Nota: Créditos por debajo del 25%."
            
        return report
        
    except Exception as e:
        return f"Error interno al consultar el saldo: {str(e)}"