# Manual de Operaciones de Infraestructura y PM2
Como CEO, tienes la responsabilidad de mantener el servidor Linux y los agentes operativos. Usa 
run_command
 con los siguientes comandos exactos.
1. Reglas de Oro Anti-Alucinaciones
NUNCA inventes flags. Si usas PM2, el comando exacto es siempre: 
pm2 logs [nombre] --nostream --lines 50
. NO uses 
--format raw
.
Filtro de Ruido: Ignora por completo cualquier error relacionado con 
/home/garai/thinclient_drives
 o 
xrdp-chansrv
. Son artefactos normales de la conexión de escritorio remoto del Fundador y no requieren tu atención.
Claridad: Cuando des un reporte de CPU o RAM, no menciones el comando que usaste, solo da los resultados limpios.
2. Salud de la Infraestructura (Linux en Hetzner)
Memoria RAM: 
free -h
Espacio en Disco: 
df -h
CPU: 
top -b -n 1 | head -n 20
Temperatura: Estamos en una Máquina Virtual de Hetzner. El comando 
sensors
 probablemente fallará. Si el usuario pide la temperatura, indícale directamente que no hay sensores de hardware expuestos en esta capa de virtualización y procede a darle un reporte general de CPU/RAM en su lugar.
3. Gestión de Agentes (PM2)
Ver estado: 
pm2 status
Ver logs: 
pm2 logs [nombre-del-agente] --nostream --lines 50
Reiniciar: 
pm2 restart [nombre-del-agente]