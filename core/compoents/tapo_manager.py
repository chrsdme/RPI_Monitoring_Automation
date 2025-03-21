#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tapo Manager Module

This module handles integration with TP-Link Tapo smart plugs (P100, etc.)
providing control for devices connected to these plugs instead of directly
to the relay module.

References:
- https://github.com/ClementNerma/tapo-rest
- https://github.com/mihai-dinculescu/tapo/tree/main/tapo
- https://github.com/omegahiro/tapo-esp32
"""

import os
import time
import logging
import threading
import json
import requests
import uuid
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class TapoManager:
    """Tapo Manager class for integrating with TP-Link Tapo smart plugs"""
    
    def __init__(self, component_manager):
        """Initialize the Tapo Manager
        
        Args:
            component_manager: Component manager instance
        """
        self.component_manager = component_manager
        self.app = component_manager.app
        self.logger = logging.getLogger('TapoManager')
        
        # Initialize device configurations
        self.devices = {}
        
        # Authentication tokens
        self.tokens = {}
        
        # Running state
        self.running = False
        
        # Update thread
        self.update_thread = None
        
        # Terminal UUID for Tapo API
        self.terminal_uuid = str(uuid.uuid4())
    
    def initialize(self):
        """Initialize Tapo integration
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Initializing Tapo integration")
        
        try:
            # Check if Tapo integration is enabled
            tapo_config = self.app.system_manager.get_config('tapo', {})
            
            if not tapo_config.get('enabled', False):
                self.logger.info("Tapo integration is disabled")
                return True
            
            # Load device configurations
            devices_config = tapo_config.get('devices', [])
            
            for device_config in devices_config:
                device_id = device_config.get('id')
                if not device_id:
                    continue
                
                self.devices[device_id] = {
                    'ip': device_config.get('ip', ''),
                    'username': device_config.get('username', ''),
                    'password': device_config.get('password', ''),
                    'relay': device_config.get('relay', ''),
                    'state': False,
                    'connected': False,
                    'last_update': 0,
                    'error_count': 0
                }
            
            self.logger.info(f"Initialized {len(self.devices)} Tapo devices")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Tapo Manager: {str(e)}")
            return False
    
    def start(self):
        """Start the Tapo Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Authenticate all devices
        for device_id in self.devices:
            self._authenticate(device_id)
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.logger.info("Tapo Manager started")
    
    def stop(self):
        """Stop the Tapo Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for thread to terminate
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        
        # Clear tokens
        self.tokens.clear()
        
        self.logger.info("Tapo Manager stopped")
    
    def _update_loop(self):
        """Thread function for updating device states"""
        self.logger.info("Tapo update loop started")
        
        while self.running:
            try:
                # Update device states
                for device_id in self.devices:
                    try:
                        self._get_device_state(device_id)
                    except Exception as e:
                        self.logger.error(f"Error updating device {device_id}: {str(e)}")
                        self.devices[device_id]['error_count'] += 1
                        
                        # Try to re-authenticate if too many errors
                        if self.devices[device_id]['error_count'] > 5:
                            self.logger.info(f"Re-authenticating device {device_id} after errors")
                            self._authenticate(device_id)
                            self.devices[device_id]['error_count'] = 0
                
                # Sleep for a while
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in Tapo update loop: {str(e)}")
                time.sleep(120)  # Longer delay after error
    
    def _generate_key_and_iv(self, password, email):
        """Generate encryption key and IV for Tapo communication
        
        Args:
            password (str): User password
            email (str): User email/username
            
        Returns:
            tuple: (key, iv) for encryption
        """
        # Convert password and email to bytes
        password_bytes = password.encode('utf-8')
        email_bytes = email.encode('utf-8')
        
        # Generate key using SHA-256
        key = hashlib.sha256(password_bytes).digest()
        
        # Generate IV using MD5
        iv = hashlib.md5(email_bytes).digest()
        
        return key, iv
    
    def _encrypt_password(self, password, email):
        """Encrypt password for Tapo login
        
        Args:
            password (str): User password
            email (str): User email/username
            
        Returns:
            str: Encrypted password in Base64
        """
        # Generate key and IV
        key, iv = self._generate_key_and_iv(password, email)
        
        # Create AES cipher in CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Encrypt password
        padded_password = pad(password.encode('utf-8'), AES.block_size)
        encrypted_password = cipher.encrypt(padded_password)
        
        # Return Base64 encoded string
        return base64.b64encode(encrypted_password).decode('utf-8')
    
    def _authenticate(self, device_id):
        """Authenticate with Tapo device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if device_id not in self.devices:
            self.logger.error(f"Unknown device ID: {device_id}")
            return False
        
        device = self.devices[device_id]
        
        # Verify required parameters
        if not device['ip'] or not device['username'] or not device['password']:
            self.logger.error(f"Missing credentials for device {device_id}")
            return False
        
        try:
            self.logger.info(f"Authenticating with Tapo device {device_id} at {device['ip']}")
            
            # Step 1: Get handshake keys
            handshake_url = f"http://{device['ip']}/app/handshake"
            handshake_data = {
                "method": "handshake",
                "params": {
                    "key": self.terminal_uuid,
                    "requestTimeMils": int(time.time() * 1000)
                }
            }
            
            handshake_response = requests.post(
                handshake_url,
                json=handshake_data,
                timeout=10
            )
            
            if handshake_response.status_code != 200:
                self.logger.error(f"Handshake failed with status {handshake_response.status_code}")
                return False
            
            handshake_result = handshake_response.json()
            
            # Step 2: Login with encrypted credentials
            login_url = f"http://{device['ip']}/app/login"
            headers = {"Cookie": f"TP_SESSIONID={handshake_result.get('result', {}).get('token')}"}
            
            # Encrypt password
            encrypted_password = self._encrypt_password(device['password'], device['username'])
            
            login_data = {
                "method": "login_device",
                "params": {
                    "username": base64.b64encode(device['username'].encode()).decode(),
                    "password": encrypted_password
                }
            }
            
            login_response = requests.post(
                login_url,
                headers=headers,
                json=login_data,
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.logger.error(f"Login failed with status {login_response.status_code}")
                return False
            
            login_result = login_response.json()
            
            # Store token for later use
            token = login_response.headers.get('Set-Cookie', '').split('=')[1].split(';')[0]
            self.tokens[device_id] = token
            
            # Update device status
            self.devices[device_id]['connected'] = True
            self.devices[device_id]['error_count'] = 0
            self.devices[device_id]['last_update'] = time.time()
            
            self.logger.info(f"Authentication successful for device {device_id}")
            
            # Get initial state
            self._get_device_state(device_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error authenticating with device {device_id}: {str(e)}")
            self.devices[device_id]['connected'] = False
            self.devices[device_id]['error_count'] += 1
            return False
    
    def _get_device_state(self, device_id):
        """Get current state of Tapo device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if device_id not in self.devices:
            self.logger.error(f"Unknown device ID: {device_id}")
            return False
        
        device = self.devices[device_id]
        
        # Check if device is connected
        if not device['connected'] or device_id not in self.tokens:
            # Try to authenticate
            if not self._authenticate(device_id):
                return False
        
        try:
            self.logger.debug(f"Getting state for device {device_id}")
            
            # Prepare request
            url = f"http://{device['ip']}/app/device"
            headers = {"Cookie": f"TP_SESSIONID={self.tokens[device_id]}"}
            
            data = {
                "method": "get_device_info",
                "requestTimeMils": int(time.time() * 1000)
            }
            
            # Send request
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get state with status {response.status_code}")
                
                # If authentication error, try to re-authenticate
                if response.status_code == 401:
                    self._authenticate(device_id)
                
                return False
            
            result = response.json()
            
            # Extract device state
            device_info = result.get('result', {})
            device_on = device_info.get('device_on', False)
            
            # Update device state
            self.devices[device_id]['state'] = device_on
            self.devices[device_id]['last_update'] = time.time()
            self.devices[device_id]['error_count'] = 0
            
            self.logger.debug(f"Device {device_id} state: {'ON' if device_on else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error getting state for device {device_id}: {str(e)}")
            self.devices[device_id]['error_count'] += 1
            
