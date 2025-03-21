#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Components Manager Module

This module manages the hardware components including:
- Sensors (DHT22, SCD40, Display)
- Relays
- Tapo smart plugs
"""

import logging
from core.components.sensor_manager import SensorManager
from core.components.relay_manager import RelayManager
from core.components.tapo_manager import TapoManager

class ComponentManager:
    """Component Manager class for managing hardware components"""
    
    def __init__(self, app):
        """Initialize the Component Manager
        
        Args:
            app: Main application instance
        """
        self.app = app
        self.logger = logging.getLogger('ComponentManager')
        
        # Initialize component managers
        self.sensor_manager = SensorManager(self)
        self.relay_manager = RelayManager(self)
        self.tapo_manager = TapoManager(self)
        
        # Running state
        self.running = False
    
    def start(self):
        """Start the Component Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Initialize sensors
        if not self.sensor_manager.initialize():
            self.logger.error("Failed to initialize sensors")
        
        # Initialize relays
        if not self.relay_manager.initialize():
            self.logger.error("Failed to initialize relays")
        
       # Initialize Tapo integration if configured
        tapo_enabled = self.app.system_manager.get_config('tapo', 'enabled', False)
        if tapo_enabled:
            if not self.tapo_manager.initialize():
                self.logger.error("Failed to initialize Tapo integration")
        
        # Start components
        self.sensor_manager.start()
        self.relay_manager.start()
        
        if tapo_enabled:
            self.tapo_manager.start()
        
        self.logger.info("Component Manager started")
    
    def stop(self):
        """Stop the Component Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop components in reverse order
        if self.app.system_manager.get_config('tapo', 'enabled', False):
            self.tapo_manager.stop()
        
        self.relay_manager.stop()
        self.sensor_manager.stop()
        
        self.logger.info("Component Manager stopped")