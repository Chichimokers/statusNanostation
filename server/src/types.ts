// Tipos para Nanostation M5
export interface WirelessInterface {
  interfaceName: string; // ej: ath0, wlan0
  ssid: string;
  mode: string; // Station, Access Point, etc.
  frequency: number; // MHz
  channel: number;
  channelWidth: number; // MHz (20, 40, 80, etc.)
  txPower: number; // dBm
  rssi: number; // dBm
  noise: number; // dBm
  signal: number; // dBm
  ccq: number; // %
  macAddress: string;
  connectedStations?: number;
}

export interface WirelessStation {
  macAddress: string;
  signal: number; // dBm
  noise: number; // dBm
  rssi: number; // dBm
  ccq: number; // %
  txRate: number; // Mbps
  rxRate: number; // Mbps
  uptime: number; // seconds
  distance: number; // meters (if available)
  lastIp?: string;
}

export interface NetworkInterface {
  name: string; // eth0, eth1, br0, etc.
  macAddress: string;
  ipAddress: string;
  netmask: string;
  broadcast?: string;
  mtu: number;
  status: string; // up/down
  rxBytes: number;
  txBytes: number;
  rxPackets: number;
  txPackets: number;
  rxErrors: number;
  txErrors: number;
}

export interface SystemInfo {
  hostname: string;
  model: string;
  firmwareVersion: string;
  uptime: number; // seconds
  loadAverage: string;
  cpuUsage: number; // %
  memoryTotal: number; // KB
  memoryFree: number; // KB
  memoryUsage: number; // %
}

export interface WirelessScan {
  ssid: string;
  macAddress: string;
  channel: number;
  frequency: number;
  signal: number; // dBm
  quality: number;
  encryption: string;
  mode: string;
}

export interface AirMaxInfo {
  enabled: boolean;
  quality: number;
  capacity: number;
  priority: number;
}

export interface GpsInfo {
  latitude?: number;
  longitude?: number;
  altitude?: number;
  satellites?: number;
}

export interface NanostationStatus {
  timestamp: string; // ISO format
  deviceId: string; // MAC address or serial
  system: SystemInfo;
  wireless: WirelessInterface[];
  stations: WirelessStation[];
  networks: NetworkInterface[];
  wirelessScan?: WirelessScan[];
  airmax?: AirMaxInfo;
  gps?: GpsInfo;
  routes?: string[];
  arp?: Array<{ ip: string; mac: string; device: string }>;
}
