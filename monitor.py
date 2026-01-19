import os
import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from collections import deque
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

# --- CARGA DE VARIABLES Y CONFIGURACIÓN ---
load_dotenv()

ARCHIVO_DB = "actividades.json"
INTERVALO = 100
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOGS_MEMORIA = deque(maxlen=15)
ULTIMO_UPDATE_ID = 0
ESTADO_BOT = "IDLE"
TEMP_NUEVA_ACTIVIDAD = {}

ACTIVIDADES_DEFAULT = [
    {
        "nombre": "Escalada",
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21832&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",
        "palabra_clave": "libres"
    }
]
ACTIVIDADES = []

# --- HERRAMIENTAS DE LOGGING ---
def log(msg, tipo="INFO"):
    # Tipos: INFO, WARN, ERROR, SUCCESS
    hora = datetime.now().strftime('%H:%M:%S')
    iconos = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
    icono = iconos.get(tipo, "🔹")
    
    texto_log = f"[{hora}] {icono} {msg}"
    print(texto_log, flush=True)
    LOGS_MEMORIA.append(texto_log)

def enviar_mensaje(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("No se puede enviar mensaje: Faltan credenciales", "ERROR")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            log(f"Telegram rechazó el mensaje: {r.status_code} - {r.text}", "ERROR")
    except Exception as e:
        log(f"Fallo de conexión al enviar mensaje Telegram: {e}", "ERROR")

# --- PERSISTENCIA DE DATOS ---
def cargar_actividades():
    global ACTIVIDADES
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, 'r', encoding='utf-8') as f:
                ACTIVIDADES = json.load(f)
            log(f"Base de datos cargada: {len(ACTIVIDADES)} actividades.", "SUCCESS")
        except json.JSONDecodeError:
            log("El archivo JSON está corrupto o mal formado. Usando lista por defecto.", "ERROR")
            ACTIVIDADES = ACTIVIDADES_DEFAULT.copy()
        except Exception as e:
            log(f"Error desconocido leyendo archivo: {e}", "ERROR")
            ACTIVIDADES = ACTIVIDADES_DEFAULT.copy()
    else:
        log("No se encontró archivo de base de datos. Creando uno nuevo...", "WARN")
        ACTIVIDADES = ACTIVIDADES_DEFAULT.copy()
        guardar_actividades()

def guardar_actividades():
    try:
        with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
            json.dump(ACTIVIDADES, f, indent=4, ensure_ascii=False)
        log("Base de datos guardada correctamente.", "SUCCESS")
    except PermissionError:
        log("Error de permisos: No puedo escribir en el archivo JSON.", "ERROR")
    except Exception as e:
        log(f"Error crítico guardando JSON: {e}", "ERROR")

# --- MONITORIZACIÓN WEB ---
def comprobar_pagina(nombre, url, palabra_clave):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MonitorBot/1.0)"}
    try:
        r = requests.get(url, timeout=20, headers=headers)
        r.raise_for_status() # Esto lanza error si es 404, 500, etc.
        
        soup = BeautifulSoup(r.text, "lxml")
        texto = soup.get_text().lower()
        return palabra_clave.lower() in texto, url

    except HTTPError as e:
        log(f"La web de {nombre} devolvió error HTTP: {e.response.status_code}", "ERROR")
        return False, None
    except ConnectionError:
        log(f"Fallo de conexión en {nombre}. ¿Hay internet? ¿Web caída?", "ERROR")
        return False, None
    except Timeout:
        log(f"La web de {nombre} tardó demasiado en responder (Timeout).", "WARN")
        return False, None
    except RequestException as e:
        log(f"Error genérico de red en {nombre}: {e}", "ERROR")
        return False, None
    except Exception as e:
        log(f"Error interno procesando {nombre}: {e}", "ERROR")
        return False, None

