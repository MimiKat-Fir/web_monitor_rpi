import os
import requests
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from collections import deque
from requests.exceptions import RequestException

# --- CONFIGURACIÓN ---
load_dotenv()
ARCHIVO_DB = "actividades.json"
INTERVALO = 180  # 3 Minutos por defecto
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- ESTADO GLOBAL ---
LOGS_MEMORIA = deque(maxlen=15)
ULTIMO_UPDATE_ID = 0
ESTADO_BOT = "IDLE"  # IDLE, PEDIR_NOMBRE, PEDIR_URL, PEDIR_CLAVE, CONFIRMAR, BORRAR
TEMP_NUEVA_ACTIVIDAD = {}
MONITOR_ACTIVO = True
HORA_ULTIMA_COMPROBACION = "Nunca"

ACTIVIDADES_DEFAULT = [{"nombre": "Escalada UPV", "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21832&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad", "palabra_clave": "libres"}]
ACTIVIDADES = []

# --- PERSISTENCIA ---
def cargar_actividades():
    global ACTIVIDADES
    if os.path.exists(ARCHIVO_DB):
        try:
            with open(ARCHIVO_DB, 'r', encoding='utf-8') as f:
                ACTIVIDADES = json.load(f)
            log(f"Cargadas {len(ACTIVIDADES)} actividades.", "SUCCESS")
        except:
            ACTIVIDADES = ACTIVIDADES_DEFAULT.copy()
    else:
        ACTIVIDADES = ACTIVIDADES_DEFAULT.copy()
        guardar_actividades()

def guardar_actividades():
    try:
        with open(ARCHIVO_DB, 'w', encoding='utf-8') as f:
            json.dump(ACTIVIDADES, f, indent=4, ensure_ascii=False)
        log("Base de datos actualizada.", "SUCCESS")
    except Exception as e:
        log(f"Error guardando DB: {e}", "ERROR")

# --- LOGGING Y MENSAJES ---
def log(msg, tipo="INFO"):
    hora = datetime.now().strftime('%H:%M:%S')
    iconos = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
    texto = f"[{hora}] {iconos.get(tipo, '🔹')} {msg}"
    print(texto, flush=True)
    LOGS_MEMORIA.append(texto)

def enviar_mensaje(msg):
    if not TELEGRAM_BOT_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

# --- WEB SCRAPING ---
def comprobar_pagina(nombre, url, palabra_clave):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MonitorBot/1.0)"}
    try:
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code != 200: return False, None
        soup = BeautifulSoup(r.text, "lxml")
        texto = soup.get_text().lower()
        return palabra_clave.lower() in texto, url
    except: return False, None

# --- COMANDOS DEL BOT ---
def enviar_ayuda():
    msg = (
        "**PANEL DE CONTROL**\n\n"
        "🟢 `/status` - Ver estado y lista de webs\n"
        "🔄 `/switch` - Pausar/Reanudar monitorización\n"
        "📜 `/log10` - Ver últimos errores/eventos\n"
        "➕ `/add` - Añadir nueva página\n"
        "🗑 `/delete` - Eliminar una página\n\n"
    )
    enviar_mensaje(msg)

