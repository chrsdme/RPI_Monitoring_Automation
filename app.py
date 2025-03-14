#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mushroom Tent Controller - Main Application

This is the main entry point for the Mushroom Tent Controller application.
It initializes all the necessary components and starts the application.
"""

import os
import sys
import signal
import time
import argparse
import threading
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Add the application path to the system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from core.system_manager import SystemManager
from core.network_manager import NetworkManager
from core.web_api_manager import WebApiManager
from core.ota_manager import OTAManager
from core.components_manager import ComponentManager

class MushroomController:
    """Main application class for the Mushroom Tent Controller"""
    
    def __init__(self, config_path=None, debug=False):
        """Initialize the Mushroom Tent Controller application
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
            debug (bool, optional): Enable debug mode. Defaults to False.
        """
        self.running = False
        self.debug = debug
        
        # Set up logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('MushroomController')
        
        self.logger.info("Initializing Mushroom Tent Controller")
        
        # Initialize managers
        self.system_manager = SystemManager(self, config_path)
        self.network_manager = NetworkManager(self)
        self.component_manager = ComponentManager(self)
        self.web_api_manager = WebApiManager(self)
        self.ota_manager = OTAManager(self)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Initialization complete")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals
        
        Args:
            sig: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the Mushroom Tent Controller application"""
        if self.running:
            self.logger.warning("Application is already running")
            return
        
        self.logger.info("Starting application")
        self.running = True
        
        try:
            # Start managers in order
            self.logger.info("Starting System Manager")
            self.system_manager.start()
            
            self.logger.info("Starting Network Manager")
            self.network_manager.start()
            
            self.logger.info("Starting Components Manager")
            self.component_manager.start()
            
            self.logger.info("Starting Web API Manager")
            self.web_api_manager.start()
            
            self.logger.info("Starting OTA Manager")
            self.ota_manager.start()
            
            self.logger.info("Application started successfully")
            
            # Main thread loop
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the Mushroom Tent Controller application"""
        if not self.running:
            return
        
        self.logger.info("Stopping application")
        self.running = False
        
        # Stop managers in reverse order
        self.logger.info("Stopping OTA Manager")
        self.ota_manager.stop()
        
        self.logger.info("Stopping Web API Manager")
        self.web_api_manager.stop()
        
        self.logger.info("Stopping Components Manager")
        self.component_manager.stop()
        
        self.logger.info("Stopping Network Manager")
        self.network_manager.stop()
        
        self.logger.info("Stopping System Manager")
        self.system_manager.stop()
        
        self.logger.info("Application stopped")


# Main entry point
def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Mushroom Tent Controller")
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Create and start the application
    app = MushroomController(config_path=args.config, debug=args.debug)
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()