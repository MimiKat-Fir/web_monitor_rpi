# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 11:09:30 2026

@author: firas amine
"""

import os
import time
import requests

# Colores para que sea bonito en la terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
RESET = '\033[0m'

def print_header():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}========================================{RESET}")
    print(f"{CYAN}   🤖 ASISTENTE DE CONFIGURACIÓN UPV    {RESET}")
    print(f"{CYAN}========================================{RESET}\n")

def input_clean(prompt):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print(f"\n\n{RED}Cancelado por el usuario.{RESET}")
        exit()

def paso_1_crear_bot():
    print_header()
    print(f"{YELLOW}PASO 1: CREAR EL BOT DE TELEGRAM{RESET}")
    print("Si ya tienes el Token, puedes saltar estas instrucciones.\n")
    print("1. Abre Telegram y busca a user: @BotFather")
    print("2. Envía el mensaje: /newbot")
    print("3. Ponle un nombre (ej: MonitorUPV)")
    print("4. Ponle un usuario terminado en 'bot' (ej: mi_monitor_upv_bot)")
    print(f"5. BotFather te dará un {GREEN}TOKEN{RESET} (una cadena larga de letras y números).")
    print("-" * 40)

def validar_token(token):
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            bot_name = r.json()['result']['first_name']
            print(f"\n{GREEN}✅ Token válido. Conectado con: {bot_name}{RESET}")
            return True
        else:
            print(f"\n{RED}❌ Token incorrecto. Por favor, revísalo.{RESET}")
            return False
    except Exception as e:
        print(f"\n{RED}❌ Error de conexión: {e}{RESET}")
        return False

def paso_2_obtener_chat_id(token):
    print(f"\n{YELLOW}PASO 2: VINCULAR TU CUENTA{RESET}")
    print("Para saber a quién enviar las alertas, necesito tu ID.")
    print(f"👉 {CYAN}Abre tu bot en Telegram y envíale un mensaje cualquiera (ej: 'Hola'){RESET}")
    print("Esperando mensaje... (No cierres esto)")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0
    
    # Bucle infinito hasta que reciba un mensaje
    while True:
        try:
            params = {"offset": offset, "timeout": 5}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            
            if "result" in data:
                for result in data["result"]:
                    offset = result["update_id"] + 1
                    if "message" in result:
                        chat_id = result["message"]["chat"]["id"]
                        user_name = result["message"]["chat"].get("first_name", "Usuario")
                        print(f"\n{GREEN}✅ ¡Mensaje recibido de {user_name}!{RESET}")
                        print(f"ID detectado: {chat_id}")
                        return str(chat_id)
            time.sleep(1)
        except Exception as e:
            time.sleep(2)

def guardar_configuracion(token, chat_id):
    contenido = f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat_id}"
    try:
        with open(".env", "w") as f:
            f.write(contenido)
        print(f"\n{GREEN}💾 Configuración guardada en archivo .env{RESET}")
    except Exception as e:
        print(f"{RED}Error guardando archivo: {e}{RESET}")

def main():
    paso_1_crear_bot()
    
    # Bucle para pedir Token hasta que sea válido
    token = ""
    while True:
        token = input_clean(f"\nPegue aquí el {GREEN}TOKEN{RESET} y pulse Enter: ")
        if len(token) > 10 and validar_token(token):
            break
            
    chat_id = paso_2_obtener_chat_id(token)
    
    guardar_configuracion(token, chat_id)
    
    print(f"\n{CYAN}========================================{RESET}")
    print(f"{GREEN}   🚀 ¡INSTALACIÓN COMPLETADA! 🚀      {RESET}")
    print(f"{CYAN}========================================{RESET}")
    print("El monitor se reiniciará automáticamente ahora.")

if __name__ == "__main__":
    main()