#!/bin/bash

# Script de instalación automática para Web Monitor RPi

echo "--- 1. Actualizando sistema e instalando dependencias ---"
sudo apt update
sudo apt install -y python3-venv python3-pip git

echo "--- 2. Creando entorno virtual Python ---"
# Si ya existe, no lo borra, solo lo usa
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Entorno virtual creado."
else
    echo "El entorno virtual ya existía."
fi

# Activar e instalar librerías
source venv/bin/activate
pip install -r requirements.txt

echo "--- 3. Configurando Servicio Systemd (Arranque automático) ---"
# Variables dinámicas
USER_NAME=$(whoami)
WORK_DIR=$(pwd)
PYTHON_EXEC="$WORK_DIR/venv/bin/python3"
SCRIPT_PATH="$WORK_DIR/monitor.py"

# Contenido del archivo de servicio
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

# Escribir el archivo en /etc/systemd/system/
echo "$SERVICE_CONTENT" | sudo tee /etc/systemd/system/webmonitor.service > /dev/null

echo "--- 4. Activando servicio ---"
sudo systemctl daemon-reload
sudo systemctl enable webmonitor.service
sudo systemctl restart webmonitor.service

echo "✅ Instalación completada. El monitor debería estar corriendo."
echo "IMPORTANTE: Asegúrate de haber creado el archivo .env con tus claves antes de verificar el log."