#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Manager Module

This module handles all network-related functionality including:
- WiFi connection management
- MQTT client
- mDNS service
"""

import os
import json
import time
import logging
import threading
import subprocess
import socket
import paho.mqtt.client as mqtt
from zeroconf import ServiceInfo, Zeroconf

class NetworkManager:
    """Network Manager class for managing network-related functionality"""
    
    def __init__(self, app):
        """Initialize the Network Manager
        
        Args:
            app: Main application instance
        """
        self.app = app
        self.logger = logging.getLogger('NetworkManager')
        
        # WiFi connection state
        self.wifi_connected = False
        self.current_ssid = ""
        self.wifi_rssi = 0
        
        # MQTT client
        self.mqtt_client = None
        self.mqtt_connected = False
        
        # mDNS service
        self.zeroconf = None
        self.mdns_info = None
        
        # WiFi watchdog thread
        self.wifi_watchdog_thread = None
        
        # MQTT thread
        self.mqtt_thread = None
        
        # Running state
        self.running = False
    
    def start(self):
        """Start the Network Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start WiFi connection
        self._connect_wifi()
        
        # Start WiFi watchdog thread
        self.wifi_watchdog_thread = threading.Thread(target=self._wifi_watchdog_loop)
        self.wifi_watchdog_thread.daemon = True
        self.wifi_watchdog_thread.start()
        
        # Start mDNS service
        self._start_mdns()
        
        # Start MQTT client if enabled
        if self.app.system_manager.get_config('network', 'mqtt', 'enabled', False):
            self._start_mqtt()
        
        self.logger.info("Network Manager started")
    
    def stop(self):
        """Stop the Network Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop MQTT client
        self._stop_mqtt()
        
        # Stop mDNS service
        self._stop_mdns()
        
        # Wait for threads to terminate
        if self.wifi_watchdog_thread and self.wifi_watchdog_thread.is_alive():
            self.wifi_watchdog_thread.join(timeout=2)
        
        if self.mqtt_thread and self.mqtt_thread.is_alive():
            self.mqtt_thread.join(timeout=2)
        
        self.logger.info("Network Manager stopped")
    
    def _connect_wifi(self):
        """Connect to WiFi network"""
        try:
            # Check if already connected
            if self._check_wifi_connection():
                self.logger.info(f"Already connected to WiFi: {self.current_ssid}")
                return True
            
            # Try to connect to stored networks
            wifi_credentials = self._get_wifi_credentials()
            
            for ssid, password in wifi_credentials:
                if not ssid:
                    continue
                
                self.logger.info(f"Connecting to WiFi: {ssid}")
                
                # Configure WiFi connection
                with open('/tmp/wpa_supplicant.conf', 'w') as f:
                    f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
                    f.write('update_config=1\n')
                    f.write('country=US\n\n')
                    f.write('network={\n')
                    f.write(f'    ssid="{ssid}"\n')
                    if password:
                        f.write(f'    psk="{password}"\n')
                    else:
                        f.write('    key_mgmt=NONE\n')
                    f.write('}\n')
                
                # Apply configuration
                subprocess.call(['sudo', 'cp', '/tmp/wpa_supplicant.conf', '/etc/wpa_supplicant/wpa_supplicant.conf'])
                subprocess.call(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
                
                # Wait for connection
                for _ in range(30):  # Wait up to 30 seconds
                    if self._check_wifi_connection():
                        self.logger.info(f"Connected to WiFi: {self.current_ssid}")
                        
                        # Configure hostname if static IP is enabled
                        if self.app.system_manager.get_config('network', 'static_ip', False):
                            self._configure_static_ip()
                        
                        return True
                    
                    time.sleep(1)
            
            # If we get here, connection failed
            self.logger.error("Failed to connect to any WiFi network")
            
            # Start AP mode if no connection
            self._start_ap_mode()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to WiFi: {str(e)}")
            return False
    
    def _check_wifi_connection(self):
        """Check if currently connected to WiFi
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Run iwconfig command
            result = subprocess.check_output(['iwconfig', 'wlan0']).decode('utf-8')
            
            # Check for ESSID
            if 'ESSID:off/any' in result:
                self.wifi_connected = False
                self.current_ssid = ""
                self.wifi_rssi = 0
                return False
            
            # Extract SSID
            import re
            ssid_match = re.search(r'ESSID:"([^"]*)"', result)
            if ssid_match:
                self.current_ssid = ssid_match.group(1)
            else:
                self.current_ssid = ""
            
            # Extract signal level
            signal_match = re.search(r'Signal level=([0-9-]+)', result)
            if signal_match:
                self.wifi_rssi = int(signal_match.group(1))
            else:
                self.wifi_rssi = 0
            
            # Check if we have an IP address
            ip_addr = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
            
            if ip_addr:
                self.wifi_connected = True
                self.logger.debug(f"WiFi connected: {self.current_ssid}, IP: {ip_addr}, RSSI: {self.wifi_rssi} dBm")
                return True
            else:
                self.wifi_connected = False
                return False
            
        except Exception as e:
            self.logger.error(f"Error checking WiFi connection: {str(e)}")
            self.wifi_connected = False
            return False
    
    def _get_wifi_credentials(self):
        """Get stored WiFi credentials
        
        Returns:
            list: List of (SSID, password) tuples
        """
        try:
            # Try to read from NVS
            # For Raspberry Pi, we'll use a file-based approach
            credentials_file = 'config/wifi_credentials.json'
            
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    credentials = json.load(f)
                
                wifi_list = []
                for i in range(1, 4):
                    ssid = credentials.get(f'WIFI_SSID{i}', '')
                    password = credentials.get(f'WIFI_PASS{i}', '')
                    if ssid:
                        wifi_list.append((ssid, password))
                
                return wifi_list
            else:
                # Return default empty list
                return []
            
        except Exception as e:
            self.logger.error(f"Error getting WiFi credentials: {str(e)}")
            return []
    
    def _save_wifi_credentials(self, wifi_list):
        """Save WiFi credentials
        
        Args:
            wifi_list (list): List of (SSID, password) tuples
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            credentials = {}
            
            for i, (ssid, password) in enumerate(wifi_list, 1):
                if i > 3:
                    break  # Only store 3 sets of credentials
                
                credentials[f'WIFI_SSID{i}'] = ssid
                credentials[f'WIFI_PASS{i}'] = password
            
            # Save to file
            credentials_file = 'config/wifi_credentials.json'
            os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
            
            with open(credentials_file, 'w') as f:
                json.dump(credentials, f, indent=4)
            
            self.logger.info("WiFi credentials saved")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving WiFi credentials: {str(e)}")
            return False
    
    def _configure_static_ip(self):
        """Configure static IP address"""
        try:
            static_ip = self.app.system_manager.get_config('network', 'static_ip', {})
            
            if not static_ip:
                return
            
            ip_address = static_ip.get('ip', '')
            netmask = static_ip.get('netmask', '255.255.255.0')
            gateway = static_ip.get('gateway', '')
            dns1 = static_ip.get('dns1', '8.8.8.8')
            dns2 = static_ip.get('dns2', '8.8.4.4')
            
            if not ip_address or not gateway:
                self.logger.warning("Static IP configuration incomplete")
                return
            
            # Configure static IP
            with open('/tmp/dhcpcd.conf', 'w') as f:
                f.write('interface wlan0\n')
                f.write(f'static ip_address={ip_address}/24\n')
                f.write(f'static routers={gateway}\n')
                f.write(f'static domain_name_servers={dns1} {dns2}\n')
            
            # Apply configuration
            subprocess.call(['sudo', 'cp', '/tmp/dhcpcd.conf', '/etc/dhcpcd.conf'])
            subprocess.call(['sudo', 'systemctl', 'restart', 'dhcpcd'])
            
            self.logger.info(f"Static IP configured: {ip_address}")
            
        except Exception as e:
            self.logger.error(f"Error configuring static IP: {str(e)}")
    
    def _start_ap_mode(self):
        """Start Access Point mode for initial configuration"""
        try:
            self.logger.info("Starting Access Point mode for configuration")
            
            # Install required packages if not already installed
            subprocess.call(['sudo', 'apt-get', 'update'])
            subprocess.call(['sudo', 'apt-get', 'install', '-y', 'hostapd', 'dnsmasq'])
            
            # Configure hostapd
            with open('/tmp/hostapd.conf', 'w') as f:
                f.write('interface=wlan0\n')
                f.write('driver=nl80211\n')
                f.write('ssid=MushroomTentAP\n')
                f.write('hw_mode=g\n')
                f.write('channel=7\n')
                f.write('wmm_enabled=0\n')
                f.write('macaddr_acl=0\n')
                f.write('auth_algs=1\n')
                f.write('ignore_broadcast_ssid=0\n')
            
            # Configure dnsmasq
            with open('/tmp/dnsmasq.conf', 'w') as f:
                f.write('interface=wlan0\n')
                f.write('dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h\n')
                f.write('address=/#/192.168.4.1\n')
            
            # Configure network interface
            subprocess.call(['sudo', 'ifconfig', 'wlan0', 'down'])
            subprocess.call(['sudo', 'ifconfig', 'wlan0', '192.168.4.1', 'netmask', '255.255.255.0'])
            subprocess.call(['sudo', 'ifconfig', 'wlan0', 'up'])
            
            # Copy and enable hostapd configuration
            subprocess.call(['sudo', 'cp', '/tmp/hostapd.conf', '/etc/hostapd/hostapd.conf'])
            subprocess.call(['sudo', 'cp', '/tmp/dnsmasq.conf', '/etc/dnsmasq.conf'])
            
            # Enable services
            subprocess.call(['sudo', 'systemctl', 'stop', 'hostapd'])
            subprocess.call(['sudo', 'systemctl', 'stop', 'dnsmasq'])
            subprocess.call(['sudo', 'systemctl', 'start', 'hostapd'])
            subprocess.call(['sudo', 'systemctl', 'start', 'dnsmasq'])
            
            self.logger.info("Access Point mode started: SSID=MushroomTentAP, IP=192.168.4.1")
            
            # TODO: Start web server for configuration
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting AP mode: {str(e)}")
            return False
    
    def _stop_ap_mode(self):
        """Stop Access Point mode"""
        try:
            # Stop services
            subprocess.call(['sudo', 'systemctl', 'stop', 'hostapd'])
            subprocess.call(['sudo', 'systemctl', 'stop', 'dnsmasq'])
            
            # Restart networking
            subprocess.call(['sudo', 'systemctl', 'restart', 'dhcpcd'])
            
            self.logger.info("Access Point mode stopped")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping AP mode: {str(e)}")
            return False
    
    def _wifi_watchdog_loop(self):
        """Thread function for WiFi watchdog"""
        while self.running:
            try:
                # Check connection
                if not self._check_wifi_connection():
                    self.logger.warning("WiFi connection lost, attempting to reconnect")
                    self._connect_wifi()
                else:
                    # Check signal strength
                    min_rssi = self.app.system_manager.get_config('network', 'wifi_min_rssi', -75)
                    
                    if self.wifi_rssi < min_rssi:
                        self.logger.warning(f"WiFi signal too weak: {self.wifi_rssi} dBm, minimum: {min_rssi} dBm")
                        self._connect_wifi()  # Try to find a better connection
                
            except Exception as e:
                self.logger.error(f"Error in WiFi watchdog: {str(e)}")
            
            # Sleep interval
            check_interval = self.app.system_manager.get_config('network', 'wifi_check_interval', 60)
            time.sleep(check_interval)
    
    def _start_mdns(self):
        """Start mDNS service for local discovery"""
        try:
            # Get hostname from config
            hostname = self.app.system_manager.get_config('network', 'hostname', 'mushroom-controller')
            
            # Initialize Zeroconf
            self.zeroconf = Zeroconf()
            
            # Get IP address
            ip_addr = socket.gethostbyname(socket.gethostname())
            
            # Create service info
            self.mdns_info = ServiceInfo(
                "_http._tcp.local.",
                f"{hostname}._http._tcp.local.",
                addresses=[socket.inet_aton(ip_addr)],
                port=80,
                properties={
                    'path': '/'
                },
                server=f"{hostname}.local."
            )
            
            # Register service
            self.zeroconf.register_service(self.mdns_info)
            
            self.logger.info(f"mDNS service registered: {hostname}.local")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting mDNS service: {str(e)}")
            return False
    
    def _stop_mdns(self):
        """Stop mDNS service"""
        try:
            if self.zeroconf and self.mdns_info:
                self.zeroconf.unregister_service(self.mdns_info)
                self.zeroconf.close()
                
                self.zeroconf = None
                self.mdns_info = None
                
                self.logger.info("mDNS service stopped")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping mDNS service: {str(e)}")
            return False
    
    def _start_mqtt(self):
        """Start MQTT client"""
        try:
            # Get MQTT configuration
            mqtt_config = self.app.system_manager.get_config('network', 'mqtt', {})
            
            if not mqtt_config.get('enabled', False):
                return False
            
            broker = mqtt_config.get('broker', '')
            port = int(mqtt_config.get('port', 1883))
            username = mqtt_config.get('username', '')
            password = mqtt_config.get('password', '')
            topic = mqtt_config.get('topic', 'mushroom/tent')
            
            if not broker:
                self.logger.warning("MQTT broker not configured")
                return False
            
            # Create MQTT client
            client_id = f"mushroom-controller-{os.getpid()}"
            self.mqtt_client = mqtt.Client(client_id=client_id)
            
            # Set authentication if provided
            if username and password:
                self.mqtt_client.username_pw_set(username, password)
            
            # Set up callbacks
            self.mqtt_client.on_connect = self._mqtt_on_connect
            self.mqtt_client.on_disconnect = self._mqtt_on_disconnect
            self.mqtt# Raspberry Pi Mushroom Tent Controller
