#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tapo Manager Module

This module handles the integration with TP-Link Tapo smart plugs (P100, etc.)
"""

import json
import time
import logging
import threading
import requests

class TapoManager:
    """Tapo Manager class for managing TP-Link Tapo smart plugs"""
    
    def __init__(self, component_manager):
        """Initialize the Tapo Manager
        
        Args:
            component_manager: Component manager instance
        """
        self.component_manager = component_manager
        self.app = component_manager.app
        self.logger = logging.getLogger('TapoManager')
        
        # Tapo device state
        self.devices = {}
        
        # Authentication tokens
        self.tokens = {}
        
        # Threads
        self.update_thread = None
        
        # Running state
        self.running = False
    
    def initialize(self):
        """Initialize the Tapo Manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load device configuration
            tapo_config = self.app.system_manager.get_config('tapo', {})
            
            if not tapo_config.get('enabled', False):
                return True
            
            # Get device configurations
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
                    'last_update': 0
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
        
        # Initialize devices
        for device_id, device in self.devices.items():
            try:
                # Authenticate
                self._authenticate(device_id)
            except Exception as e:
                self.logger.error(f"Error authenticating Tapo device {device_id}: {str(e)}")
        
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
        
        self.logger.info("Tapo Manager stopped")
    
    def _authenticate(self, device_id):
        """Authenticate with Tapo device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return False
            
            # Skip if no credentials
            if not device.get('username') or not device.get('password'):
                return False
            
            # Skip if no IP
            if not device.get('ip'):
                return False
            
            # Prepare authentication request
            url = f"http://{device['ip']}/app/login"
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                'method': 'login',
                'params': {
                    'username': device['username'],
                    'password': device['password']
                }
            }
            
            # Send request
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code != 200:
                self.logger.error(f"Authentication failed for Tapo device {device_id}: {response.status_code}")
                return False
            
            # Parse response
            data = response.json()
            
            if 'error_code' in data and data['error_code'] != 0:
                self.logger.error(f"Authentication failed for Tapo device {device_id}: {data['error_code']}")
                return False
            
            # Extract token
            token = data.get('result', {}).get('token')
            
            if not token:
                self.logger.error(f"No token returned for Tapo device {device_id}")
                return False
            
            # Store token
            self.tokens[device_id] = token
            
            # Update device state
            device['connected'] = True
            device['last_update'] = time.time()
            
            self.logger.info(f"Authenticated with Tapo device {device_id}")
            
            # Get initial state
            self._get_device_state(device_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error authenticating with Tapo device {device_id}: {str(e)}")
            return False
    
    def _get_device_state(self, device_id):
        """Get current state of Tapo device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return False
            
            # Skip if not connected
            if not device.get('connected'):
                return False
            
            # Get token
            token = self.tokens.get(device_id)
            if not token:
                return False
            
            # Prepare request
            url = f"http://{device['ip']}/app/device"
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'token={token}'
            }
            payload = {
                'method': 'get_device_info',
                'params': {}
            }
            
            # Send request
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get state for Tapo device {device_id}: {response.status_code}")
                return False
            
            # Parse response
            data = response.json()
            
            if 'error_code' in data and data['error_code'] != 0:
                self.logger.error(f"Failed to get state for Tapo device {device_id}: {data['error_code']}")
                
                # Re-authenticate if token expired
                if data['error_code'] == -20671:
                    self._authenticate(device_id)
                
                return False
            
            # Extract state
            device_info = data.get('result', {})
            device_on = device_info.get('device_on', False)
            
            # Update device state
            device['state'] = device_on
            device['last_update'] = time.time()
            
            self.logger.debug(f"Tapo device {device_id} state: {'ON' if device_on else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error getting state for Tapo device {device_id}: {str(e)}")
            return False
    
    def _set_device_state(self, device_id, state):
        """Set state of Tapo device
        
        Args:
            device_id (str): Device ID
            state (bool): True for on, False for off
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                return False
            
            # Skip if not connected
            if not device.get('connected'):
                # Try to authenticate
                if not self._authenticate(device_id):
                    return False
            
            # Get token
            token = self.tokens.get(device_id)
            if not token:
                return False
            
            # Prepare request
            url = f"http://{device['ip']}/app/device"
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'token={token}'
            }
            payload = {
                'method': 'set_device_info',
                'params': {
                    'device_on': state
                }
            }
            
            # Send request
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to set state for Tapo device {device_id}: {response.status_code}")
                return False
            
            # Parse response
            data = response.json()
            
            if 'error_code' in data and data['error_code'] != 0:
                self.logger.error(f"Failed to set state for Tapo device {device_id}: {data['error_code']}")
                
                # Re-authenticate if token expired
                if data['error_code'] == -20671:
                    if self._authenticate(device_id):
                        # Retry after re-authentication
                        return self._set_device_state(device_id, state)
                
                return False
            
            # Update device state
            device['state'] = state
            device['last_update'] = time.time()
            
            self.logger.info(f"Set Tapo device {device_id} state to {'ON' if state else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting state for Tapo device {device_id}: {str(e)}")
            return False
    
    def _update_loop(self):
        """Thread function for updating device states"""
        while self.running:
            try:
                # Update device states
                for device_id in self.devices:
                    self._get_device_state(device_id)
                
                # Update relay states based on device states
                self._update_relay_states()
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {str(e)}")
            
            # Sleep for next update
            time.sleep(30)  # Update every 30 seconds
    
    def _update_relay_states(self):
        """Update relay states based on device states"""
        try:
            for device_id, device in self.devices.items():
                relay_id = device.get('relay')
                if not relay_id:
                    continue
                
                # Check if relay exists
                relay_states = self.component_manager.relay_manager.get_relay_states()
                if relay_id not in relay_states:
                    continue
                
                # Check if device state changed
                device_state = device.get('state', False)
                relay_state = relay_states[relay_id]['state']
                
                if device_state != relay_state:
                    self.logger.info(f"Tapo device {device_id} state ({device_state}) differs from relay {relay_id} state ({relay_state})")
                    
                    # Sync relay state to match device state
                    self.component_manager.relay_manager.set_relay(relay_id, device_state, override=True)
            
        except Exception as e:
            self.logger.error(f"Error updating relay states: {str(e)}")
    
    def set_device_by_relay(self, relay_id, state):
        """Set device state based on relay ID
        
        Args:
            relay_id (str): Relay ID
            state (bool): True for on, False for off
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find device associated with relay
            for device_id, device in self.devices.items():
                if device.get('relay') == relay_id:
                    # Set device state
                    return self._set_device_state(device_id, state)
            
            # No device found for relay
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting device state for relay {relay_id}: {str(e)}")
            return False
    
    def get_devices(self):
        """Get all devices
        
        Returns:
            dict: Device states
        """
        device_states = {}
        
        for device_id, device in self.devices.items():
            device_states[device_id] = {
                'state': device.get('state', False),
                'connected': device.get('connected', False),
                'ip': device.get('ip', ''),
                'relay': device.get('relay', '')
            }
        
        return device_states