def procesar_comando(texto):
    global ESTADO_BOT, TEMP_NUEVA_ACTIVIDAD, ACTIVIDADES, MONITOR_ACTIVO

    texto = texto.strip()

    # Cancelar global
    if texto == "/cancel":
        ESTADO_BOT = "IDLE"
        TEMP_NUEVA_ACTIVIDAD = {}
        enviar_mensaje("❌ Operación cancelada.")
        return

    # --- FLUJO DE BORRADO ---
    if ESTADO_BOT == "BORRAR":
        nombre_a_borrar = texto
        # Buscar insensible a mayúsculas
        actividad_encontrada = next((a for a in ACTIVIDADES if a["nombre"].lower() == nombre_a_borrar.lower()), None)
        
        if actividad_encontrada:
            ACTIVIDADES.remove(actividad_encontrada)
            guardar_actividades()
            enviar_mensaje(f"🗑 Actividad **{actividad_encontrada['nombre']}** eliminada correctamente.")
        else:
            enviar_mensaje(f"❌ No encuentro ninguna actividad llamada '{texto}'. Intenta de nuevo o usa /cancel.")
        
        ESTADO_BOT = "IDLE"
        return

    # --- FLUJO DE AÑADIR (/add) ---
    if ESTADO_BOT == "PEDIR_NOMBRE":
        TEMP_NUEVA_ACTIVIDAD["nombre"] = texto
        ESTADO_BOT = "PEDIR_URL"
        enviar_mensaje(f"📝 Nombre: **{texto}**\n🔗 Pega la **URL**:")
        return
    elif ESTADO_BOT == "PEDIR_URL":
        if not texto.startswith("http"):
            enviar_mensaje("⚠️ La URL debe empezar por `http` o `https`.")
            return
        TEMP_NUEVA_ACTIVIDAD["url"] = texto
        ESTADO_BOT = "PEDIR_CLAVE"
        enviar_mensaje("🔗 URL OK.\n🔑 Palabra clave:")
        return
    elif ESTADO_BOT == "PEDIR_CLAVE":
        TEMP_NUEVA_ACTIVIDAD["palabra_clave"] = texto
        ESTADO_BOT = "CONFIRMAR"
        resumen = json.dumps(TEMP_NUEVA_ACTIVIDAD, indent=4, ensure_ascii=False)
        enviar_mensaje(f"Confirmar:\n```json\n{resumen}\n```\nResponde **Y** o **N**.")
        return
    elif ESTADO_BOT == "CONFIRMAR":
        if texto.lower() in ["y", "si", "s"]:
            ACTIVIDADES.append(TEMP_NUEVA_ACTIVIDAD)
            guardar_actividades()
            enviar_mensaje(f"✅ **{TEMP_NUEVA_ACTIVIDAD['nombre']}** guardada.")
        else: enviar_mensaje("❌ Cancelado.")
        ESTADO_BOT = "IDLE"
        TEMP_NUEVA_ACTIVIDAD = {}
        return

    # --- COMANDOS DIRECTOS ---
    if texto == "/add":
        ESTADO_BOT = "PEDIR_NOMBRE"
        TEMP_NUEVA_ACTIVIDAD = {}
        enviar_mensaje("➕ **Añadir Web**\nEscribe el nombre identificativo:")
    
    elif texto == "/delete":
        if not ACTIVIDADES:
            enviar_mensaje("📭 La lista está vacía, no hay nada que borrar.")
            return
        
        lista_nombres = "\n".join([f"• {a['nombre']}" for a in ACTIVIDADES])
        enviar_mensaje(f"🗑 **Modo Eliminación**\nEscribe el NOMBRE exacto de la que quieras borrar:\n\n{lista_nombres}\n\n(Usa /cancel para salir)")
        ESTADO_BOT = "BORRAR"

    elif texto == "/switch":
        MONITOR_ACTIVO = not MONITOR_ACTIVO
        estado = "🟢 ACTIVADO" if MONITOR_ACTIVO else "🔴 PAUSADO"
        enviar_mensaje(f"🔄 Monitor **{estado}**.")
        if MONITOR_ACTIVO: log("Monitor reanudado manualmente.")
        else: log("Monitor pausado manualmente.")

    elif texto == "/status":
        icono = "🟢 Activo" if MONITOR_ACTIVO else "🔴 Pausado"
        lista = "\n".join([f"🔹 {a['nombre']}" for a in ACTIVIDADES]) if ACTIVIDADES else "_(Lista vacía)_"
        msg = (
            f"🤖 **STATUS SYSTEM**\n"
            f"Estado: {icono}\n"
            f"⏱ Último escaneo: {HORA_ULTIMA_COMPROBACION}\n"
            f"📋 **Webs Monitoreadas ({len(ACTIVIDADES)}):**\n"
            f"{lista}"
        )
        enviar_mensaje(msg)

    elif texto == "/log10":
        logs = "\n".join(list(LOGS_MEMORIA))
        enviar_mensaje(f"📜 **Logs Recientes:**\n```\n{logs[-4000:]}\n```")

    elif texto == "/help" or texto == "/start":
        enviar_ayuda()

    else:
        if ESTADO_BOT == "IDLE": enviar_ayuda()

def chequear_telegram():
    global ULTIMO_UPDATE_ID
    if not TELEGRAM_BOT_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": ULTIMO_UPDATE_ID + 1, "timeout": 1}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            for res in r.json().get("result", []):
                ULTIMO_UPDATE_ID = res["update_id"]
                if "message" in res and "text" in res["message"]:
                    procesar_comando(res["message"]["text"])
    except: pass

# --- MAIN LOOP ---
def main():
    if not TELEGRAM_BOT_TOKEN:
        log("Faltan credenciales.", "ERROR"); return

    cargar_actividades()
    log("Monitor iniciado.", "SUCCESS")
    enviar_mensaje(
        "👋 **¡Hola! Soy tu Monitor UPV.**\n"
        "Usa `/help` para ver qué puedo hacer.\n"
        "💡 *Tip: Puedes añadir webs manualmente editando 'actividades.json'*."
    )
    
    estados = {act["nombre"]: None for act in ACTIVIDADES}
    next_check = time.time()
    global HORA_ULTIMA_COMPROBACION

    while True:
        try:
            chequear_telegram()

            # Solo escanea si el monitor está activo y ha pasado el tiempo
            if MONITOR_ACTIVO and time.time() >= next_check:
                cambios = []
                HORA_ULTIMA_COMPROBACION = datetime.now().strftime('%H:%M %p')
                log(f"Escaneando {len(ACTIVIDADES)} webs...", "INFO")
                
                # Sincronizar estados
                for act in ACTIVIDADES:
                    if act["nombre"] not in estados: estados[act["nombre"]] = None

                for act in ACTIVIDADES:
                    nombre = act["nombre"]
                    libres, url = comprobar_pagina(nombre, act["url"], act["palabra_clave"])
                    
                    previo = estados.get(nombre)
                    if libres and previo != True:
                        log(f"¡Plazas en {nombre}!", "SUCCESS")
                        cambios.append(f"✅ **{nombre}**\n[Ir a la web]({url})")
                        estados[nombre] = True
                    elif not libres and previo != False:
                        estados[nombre] = False
                
                if cambios:
                    enviar_mensaje("🚨 **PLAZAS ENCONTRADAS**\n\n" + "\n\n".join(cambios))
                
                next_check = time.time() + INTERVALO
            
            time.sleep(1)

        except KeyboardInterrupt: break
        except Exception as e:
            log(f"Error Loop: {e}", "ERROR")
            time.sleep(5)

if __name__ == "__main__":
    main()