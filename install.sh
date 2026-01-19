#!/bin/bash

# ==========================================
# SCRIPT DE INSTALACIÓN AUTOMÁTICA - MONITOR UPV
# ==========================================

# 1. Instalar dependencias del sistema
echo "📦 --- 1. Actualizando sistema e instalando dependencias ---"
sudo apt update
sudo apt install -y python3-venv python3-pip git

# 2. Configurar entorno virtual Python
echo "🐍 --- 2. Configurando entorno virtual Python ---"
# Si ya existe, no lo borra, solo lo usa
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Entorno virtual creado."
else
    echo "ℹ️ El entorno virtual ya existía."
fi

# Activar e instalar librerías dentro del entorno
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "⬇️ Instalando librerías desde requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ ERROR: No se encuentra requirements.txt. Asegúrate de haber subido todos los archivos."
    exit 1
fi

# 3. EJECUTAR EL ASISTENTE DE CONFIGURACIÓN (INTERACTIVO)
echo "🤖 --- 3. Iniciando Asistente de Configuración ---"
# Esto lanzará el script de Python para pedir el Token y detectar el ID
python3 setup_wizard.py

# Verificamos si se creó el archivo .env correctamente
if [ ! -f ".env" ]; then
    echo "❌ ERROR: No se ha creado el archivo de configuración .env."
    echo "La instalación se detendrá aquí porque el bot no puede funcionar sin claves."
    exit 1
fi

# 4. Configurar servicio Systemd (Arranque automático)
echo "⚙️ --- 4. Configurando arranque automático (Systemd) ---"

# Variables dinámicas para rutas absolutas
USER_NAME=$(whoami)
WORK_DIR=$(pwd)
PYTHON_EXEC="$WORK_DIR/venv/bin/python3"
SCRIPT_PATH="$WORK_DIR/monitor.py"

# Contenido del servicio
SERVICE_CONTENT="[Unit]
Description=Monitor Web Actividades UPV
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$WORK_DIR
ExecStart=$PYTHON_EXEC $SCRIPT_PATH
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"

# Escribir el archivo de servicio
echo "$SERVICE_CONTENT" | sudo tee /etc/systemd/system/webmonitor.service > /dev/null

# 5. Activar y arrancar el servicio
echo "🚀 --- 5. Iniciando el Monitor ---"
sudo systemctl daemon-reload
sudo systemctl enable webmonitor.service
sudo systemctl restart webmonitor.service

echo ""
echo "✅ ¡INSTALACIÓN COMPLETADA CON ÉXITO!"
echo "El bot ya está corriendo en segundo plano."
echo "Puedes ver los logs con: sudo journalctl -u webmonitor -f"