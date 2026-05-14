import os

import subprocess



def list_files(path="."):

    """Lista archivos y carpetas en una ruta específica."""

    try:

        if not path or path == ".": path = os.getcwd()

        files = os.listdir(path)

        return "\n".join(files)

    except Exception as e:

        return f"Error al listar: {str(e)}"



def read_file(path):

    """Lee el contenido de un archivo (código, logs, etc)."""

    try:

        with open(path.strip(), "r", encoding="utf-8") as f:

            return f.read()

    except Exception as e:

        return f"Error al leer archivo: {str(e)}"



def write_file(args):

    """

    Escribe o sobrescribe un archivo.

    Espera un string con el formato: ruta_del_archivo|||contenido_a_escribir

    """

    try:

        # Separamos la ruta del contenido usando |||

        path, content = args.split("|||", 1)

        path = path.strip()

       

        # Aseguramos que el directorio exista

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

       

        with open(path, "w", encoding="utf-8") as f:

            f.write(content)

        return f"Éxito: Archivo {path} guardado correctamente."

    except ValueError:

        return "Error: Formato incorrecto. Debes usar: ruta|||contenido"

    except Exception as e:

        return f"Error al escribir archivo: {str(e)}"



def run_command(command):

    """Ejecuta un comando de terminal (Linux, PM2, etc)."""

    try:

        # Aumentamos a 2000 caracteres para poder leer bien el 'pm2 status' o logs

        result = subprocess.check_output(command.strip(), shell=True, stderr=subprocess.STDOUT, text=True)

        salida = result[:2000]

        return salida if salida else "Comando ejecutado con éxito sin salida en consola."

    except subprocess.CalledProcessError as e:

        return f"Error en comando (Código {e.returncode}): {e.output[:1000]}"

    except Exception as e:

        return f"Error al ejecutar: {str(e)}"



# Diccionario para mapear nombres de herramientas a funciones reales

AVAILABLE_TOOLS = {

    "list_files": list_files,

    "read_file": read_file,

    "write_file": write_file,

    "run_command": run_command

}