# Nanostation M5 Status Monitor

Sistema completo para monitorear en tiempo real un Nanostation M5 de Ubiquiti.

## 🏗️ Estructura del Proyecto

```
statusNanostation/
├── server/          # Servidor Express + SQLite + Handlebars
│   ├── src/
│   │   ├── index.ts
│   │   ├── database.ts
│   │   └── types.ts
│   ├── views/
│   │   ├── layouts/
│   │   └── home.handlebars
│   ├── package.json
│   └── tsconfig.json
│
└── client/          # Cliente Python que conecta por SSH
    ├── nanostation_client.py
    └── requirements.txt
```

## 📋 Características

### Servidor
- **Express + TypeScript**: API REST robusta
- **SQLite**: Base de datos para almacenar historial
- **Handlebars**: Dashboard web con visualización en tiempo real
- **Endpoints**:
  - `GET /` - Dashboard principal
  - `POST /api/info` - Recibir datos del cliente
  - `GET /api/status` - Obtener último estado
  - `GET /api/history` - Obtener historial

### Cliente Python
- **Conexión SSH**: Se conecta automáticamente al Nanostation
- **Extracción completa de datos**:
  - ✅ Información del sistema (hostname, modelo, firmware, uptime, CPU, memoria)
  - ✅ Interfaces wireless (SSID, frecuencia, canal, potencia, CCQ)
  - ✅ Estaciones conectadas (MAC, señal, CCQ, velocidad)
  - ✅ Interfaces de red (IP, MAC, tráfico)
  - ✅ Escaneo de redes WiFi disponibles
  - ✅ Señal, ruido, RSSI en tiempo real
- **Envío automático**: Actualiza cada 30 segundos

## 🚀 Instalación y Uso

### 1. Servidor (Express)

```powershell
cd server
npm install
npm run dev
```

El servidor estará disponible en: `http://localhost:5000`

**Compilar para producción:**
```powershell
npm run build
npm start
```

### 2. Cliente (Python)

```powershell
cd client
pip install -r requirements.txt
python nanostation_client.py
```

## ⚙️ Configuración

### Cliente Python

Editar `nanostation_client.py`:

```python
NANOSTATION_IP = "192.168.1.1"          # IP del Nanostation
NANOSTATION_USER = "ubnt"                # Usuario SSH
NANOSTATION_PASSWORD = "123456789291203Er*."  # Contraseña SSH
SERVER_URL = "http://esaki-jrr.com:5000/api/info"  # URL del servidor
UPDATE_INTERVAL = 30                     # Intervalo en segundos
```

### Servidor

El puerto se puede cambiar con variable de entorno:
```powershell
$env:PORT=5000
npm start
```

## 📊 Datos Monitoreados

### Sistema
- Hostname, modelo, firmware
- Uptime, load average
- Uso de CPU y memoria

### Wireless
- SSID, modo, frecuencia, canal
- Potencia TX, señal, ruido, RSSI
- CCQ (Connection Quality)
- Ancho de canal

### Estaciones
- MAC address de clientes conectados
- Señal, ruido, RSSI, CCQ
- Velocidad TX/RX
- Tiempo de conexión

### Red
- Interfaces (eth0, wlan0, br0, etc.)
- Direcciones IP y MAC
- Tráfico RX/TX
- Errores de red

### Scan WiFi
- Redes detectadas cercanas
- Canal, frecuencia, señal
- Tipo de encriptación

## 🎨 Dashboard

El dashboard muestra:
- ✅ Estado del sistema en tiempo real
- ✅ Calidad de señal con código de colores
- ✅ Estaciones conectadas
- ✅ Gráficos de uso de memoria
- ✅ Interfaces de red
- ✅ Redes WiFi detectadas
- ✅ Auto-refresh cada 30 segundos

## 🔧 Desarrollo

### Servidor

```powershell
# Modo desarrollo (hot reload)
npm run dev

# Compilar TypeScript
npm run build

# Limpiar compilación
npm run clean
```

### Cliente

El cliente está listo para usar. Ajustar los comandos en `nanostation_client.py` si el firmware del Nanostation es diferente.

## 📝 Notas

- El cliente Python requiere acceso SSH al Nanostation
- Los comandos usados son compatibles con firmware AirOS
- El servidor guarda historial en `nanostation.db`
- Puerto por defecto: 5000

## 🐛 Troubleshooting

**Cliente no conecta:**
- Verificar IP, usuario y contraseña
- Verificar que SSH esté habilitado en el Nanostation
- Verificar conectividad de red

**Servidor no recibe datos:**
- Verificar que el servidor esté corriendo
- Verificar firewall y puertos abiertos
- Revisar URL del servidor en el cliente

**Datos incompletos:**
- Algunos comandos pueden variar según firmware
- Revisar logs del cliente para ver errores SSH

## 📄 Licencia

ISC
