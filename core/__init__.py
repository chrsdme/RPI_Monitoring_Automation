#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mushroom Tent Controller Core Package

This package contains all core modules for the Mushroom Tent Controller application.
"""

# Define version information
__version__ = '1.0.0'
__author__ = 'Mushroom Tent Controller Team'

# Import core modules
from .system_manager import SystemManager
from .network_manager import NetworkManager
from .web_api_manager import WebApiManager
from .ota_manager import OTAManager
from .components_manager import ComponentManager

# Initialize module docstrings
SystemManager.__doc__ = "System Manager for handling system-related functionality"
NetworkManager.__doc__ = "Network Manager for handling network-related functionality"
WebApiManager.__doc__ = "Web API Manager for handling web server and API endpoints"
OTAManager.__doc__ = "OTA Manager for handling over-the-air updates"
ComponentManager.__doc__ = "Component Manager for managing hardware components"