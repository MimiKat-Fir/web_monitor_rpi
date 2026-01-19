import os
import time
import requests

# Colores
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
        print(f"\n\n{RED}Cancelado.{RESET}")
        exit()

def paso_1_crear_bot():
    print_header()
    print(f"{YELLOW}PASO 1: TOKEN DEL BOT{RESET}")
    print("1. Abre Telegram y busca a @BotFather")
    print("2. Crea un bot con /newbot y copia el TOKEN.")

def validar_token(token):
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            bot_name = r.json()['result']['first_name']
            print(f"\n{GREEN}✅ Token válido. Bot: {bot_name}{RESET}")
            return True
        print(f"\n{RED}❌ Token inválido.{RESET}")
        return False
    except:
        return False

def paso_2_vincular(token):
    print(f"\n{YELLOW}PASO 2: VINCULAR TU CUENTA{RESET}")
    print(f"👉 {CYAN}Envía un mensaje 'Hola' a tu bot en Telegram AHORA.{RESET}")
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = 0
    
    while True:
        try:
            params = {"offset": offset, "timeout": 5}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            
            if "result" in data:
                for result in data["result"]:
                    offset = result["update_id"] + 1
                    if "message" in result:
                        msg = result["message"]
                        chat_id = msg["chat"]["id"]
                        nombre = msg["chat"].get("first_name", "Desconocido")
                        username = msg["chat"].get("username", "Sin alias")
                        
                        # CONFIRMACIÓN DEL USUARIO
                        print(f"\n{GREEN}📩 Mensaje recibido de:{RESET} {nombre} (@{username})")
                        confirmacion = input_clean(f"¿Eres tú? (Y/N): ").lower()
                        
                        if confirmacion == 'y':
                            print(f"{GREEN}✅ Identidad confirmada.{RESET}")
                            return str(chat_id)
                        else:
                            print(f"{YELLOW}⚠️ Esperando otro mensaje... Envía 'Hola' de nuevo desde tu cuenta.{RESET}")
            
            time.sleep(1)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            time.sleep(2)

def main():
    paso_1_crear_bot()
    while True:
        token = input_clean(f"\nPegue el {GREEN}TOKEN{RESET}: ")
        if len(token) > 10 and validar_token(token): break
            
    chat_id = paso_2_vincular(token)
    
    with open(".env", "w") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat_id}")
    
    print(f"\n{GREEN}✅ CONFIGURACIÓN GUARDADA.{RESET} Reiniciando...")

if __name__ == "__main__":
    main()