# --- LÓGICA DEL BOT ---
def procesar_comando(texto):
    global ESTADO_BOT, TEMP_NUEVA_ACTIVIDAD, ACTIVIDADES
    texto = texto.strip()

    if texto == "/cancel":
        ESTADO_BOT = "IDLE"
        TEMP_NUEVA_ACTIVIDAD = {}
        enviar_mensaje("🚫 Operación cancelada.")
        return

    # MÁQUINA DE ESTADOS (/add)
    if ESTADO_BOT == "PEDIR_NOMBRE":
        TEMP_NUEVA_ACTIVIDAD["nombre"] = texto
        ESTADO_BOT = "PEDIR_URL"
        enviar_mensaje(f"📝 Nombre: **{texto}**\n🔗 Pega la **URL**:")
        return

    elif ESTADO_BOT == "PEDIR_URL":
        if not texto.startswith("http"):
            enviar_mensaje("⚠️ Error: La URL debe empezar por `http` o `https`.")
            return
        TEMP_NUEVA_ACTIVIDAD["url"] = texto
        ESTADO_BOT = "PEDIR_CLAVE"
        enviar_mensaje("🔗 URL OK.\n🔑 Palabra clave (ej: `libres`):")
        return

    elif ESTADO_BOT == "PEDIR_CLAVE":
        TEMP_NUEVA_ACTIVIDAD["palabra_clave"] = texto
        ESTADO_BOT = "CONFIRMAR"
        resumen = json.dumps(TEMP_NUEVA_ACTIVIDAD, indent=4, ensure_ascii=False)
        enviar_mensaje(f"🔍 Confirmar:\n```json\n{resumen}\n```\nResponde **Y** o **N**.")
        return

    elif ESTADO_BOT == "CONFIRMAR":
        if texto.lower() in ["y", "si", "s"]:
            ACTIVIDADES.append(TEMP_NUEVA_ACTIVIDAD)
            guardar_actividades()
            enviar_mensaje(f"✅ **{TEMP_NUEVA_ACTIVIDAD['nombre']}** guardada.")
        else:
            enviar_mensaje("❌ Cancelado.")
        ESTADO_BOT = "IDLE"
        TEMP_NUEVA_ACTIVIDAD = {}
        return

    # COMANDOS
    if texto == "/add":
        ESTADO_BOT = "PEDIR_NOMBRE"
        TEMP_NUEVA_ACTIVIDAD = {}
        enviar_mensaje("➕ **Añadir Web**\nNombre de la actividad:")
    elif texto == "/status":
        enviar_mensaje(f"🤖 **STATUS**\n✅ Online\n📋 Webs: {len(ACTIVIDADES)}")
    elif texto == "/log10":
        logs = "\n".join(list(LOGS_MEMORIA))
        enviar_mensaje(f"📜 **Logs:**\n```\n{logs[-4000:]}\n```")
    elif texto == "/help":
        enviar_mensaje("Comandos: /status, /log10, /add, /cancel")
    else:
        if ESTADO_BOT == "IDLE":
            enviar_mensaje("❓ No entiendo. Usa /help")

def chequear_telegram():
    global ULTIMO_UPDATE_ID
    if not TELEGRAM_BOT_TOKEN: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": ULTIMO_UPDATE_ID + 1, "timeout": 2}
    
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            datos = r.json()
            for res in datos.get("result", []):
                ULTIMO_UPDATE_ID = res["update_id"]
                if "message" in res and "text" in res["message"]:
                    txt = res["message"]["text"]
                    user = res["message"].get("from", {}).get("first_name", "?")
                    log(f"Mensaje de {user}: {txt}", "INFO")
                    procesar_comando(txt)
        elif r.status_code == 409:
            log("Conflicto Telegram: ¿Hay otro bot corriendo con el mismo token?", "ERROR")
        elif r.status_code == 401:
            log("Error Telegram: Token inválido (Unauthorized)", "ERROR")
            
    except ConnectionError:
        # No logueamos error cada segundo si se va internet para no llenar el log
        pass 
    except Exception as e:
        log(f"Error chequeando Telegram: {e}", "ERROR")

# --- BUCLE PRINCIPAL ---
def main():
    if not TELEGRAM_BOT_TOKEN:
        log("Falta TOKEN en .env", "ERROR")
        return

    cargar_actividades()
    log("Monitor iniciado.", "SUCCESS")
    enviar_mensaje("🤖 **Monitor Reiniciado**")
    
    estados = {act["nombre"]: None for act in ACTIVIDADES}
    next_check = time.time()
    
    while True:
        try:
            chequear_telegram()

            if time.time() >= next_check:
                cambios = []
                log("Escaneando webs...", "INFO")
                
                # Actualizar lista de estados por si hay nuevas actividades
                for act in ACTIVIDADES:
                    if act["nombre"] not in estados: estados[act["nombre"]] = None

                for act in ACTIVIDADES:
                    nombre = act["nombre"]
                    libres, url = comprobar_pagina(nombre, act["url"], act["palabra_clave"])
                    
                    previo = estados.get(nombre)
                    if libres and previo != True:
                        log(f"¡Plazas en {nombre}!", "SUCCESS")
                        cambios.append(f"✅ **{nombre}**\n{url}")
                        estados[nombre] = True
                    elif not libres and previo != False:
                        estados[nombre] = False
                
                if cambios:
                    enviar_mensaje("🚨 **PLAZAS ENCONTRADAS**\n\n" + "\n".join(cambios))
                
                next_check = time.time() + INTERVALO
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            log("Deteniendo bot...", "WARN")
            break
        except Exception as e:
            log(f"Error inesperado en main: {e}", "ERROR")
            time.sleep(5)

if __name__ == "__main__":
    main()