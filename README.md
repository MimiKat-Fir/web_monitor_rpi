# Firas Amine's Web Monitor

### Bot de Telegram Automatizado para Raspberry Pi

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux-red?style=for-the-badge&logo=raspberrypi)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Monitoriza páginas web (Intranet UPV, reservas, citas) y recibe alertas instantáneas en tu móvil cuando haya plazas libres.**

---

## 💡 Instalación Rápida

Abre la terminal de tu Raspberry Pi (o Linux), copia el siguiente comando **completo** y pulsa Enter. El asistente se encargará de todo.

```bash
cd ~ && git clone https://github.com/MimiKat-Fir/web_monitor_rpi.git && cd web_monitor_rpi && chmod +x install.sh && ./install.sh
```

> **Nota:** Durante la instalación se te pedirá el Token de tu bot (consíguelo en @BotFather). Recuerda enviar un "Hola" a tu bot desde tu cuenta personal para que el sistema capture tu ID automáticamente.

---

## ⚙️ Gestión y Mantenimiento

Comandos rápidos para gestionar tu instalación.

### Actualizar

Si hay mejoras en el código, usa este comando para descargar los cambios y reiniciar el servicio:

```bash
cd ~/web_monitor_rpi && git pull && sudo systemctl restart webmonitor
```

### Desinstalar

Para detener el bot, borrar el servicio y eliminar los archivos:

```bash
sudo systemctl stop webmonitor && sudo systemctl disable webmonitor && sudo rm /etc/systemd/system/webmonitor.service && sudo systemctl daemon-reload && rm -rf ~/web_monitor_rpi && echo "✅ Desinstalación completada."
```

---

## 💡 Usage

Una vez activo, controla todo desde el chat con tu bot:

| Comando | Descripción |
|---------|-------------|
| `/status` | 🟢 Estado del bot, última comprobación y webs activas. |
| `/switch` | 🔄 Pausa/Reanuda la monitorización (Ideal para mantenimientos). |
| `/add` | ➕ Asistente interactivo para añadir una web. |
| `/delete` | 🗑 Menú para borrar una web de la lista. |
| `/log10` | 📜 Muestra los últimos 10 eventos/errores. |
| `/help` | ℹ️ Muestra la ayuda detallada. |

---

## 🛠️ Avanzado: Edición Manual

Si necesitas añadir muchas páginas a la vez, es más rápido editar la base de datos directamente.

1. **Abre el archivo de configuración:**

```bash
nano ~/web_monitor_rpi/actividades.json
```

2. **Edita siguiendo este formato exacto:**

```json
[
    {
        "nombre": "Escalada",
        "url": "https://www.upv.es/...",
        "palabra_clave": "libres"
    },
    {
        "nombre": "Tenis",
        "url": "https://www.upv.es/...",
        "palabra_clave": "plazas"
    }
]
```

> **⚠️ Importante:** El último elemento de la lista NO debe llevar coma final. Si la pones, el bot fallará.

3. **Guarda y Reinicia:** Pulsa `Ctrl + O`, `Enter` y `Ctrl + X`. Después, es obligatorio reiniciar el bot:

```bash
sudo systemctl restart webmonitor
```

---

## 🛠️ Compatibilidad

Diseñado para Raspberry Pi, pero funciona en cualquier sistema basado en Debian/Ubuntu.

- **Raspberry Pi:** Zero, 3, 4, 5 (Raspberry Pi OS).
- **PC/Servidor:** Ubuntu, Debian, Linux Mint.
- **Requisitos:** Python 3 y conexión a internet.

---

<div align="center">
<sub>Hecho con ❤️ para la comunidad UPV</sub>
</div>