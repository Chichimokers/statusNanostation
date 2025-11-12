"""
Cliente Python para extraer información del Nanostation M5
Se conecta por SSH y envía los datos al servidor Express
"""

import paramiko
import json
import requests
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuración
NANOSTATION_IP = "192.168.1.1"
NANOSTATION_USER = "ubnt"
NANOSTATION_PASSWORD = "123456789291203Er*."
SERVER_URL = "http://esaki-jrr.com:8888/api/info"

# Intervalo de actualización en segundos
UPDATE_INTERVAL = 30


class NanostationClient:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.ssh = None
        
    def connect(self):
        """Conectar por SSH al Nanostation"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                timeout=10
            )
            print(f"✓ Conectado a {self.host}")
            return True
        except Exception as e:
            print(f"✗ Error al conectar: {e}")
            return False
    
    def execute_command(self, command: str) -> str:
        """Ejecutar comando en el Nanostation"""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            return output
        except Exception as e:
            print(f"Error ejecutando comando '{command}': {e}")
            return ""
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtener información del sistema"""
        info = {}
        
        # Hostname
        hostname = self.execute_command("uname -n").strip()
        info['hostname'] = hostname or "Nanostation-M5"
        
        # Modelo
        model = self.execute_command("cat /etc/board.info 2>/dev/null | grep board.name | cut -d= -f2").strip()
        info['model'] = model or "NanoStation M5"
        
        # Firmware
        firmware = self.execute_command("cat /etc/version").strip()
        info['firmwareVersion'] = firmware or "Unknown"
        
        # Uptime (en segundos)
        uptime_output = self.execute_command("cat /proc/uptime").strip().split()[0]
        info['uptime'] = int(float(uptime_output))
        
        # Load average
        loadavg = self.execute_command("cat /proc/loadavg").strip().split()[:3]
        info['loadAverage'] = " ".join(loadavg)
        
        # CPU usage (promedio)
        cpu_usage = self.execute_command("top -bn1 | grep 'CPU:' | awk '{print $2}'").strip()
        info['cpuUsage'] = float(cpu_usage.replace('%', '')) if cpu_usage else 0.0
        
        # Memoria
        meminfo = self.execute_command("cat /proc/meminfo")
        mem_total = re.search(r'MemTotal:\s+(\d+)', meminfo)
        mem_free = re.search(r'MemFree:\s+(\d+)', meminfo)
        
        if mem_total and mem_free:
            total = int(mem_total.group(1))
            free = int(mem_free.group(1))
            info['memoryTotal'] = total
            info['memoryFree'] = free
            info['memoryUsage'] = round(((total - free) / total) * 100, 2)
        else:
            info['memoryTotal'] = 0
            info['memoryFree'] = 0
            info['memoryUsage'] = 0
        
        return info
    
    def get_wireless_interfaces(self) -> List[Dict[str, Any]]:
        """Obtener información de interfaces wireless"""
        interfaces = []
        
        # Obtener lista de interfaces wireless
        iwconfig_output = self.execute_command("iwconfig 2>/dev/null")
        
        # Parsear iwconfig
        interface_blocks = iwconfig_output.split('\n\n')
        
        for block in interface_blocks:
            if not block.strip() or 'no wireless extensions' in block.lower():
                continue
            
            lines = block.split('\n')
            if not lines:
                continue
            
            interface = {}
            
            # Primera línea contiene nombre de interfaz
            first_line = lines[0]
            interface_name = first_line.split()[0]
            interface['interfaceName'] = interface_name
            
            # SSID
            ssid_match = re.search(r'ESSID:"([^"]*)"', block)
            interface['ssid'] = ssid_match.group(1) if ssid_match else "N/A"
            
            # Mode
            mode_match = re.search(r'Mode:(\S+)', block)
            interface['mode'] = mode_match.group(1) if mode_match else "Unknown"
            
            # Frequency
            freq_match = re.search(r'Frequency:([\d.]+)\s*GHz', block)
            if freq_match:
                interface['frequency'] = int(float(freq_match.group(1)) * 1000)
            else:
                interface['frequency'] = 0
            
            # Channel (extraer de wlanconfig)
            channel_cmd = f"iwlist {interface_name} channel 2>/dev/null | grep 'Current' | awk '{{print $5}}' | cut -d')' -f1"
            channel = self.execute_command(channel_cmd).strip()
            interface['channel'] = int(channel) if channel.isdigit() else 0
            
            # TX Power
            txpower_match = re.search(r'Tx-Power=(\d+)', block)
            interface['txPower'] = int(txpower_match.group(1)) if txpower_match else 0
            
            # Signal, Noise, RSSI (de wstutil o iwconfig)
            signal_cmd = f"wstutil {interface_name} list 2>/dev/null | tail -1"
            signal_output = self.execute_command(signal_cmd)
            
            if signal_output:
                parts = signal_output.split()
                if len(parts) >= 7:
                    interface['signal'] = int(parts[3]) if parts[3].lstrip('-').isdigit() else -95
                    interface['noise'] = int(parts[4]) if parts[4].lstrip('-').isdigit() else -95
                    interface['rssi'] = interface['signal'] - interface['noise']
                    interface['ccq'] = int(parts[6]) if parts[6].isdigit() else 0
                else:
                    interface['signal'] = -95
                    interface['noise'] = -95
                    interface['rssi'] = 0
                    interface['ccq'] = 0
            else:
                interface['signal'] = -95
                interface['noise'] = -95
                interface['rssi'] = 0
                interface['ccq'] = 0
            
            # Channel width
            interface['channelWidth'] = 20  # Por defecto 20MHz
            
            # MAC Address
            mac_match = re.search(r'Access Point: ([0-9A-Fa-f:]{17})', block)
            interface['macAddress'] = mac_match.group(1) if mac_match else "00:00:00:00:00:00"
            
            interfaces.append(interface)
        
        return interfaces
    
    def get_wireless_stations(self) -> List[Dict[str, Any]]:
        """Obtener información de estaciones conectadas"""
        stations = []
        
        # Usar wstutil para obtener lista de estaciones
        wstutil_output = self.execute_command("wstutil ath0 list 2>/dev/null")
        
        lines = wstutil_output.strip().split('\n')
        
        # Saltar encabezado
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 8:
                station = {
                    'macAddress': parts[0],
                    'signal': int(parts[3]) if parts[3].lstrip('-').isdigit() else -95,
                    'noise': int(parts[4]) if parts[4].lstrip('-').isdigit() else -95,
                    'rssi': int(parts[3]) - int(parts[4]) if parts[3].lstrip('-').isdigit() and parts[4].lstrip('-').isdigit() else 0,
                    'ccq': int(parts[6]) if parts[6].isdigit() else 0,
                    'txRate': int(parts[1]) if parts[1].isdigit() else 0,
                    'rxRate': int(parts[2]) if parts[2].isdigit() else 0,
                    'uptime': int(parts[5]) if parts[5].isdigit() else 0,
                    'distance': 0
                }
                stations.append(station)
        
        return stations
    
    def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Obtener información de interfaces de red"""
        interfaces = []
        
        # Usar ifconfig
        ifconfig_output = self.execute_command("ifconfig")
        
        # Parsear por bloques de interfaz
        interface_blocks = re.split(r'\n(?=\S)', ifconfig_output)
        
        for block in interface_blocks:
            if not block.strip():
                continue
            
            lines = block.split('\n')
            first_line = lines[0]
            
            # Nombre de interfaz
            name_match = re.match(r'^(\S+)', first_line)
            if not name_match:
                continue
            
            interface = {}
            interface['name'] = name_match.group(1)
            
            # MAC Address
            mac_match = re.search(r'HWaddr ([0-9A-Fa-f:]{17})', block)
            interface['macAddress'] = mac_match.group(1) if mac_match else "00:00:00:00:00:00"
            
            # IP Address
            ip_match = re.search(r'inet addr:(\S+)', block)
            interface['ipAddress'] = ip_match.group(1) if ip_match else "0.0.0.0"
            
            # Netmask
            mask_match = re.search(r'Mask:(\S+)', block)
            interface['netmask'] = mask_match.group(1) if mask_match else "0.0.0.0"
            
            # Broadcast
            bcast_match = re.search(r'Bcast:(\S+)', block)
            interface['broadcast'] = bcast_match.group(1) if bcast_match else ""
            
            # MTU
            mtu_match = re.search(r'MTU:(\d+)', block)
            interface['mtu'] = int(mtu_match.group(1)) if mtu_match else 1500
            
            # Status
            interface['status'] = 'up' if 'UP' in first_line else 'down'
            
            # RX/TX stats
            rx_bytes_match = re.search(r'RX bytes:(\d+)', block)
            tx_bytes_match = re.search(r'TX bytes:(\d+)', block)
            
            interface['rxBytes'] = int(rx_bytes_match.group(1)) if rx_bytes_match else 0
            interface['txBytes'] = int(tx_bytes_match.group(1)) if tx_bytes_match else 0
            
            # RX/TX packets
            rx_packets_match = re.search(r'RX packets:(\d+)', block)
            tx_packets_match = re.search(r'TX packets:(\d+)', block)
            
            interface['rxPackets'] = int(rx_packets_match.group(1)) if rx_packets_match else 0
            interface['txPackets'] = int(tx_packets_match.group(1)) if tx_packets_match else 0
            
            # Errores
            rx_errors_match = re.search(r'errors:(\d+)', block)
            interface['rxErrors'] = int(rx_errors_match.group(1)) if rx_errors_match else 0
            interface['txErrors'] = 0  # Buscar en segunda línea de errores si existe
            
            interfaces.append(interface)
        
        return interfaces
    
    def get_wireless_scan(self) -> List[Dict[str, Any]]:
        """Escanear redes WiFi disponibles"""
        networks = []
        
        # Ejecutar scan
        scan_output = self.execute_command("iwlist ath0 scan 2>/dev/null")
        
        # Parsear resultados
        cells = scan_output.split('Cell ')
        
        for cell in cells[1:]:  # Saltar primer elemento vacío
            network = {}
            
            # MAC Address (BSSID)
            mac_match = re.search(r'Address: ([0-9A-Fa-f:]{17})', cell)
            network['macAddress'] = mac_match.group(1) if mac_match else ""
            
            # SSID
            ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
            network['ssid'] = ssid_match.group(1) if ssid_match else "Hidden"
            
            # Channel
            channel_match = re.search(r'Channel:(\d+)', cell)
            network['channel'] = int(channel_match.group(1)) if channel_match else 0
            
            # Frequency
            freq_match = re.search(r'Frequency:([\d.]+)\s*GHz', cell)
            if freq_match:
                network['frequency'] = int(float(freq_match.group(1)) * 1000)
            else:
                network['frequency'] = 0
            
            # Signal
            signal_match = re.search(r'Signal level=(-?\d+)', cell)
            network['signal'] = int(signal_match.group(1)) if signal_match else -95
            
            # Quality
            quality_match = re.search(r'Quality=(\d+)/(\d+)', cell)
            if quality_match:
                network['quality'] = int((int(quality_match.group(1)) / int(quality_match.group(2))) * 100)
            else:
                network['quality'] = 0
            
            # Encryption
            if 'Encryption key:on' in cell:
                if 'WPA2' in cell:
                    network['encryption'] = "WPA2"
                elif 'WPA' in cell:
                    network['encryption'] = "WPA"
                else:
                    network['encryption'] = "WEP"
            else:
                network['encryption'] = "Open"
            
            # Mode
            mode_match = re.search(r'Mode:(\S+)', cell)
            network['mode'] = mode_match.group(1) if mode_match else "Unknown"
            
            networks.append(network)
        
        return networks[:20]  # Limitar a 20 redes
    
    def get_device_id(self) -> str:
        """Obtener ID único del dispositivo (MAC de interfaz principal)"""
        mac = self.execute_command("ifconfig br0 2>/dev/null | grep HWaddr | awk '{print $5}'").strip()
        if not mac:
            mac = self.execute_command("cat /sys/class/net/eth0/address 2>/dev/null").strip()
        return mac or "00:00:00:00:00:00"
    
    def collect_all_data(self) -> Dict[str, Any]:
        """Recopilar toda la información del Nanostation"""
        print("📊 Recopilando información del Nanostation...")
        
        data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'deviceId': self.get_device_id(),
            'system': self.get_system_info(),
            'wireless': self.get_wireless_interfaces(),
            'stations': self.get_wireless_stations(),
            'networks': self.get_network_interfaces(),
            'wirelessScan': self.get_wireless_scan()
        }
        
        print(f"✓ Datos recopilados - Device: {data['deviceId']}")
        return data
    
    def disconnect(self):
        """Cerrar conexión SSH"""
        if self.ssh:
            self.ssh.close()
            print("✓ Desconectado")


def send_to_server(data: Dict[str, Any], server_url: str) -> bool:
    """Enviar datos al servidor Express"""
    try:
        print(f"📤 Enviando datos al servidor {server_url}...")
        response = requests.post(
            server_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Datos enviados correctamente")
            return True
        else:
            print(f"✗ Error del servidor: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error al enviar datos: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Cliente Nanostation M5")
    print("=" * 60)
    print(f"Dispositivo: {NANOSTATION_IP}")
    print(f"Servidor: {SERVER_URL}")
    print(f"Intervalo: {UPDATE_INTERVAL}s")
    print("=" * 60)
    
    client = NanostationClient(NANOSTATION_IP, NANOSTATION_USER, NANOSTATION_PASSWORD)
    
    while True:
        try:
            # Conectar
            if not client.connect():
                print("⏳ Reintentando en 10 segundos...")
                time.sleep(10)
                continue
            
            # Recopilar datos
            data = client.collect_all_data()
            
            # Enviar al servidor
            send_to_server(data, SERVER_URL)
            
            # Desconectar
            client.disconnect()
            
            # Esperar para próxima actualización
            print(f"\n⏰ Próxima actualización en {UPDATE_INTERVAL} segundos...\n")
            time.sleep(UPDATE_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Detenido por el usuario")
            client.disconnect()
            break
        except Exception as e:
            print(f"✗ Error inesperado: {e}")
            client.disconnect()
            time.sleep(10)


if __name__ == "__main__":
    main()
