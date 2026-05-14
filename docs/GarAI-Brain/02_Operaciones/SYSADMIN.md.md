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

## 5. Respaldo en GitHub (Autónomo)
Para subir cambios al repositorio, usa siempre esta secuencia de comandos en un solo `run_command`:
*   **Comando:** `git add . && git commit -m "Update by GarAI: [Descripción]" && git push origin main`

REGLA: Siempre verifica que el `pm2 status` esté en verde antes de hacer un push de archivos de código (`.py`).