# Manual de Operaciones de Infraestructura y PM2

Como CEO, tienes la responsabilidad de mantener el servidor Linux y los agentes operativos. Usa `run_command` con los siguientes comandos exactos cuando Sebastian te pida un reporte o una acción:

## 1. Gestión de Agentes (PM2)
Todos los agentes (Sudo, ROI-berto, Lana, etc.) corren en PM2.
*   **Ver estado de todos los agentes:** `pm2 status`
*   **Ver logs de un agente:** `pm2 logs [nombre-del-agente] --nostream --lines 50`
*   **Reiniciar un agente:** `pm2 restart [nombre-del-agente]`
*   **Frenar un agente:** `pm2 stop [nombre-del-agente]`

## 2. Salud de la Infraestructura (Linux)
*   **Ver uso de Memoria RAM:** `free -h`
*   **Ver espacio en Disco:** `df -h`
*   **Ver procesos que más CPU consumen:** `top -b -n 1 | head -n 20`
*   **Ver temperatura (si aplica):** `sensors`

## 3. Tareas Programadas (Cron)
*   **Leer el cron del usuario:** `crontab -l`
*   *(Para editar el cron, es mejor leerlo primero, guardarlo en un archivo temporal, modificarlo y cargarlo con `crontab archivo_temporal`)*.

## 4. Gestión del Conocimiento (Archivos .md)
Cuando Sebastian te pida actualizar información, usa `read_file` para leer el archivo actual, analiza qué debe cambiar, y usa `write_file` para sobrescribirlo con la información actualizada.

## 5. Gestión de Versiones (GitHub)
Para respaldar el trabajo en la nube, usa estos comandos en orden:
1. `git add .`
2. `git commit -m "Descripción clara del cambio hecho por GarAI"`
3. `git push origin [tu-rama]` (ej. git push origin main)

REGLA: Solo haz push después de haber verificado que los cambios no rompen el listener (usando pm2 status).