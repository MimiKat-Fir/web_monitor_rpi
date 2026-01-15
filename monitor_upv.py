import os
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

# CONFIGURACION MULTI-PAGINAS
ACTIVIDADES = [
    {
        "nombre": "Escalada",
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21832&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",
        "palabra_clave": "libres"
    },
    {
        "nombre": "Esgrima", 
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21833&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",
        "palabra_clave": "libres"
    },
    {
        "nombre": "Tenis de Mesa",
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21840&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",  
        "palabra_clave": "libres"
    },
    {
        "nombre": "Voley Playa", 
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21843&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad", 
        "palabra_clave": "libres"
    },
    {
        "nombre": "Pelota Valenciana",
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21838&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",  
        "palabra_clave": "libres"
    },
    {
        "nombre": "Tiro Con Arco",
        "url": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6849&p_codacti=21841&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad",  
        "palabra_clave": "libres"
    }
]

INTERVALO = 300  # segundos (5 minutos)

# LEER CREDENCIALES DESDE EL SISTEMA (No hardcoded)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def log(msg):
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"[{hora}] {msg}", flush=True)

def comprobar_pagina(nombre, url, palabra_clave):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            log(f"Error HTTP {r.status_code} en {nombre}")
            return False, None
        
        soup = BeautifulSoup(r.text, "lxml")
        texto = soup.get_text().lower()
        return palabra_clave in texto, url
    except Exception as e:
        log(f"Error al acceder a {nombre}: {e}")
        return False, None

def alerta_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("Error: No hay credenciales de Telegram configuradas.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            log("Mensaje enviado por Telegram")
        else:
            log(f"Error al enviar Telegram: {r.status_code}")
    except Exception as e:
        log(f"Excepcion al enviar Telegram: {e}")

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR CRITICO: Faltan las variables de entorno TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        print("Asegúrate de haber creado el archivo .env")
        return

    log("Monitor multi-paginas iniciado...")
    alerta_telegram("Monitor iniciado - Comenzando la monitorización...")
    
    estados_anteriores = {actividad["nombre"]: None for actividad in ACTIVIDADES}
    
    while True:
        cambios_detectados = []
        
        for actividad in ACTIVIDADES:
            nombre = actividad["nombre"]
            url = actividad["url"]
            palabra_clave = actividad["palabra_clave"]
            
            hay_libres, url_pagina = comprobar_pagina(nombre, url, palabra_clave)
            
            if hay_libres and estados_anteriores[nombre] != True:
                log(f"ALERTA! Hay plazas libres en {nombre}!")
                cambios_detectados.append(f"{nombre}: {url_pagina}")
                estados_anteriores[nombre] = True
            elif not hay_libres and estados_anteriores[nombre] != False:
                log(f"No hay plazas libres en {nombre}.")
                estados_anteriores[nombre] = False
            else:
                log(f"Sin cambios en {nombre}.")
        
        if cambios_detectados:
            mensaje = "PLAZAS LIBRES ENCONTRADAS:\n\n" + "\n".join(cambios_detectados)
            alerta_telegram(mensaje)
        
        time.sleep(INTERVALO)

if __name__ == "__main__":
    main()