# Try to re-authenticate if connection error
            if self.devices[device_id]['error_count'] > 3:
                self._authenticate(device_id)
            
            return False
    
    def _set_device_state(self, device_id, state):
        """Set state of Tapo device
        
        Args:
            device_id (str): Device ID
            state (bool): True for ON, False for OFF
            
        Returns:
            bool: True if successful, False otherwise
        """
        if device_id not in self.devices:
            self.logger.error(f"Unknown device ID: {device_id}")
            return False
        
        device = self.devices[device_id]
        
        # Check if device is connected
        if not device['connected'] or device_id not in self.tokens:
            # Try to authenticate
            if not self._authenticate(device_id):
                return False
        
        try:
            self.logger.info(f"Setting device {device_id} state to {'ON' if state else 'OFF'}")
            
            # Prepare request
            url = f"http://{device['ip']}/app/device"
            headers = {"Cookie": f"TP_SESSIONID={self.tokens[device_id]}"}
            
            data = {
                "method": "set_device_info",
                "params": {
                    "device_on": state
                },
                "requestTimeMils": int(time.time() * 1000)
            }
            
            # Send request
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to set state with status {response.status_code}")
                
                # If authentication error, try to re-authenticate
                if response.status_code == 401:
                    self._authenticate(device_id)
                    # Try again after re-authentication
                    return self._set_device_state(device_id, state)
                
                return False
            
            result = response.json()
            
            # Update device state
            self.devices[device_id]['state'] = state
            self.devices[device_id]['last_update'] = time.time()
            self.devices[device_id]['error_count'] = 0
            
            self.logger.info(f"Successfully set device {device_id} to {'ON' if state else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting state for device {device_id}: {str(e)}")
            self.devices[device_id]['error_count'] += 1
            
            # Try to re-authenticate if connection error
            if self.devices[device_id]['error_count'] > 3:
                self._authenticate(device_id)
            
            return False
    
    def set_device_by_relay(self, relay_id, state):
        """Set Tapo device state based on associated relay ID
        
        Args:
            relay_id (str): Relay ID
            state (bool): True for ON, False for OFF
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Find device mapped to this relay
        for device_id, device in self.devices.items():
            if device['relay'] == relay_id:
                return self._set_device_state(device_id, state)
        
        self.logger.warning(f"No Tapo device mapped to relay {relay_id}")
        return False
    
    def get_devices(self):
        """Get all Tapo devices
        
        Returns:
            dict: Dictionary of device information
        """
        result = {}
        
        for device_id, device in self.devices.items():
            result[device_id] = {
                'ip': device['ip'],
                'relay': device['relay'],
                'state': device['state'],
                'connected': device['connected'],
                'last_update': device['last_update']
            }
        
        return result
    
    def add_device(self, device_id, ip, username, password, relay_id=None):
        """Add a new Tapo device
        
        Args:
            device_id (str): Device ID
            ip (str): Device IP address
            username (str): Tapo account username/email
            password (str): Tapo account password
            relay_id (str, optional): Associated relay ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if device ID already exists
            if device_id in self.devices:
                self.logger.warning(f"Device ID {device_id} already exists, updating configuration")
            
            # Add device
            self.devices[device_id] = {
                'ip': ip,
                'username': username,
                'password': password,
                'relay': relay_id,
                'state': False,
                'connected': False,
                'last_update': 0,
                'error_count': 0
            }
            
            # Save to configuration
            tapo_config = self.app.system_manager.get_config('tapo', {})
            
            if 'devices' not in tapo_config:
                tapo_config['devices'] = []
            
            # Check if device already exists in config
            device_exists = False
            for i, device in enumerate(tapo_config['devices']):
                if device.get('id') == device_id:
                    # Update existing device
                    tapo_config['devices'][i] = {
                        'id': device_id,
                        'ip': ip,
                        'username': username,
                        'password': password,
                        'relay': relay_id
                    }
                    device_exists = True
                    break
            
            if not device_exists:
                # Add new device
                tapo_config['devices'].append({
                    'id': device_id,
                    'ip': ip,
                    'username': username,
                    'password': password,
                    'relay': relay_id
                })
            
            # Enable Tapo integration if not already enabled
            tapo_config['enabled'] = True
            
            # Save configuration
            self.app.system_manager.set_config('tapo', tapo_config)
            
            # Try to authenticate with the device
            self._authenticate(device_id)
            
            self.logger.info(f"Added Tapo device {device_id} at {ip}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding Tapo device: {str(e)}")
            return False
    
    def remove_device(self, device_id):
        """Remove a Tapo device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if device exists
            if device_id not in self.devices:
                self.logger.warning(f"Device ID {device_id} not found")
                return False
            
            # Remove device
            del self.devices[device_id]
            
            # Remove from tokens if exists
            if device_id in self.tokens:
                del self.tokens[device_id]
            
            # Save to configuration
            tapo_config = self.app.system_manager.get_config('tapo', {})
            
            if 'devices' in tapo_config:
                # Remove device from config
                tapo_config['devices'] = [
                    device for device in tapo_config['devices']
                    if device.get('id') != device_id
                ]
            
            # Save configuration
            self.app.system_manager.set_config('tapo', tapo_config)
            
            self.logger.info(f"Removed Tapo device {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing Tapo device: {str(e)}")
            return False
    
    def update_device_mapping(self, device_id, relay_id):
        """Update mapping between Tapo device and relay
        
        Args:
            device_id (str): Device ID
            relay_id (str): Relay ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if device exists
            if device_id not in self.devices:
                self.logger.warning(f"Device ID {device_id} not found")
                return False
            
            # Update mapping
            self.devices[device_id]['relay'] = relay_id
            
            # Save to configuration
            tapo_config = self.app.system_manager.get_config('tapo', {})
            
            if 'devices' in tapo_config:
                # Update device in config
                for device in tapo_config['devices']:
                    if device.get('id') == device_id:
                        device['relay'] = relay_id
                        break
            
            # Save configuration
            self.app.system_manager.set_config('tapo', tapo_config)
            
            self.logger.info(f"Updated Tapo device {device_id} mapping to relay {relay_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating Tapo device mapping: {str(e)}")
            return False
    
    def test_device(self, device_id):
        """Test a Tapo device by turning it on and then off
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if device exists
            if device_id not in self.devices:
                self.logger.warning(f"Device ID {device_id} not found")
                return False
            
            self.logger.info(f"Testing Tapo device {device_id}")
            
            # Turn device on
            if not self._set_device_state(device_id, True):
                return False
            
            # Wait for 2 seconds
            time.sleep(2)
            
            # Turn device off
            if not self._set_device_state(device_id, False):
                return False
            
            self.logger.info(f"Tapo device {device_id} test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error testing Tapo device: {str(e)}")
            return False