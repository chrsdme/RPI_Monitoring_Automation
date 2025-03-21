#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relay Manager Module

This module handles all relay-related functionality, including:
- Relay initialization and configuration
- Relay state management
- Automation based on sensor readings and schedules
- Manual override functionality

Relay config details:
1. Main PSU (relay1): Turned on when needed by dependents, off otherwise
2. UV Light (relay2): Alternates with Grow Light on schedule
3. Grow Light (relay3): Alternates with UV Light on schedule
4. Tub Fans (relay4): Runs on schedule or when CO2 < 1100ppm
5. Humidifiers (relay5): Runs when humidity < 50% until > 85%
6. Heater (relay6): Runs when temperature < 20°C until > 24°C
7. IN/OUT Fans (relay7): Runs on schedule or when CO2 > 1600ppm until < 1000ppm
8. Reserved (relay8): For future use
"""

import os
import time
import logging
import threading
import json
from datetime import datetime, time as dt_time
import RPi.GPIO as GPIO

class RelayManager:
    """Relay Manager class for controlling relays"""
    
    def __init__(self, component_manager):
        """Initialize the Relay Manager
        
        Args:
            component_manager: Component manager instance
        """
        self.component_manager = component_manager
        self.app = component_manager.app
        self.logger = logging.getLogger('RelayManager')
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Get pin configurations from config
        pins = self.app.system_manager.get_config('pins', {})
        
        # Define default relay configurations
        self.relay_configs = {
            'relay1': {
                'name': 'Main PSU',
                'pin': pins.get('Relay1_PIN', 18),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,  # 5 minutes default
                'dependencies': [],
                'visible': False,
                'state': False
            },
            'relay2': {
                'name': 'UV Light',
                'pin': pins.get('Relay2_PIN', 24),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': ['relay1'],
                'visible': True,
                'state': False,
                'cycle': {'on_duration': 30, 'interval': 60, 'last_toggle': 0}
            },
            'relay3': {
                'name': 'Grow Light',
                'pin': pins.get('Relay3_PIN', 25),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': ['relay1'],
                'visible': True,
                'state': False,
                'cycle': {'on_duration': 30, 'interval': 60, 'last_toggle': 0}
            },
            'relay4': {
                'name': 'Tub Fans',
                'pin': pins.get('Relay4_PIN', 6),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': ['relay1'],
                'visible': True,
                'state': False,
                'cycle': {'on_duration': 15, 'interval': 60, 'last_toggle': 0}
            },
            'relay5': {
                'name': 'Humidifiers',
                'pin': pins.get('Relay5_PIN', 26),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': ['relay1'],
                'visible': True,
                'state': False
            },
            'relay6': {
                'name': 'Heater',
                'pin': pins.get('Relay6_PIN', 19),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': [],
                'visible': True,
                'state': False
            },
            'relay7': {
                'name': 'IN/OUT Fans',
                'pin': pins.get('Relay7_PIN', 13),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': ['relay1'],
                'visible': True,
                'state': False,
                'cycle': {'on_duration': 15, 'interval': 60, 'last_toggle': 0}
            },
            'relay8': {
                'name': 'Reserved',
                'pin': pins.get('Relay8_PIN', 16),
                'schedule': {'start': '00:00', 'end': '23:59'},
                'override': False,
                'override_until': 0,
                'override_duration': 300,
                'dependencies': [],
                'visible': False,
                'state': False
            }
        }
        
        # Thresholds for automation
        self.thresholds = {
            'humidity': {
                'low': 50,  # Trigger humidifier when below this
                'high': 85  # Turn off humidifier when above this
            },
            'temperature': {
                'low': 20,  # Trigger heater when below this
                'high': 24  # Turn off heater when above this
            },
            'co2': {
                'low': 1000,  # Stop IN/OUT fans when below this
                'tubfans_low': 1100,  # Turn on tub fans when below this
                'high': 1600  # Trigger IN/OUT fans when above this
            }
        }
        
        # Running state
        self.running = False
        
        # Initialize automation thread
        self.automation_thread = None
        
        # Last state update time
        self.last_update = 0
        
        # Initialize tapo integration
        self.tapo_integration = None
    
    def initialize(self):
        """Initialize all relays
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Initializing relays")
        
        try:
            # Update configurations from profile
            self._update_config_from_profile()
            
            # Set up GPIO pins
            for relay_id, config in self.relay_configs.items():
                pin = config['pin']
                GPIO.setup(pin, GPIO.OUT)
                
                # Relays are typically active LOW (OFF when HIGH)
                GPIO.output(pin, GPIO.HIGH)  # Ensure relays start in OFF state
                
                self.logger.info(f"Initialized {config['name']} relay on pin {pin}")
            
            # Set up Tapo integration if enabled
            if self.app.system_manager.get_config('tapo', 'enabled', False):
                self.tapo_integration = self.component_manager.tapo_manager
            
            self.logger.info("All relays initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing relays: {str(e)}")
            return False
    
    def _update_config_from_profile(self):
        """Update relay configurations from active profile"""
        try:
            # Get active profile
            profile = self.app.system_manager.get_active_profile()
            
            # Update threshold values
            if 'humidity_low_threshold' in profile:
                self.thresholds['humidity']['low'] = profile['humidity_low_threshold']
            
            if 'humidity_high_threshold' in profile:
                self.thresholds['humidity']['high'] = profile['humidity_high_threshold']
            
            if 'temperature_low_threshold' in profile:
                self.thresholds['temperature']['low'] = profile['temperature_low_threshold']
            
            if 'temperature_high_threshold' in profile:
                self.thresholds['temperature']['high'] = profile['temperature_high_threshold']
            
            if 'co2_low_threshold' in profile:
                self.thresholds['co2']['low'] = profile['co2_low_threshold']
                
            if 'co2_high_threshold' in profile:
                self.thresholds['co2']['high'] = profile['co2_high_threshold']
            
            # Update cycle configurations
            if 'fan_cycle' in profile:
                fan_cycle = profile['fan_cycle']
                
                # Update relay4 (Tub Fans) cycle
                if 'relay4' in self.relay_configs:
                    self.relay_configs['relay4']['cycle']['on_duration'] = fan_cycle.get('duration', 15)
                    self.relay_configs['relay4']['cycle']['interval'] = fan_cycle.get('interval', 60)
                
                # Update relay7 (IN/OUT Fans) cycle
                if 'relay7' in self.relay_configs:
                    self.relay_configs['relay7']['cycle']['on_duration'] = fan_cycle.get('duration', 15)
                    self.relay_configs['relay7']['cycle']['interval'] = fan_cycle.get('interval', 60)
            
            # Update light cycle configurations
            if 'light_cycle' in profile:
                light_cycle = profile['light_cycle']
                
                # Update relay2 (UV Light) cycle
                if 'relay2' in self.relay_configs:
                    self.relay_configs['relay2']['cycle']['on_duration'] = light_cycle.get('duration', 30)
                    self.relay_configs['relay2']['cycle']['interval'] = light_cycle.get('interval', 60)
                
                # Update relay3 (Grow Light) cycle
                if 'relay3' in self.relay_configs:
                    self.relay_configs['relay3']['cycle']['on_duration'] = light_cycle.get('duration', 30)
                    self.relay_configs['relay3']['cycle']['interval'] = light_cycle.get('interval', 60)
            
            # Update schedules
            if 'fan_schedule' in profile:
                fan_schedule = profile['fan_schedule']
                
                # Update relay4 (Tub Fans) schedule
                if 'relay4' in self.relay_configs:
                    self.relay_configs['relay4']['schedule']['start'] = fan_schedule.get('start', '00:00')
                    self.relay_configs['relay4']['schedule']['end'] = fan_schedule.get('end', '23:59')
                
                # Update relay7 (IN/OUT Fans) schedule
                if 'relay7' in self.relay_configs:
                    self.relay_configs['relay7']['schedule']['start'] = fan_schedule.get('start', '00:00')
                    self.relay_configs['relay7']['schedule']['end'] = fan_schedule.get('end', '23:59')
            
            # Update light schedules
            if 'light_schedule' in profile:
                light_schedule = profile['light_schedule']
                
                # Update relay2 (UV Light) schedule
                if 'relay2' in self.relay_configs:
                    self.relay_configs['relay2']['schedule']['start'] = light_schedule.get('start', '00:00')
                    self.relay_configs['relay2']['schedule']['end'] = light_schedule.get('end', '23:59')
                
                # Update relay3 (Grow Light) schedule
                if 'relay3' in self.relay_configs:
                    self.relay_configs['relay3']['schedule']['start'] = light_schedule.get('start', '00:00')
                    self.relay_configs['relay3']['schedule']['end'] = light_schedule.get('end', '23:59')
            
            # Update humidity schedule (for relay5)
            if 'humidity_schedule' in profile:
                humidity_schedule = profile['humidity_schedule']
                
                # Update relay5 (Humidifiers) schedule
                if 'relay5' in self.relay_configs:
                    self.relay_configs['relay5']['schedule']['start'] = humidity_schedule.get('start', '00:00')
                    self.relay_configs['relay5']['schedule']['end'] = humidity_schedule.get('end', '23:59')
            
            # Update override duration
            if 'override_duration' in profile:
                for relay_id in self.relay_configs:
                    self.relay_configs[relay_id]['override_duration'] = profile['override_duration']
            
            self.logger.info("Relay configurations updated from profile")
            
        except Exception as e:
            self.logger.error(f"Error updating relay configurations from profile: {str(e)}")
    
    def start(self):
        """Start the Relay Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start automation thread
        self.automation_thread = threading.Thread(target=self._automation_loop)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
        self.logger.info("Relay Manager started")
    
    def stop(self):
        """Stop the Relay Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for thread to terminate
        if self.automation_thread and self.automation_thread.is_alive():
            self.automation_thread.join(timeout=2)
        
        # Turn off all relays
        self._all_relays_off()
        
        self.logger.info("Relay Manager stopped")
    
    def _automation_loop(self):
        """Thread function for relay automation"""
        self.logger.info("Relay automation loop started")
        
        while self.running:
            try:
                # Update configurations from profile if changed
                self._update_config_from_profile()
                
                # Process relay automation
                self._process_automation()
                
                # Update Tapo devices if enabled
                if self.tapo_integration:
                    self._update_tapo_devices()
                
                # Publish relay states via MQTT if connected
                if self.app.network_manager.mqtt_connected:
                    self.app.network_manager.publish_relay_states()
                
                # Sleep for a short interval (we want responsive control)
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in relay automation loop: {str(e)}")
                time.sleep(10)  # Longer delay after error
    
    def _process_automation(self):
        """Process relay automation logic"""
        # Get current time
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_time = dt_time(now.hour, now.minute)
        
        # Get sensor data
        sensor_data = self.component_manager.sensor_manager.get_all_readings()
        
        # Calculate average temperature and humidity
        avg_temp = self.component_manager.sensor_manager.get_average_temperature()
        avg_humidity = self.component_manager.sensor_manager.get_average_humidity()
        
        # Get CO2 level
        co2 = sensor_data['scd40']['co2']
        
        # Process override timeouts
        current_timestamp = time.time()
        for relay_id, config in self.relay_configs.items():
            if config['override'] and config['override_until'] > 0 and current_timestamp > config['override_until']:
                # Override has expired
                self.logger.info(f"Override for {config['name']} has expired")
                config['override'] = False
                config['override_until'] = 0
        
        # Determine relay states based on logic
        
        # Relay 1 (Main PSU) - Turn on if any dependent relay needs it
        relay1_needed = False
        for relay_id, config in self.relay_configs.items():
            if relay_id != 'relay1' and 'relay1' in config['dependencies']:
                if self._should_relay_be_on(relay_id, current_time, avg_temp, avg_humidity, co2):
                    relay1_needed = True
                    break
        
        # Set relay1 state based on need
        if relay1_needed:
            self._set_relay_output('relay1', True)
        else:
            # Only turn off if not in override mode
            if not self.relay_configs['relay1']['override']:
                self._set_relay_output('relay1', False)
        
        # Process other relays
        for relay_id, config in self.relay_configs.items():
            if relay_id == 'relay1':
                continue  # Already handled
            
            # Check if relay should be on
            should_be_on = self._should_relay_be_on(relay_id, current_time, avg_temp, avg_humidity, co2)
            
            # Check dependencies
            dependencies_met = True
            for dep in config['dependencies']:
                if not self.relay_configs[dep]['state']:
                    dependencies_met = False
                    break
            
            # Set relay state
            if should_be_on and dependencies_met:
                self._set_relay_output(relay_id, True)
            elif not config['override']:
                self._set_relay_output(relay_id, False)
        
        # Special handling for UV Light and Grow Light alternating cycle
        if (not self.relay_configs['relay2']['override'] and 
            not self.relay_configs['relay3']['override']):
            
            # Check if both lights are in their operating time window
            uv_in_schedule = self._is_in_schedule('relay2', current_time)
            grow_in_schedule = self._is_in_schedule('relay3', current_time)
            
            if uv_in_schedule and grow_in_schedule:
                # Both lights should be in their alternating cycle
                
                # Calculate which light should be on based on the cycle
                cycle_time = int(current_timestamp / 60) % self.relay_configs['relay2']['cycle']['interval']
                
                if cycle_time < self.relay_configs['relay2']['cycle']['on_duration']:
                    # UV Light should be on, Grow Light off
                    self._set_relay_output('relay2', True)
                    self._set_relay_output('relay3', False)
                else:
                    # UV Light off, Grow Light on
                    self._set_relay_output('relay2', False)
                    self._set_relay_output('relay3', True)
        
        # Special handling for humidifiers and IN/OUT fans parallel operation
        if self.relay_configs['relay5']['state']:
            # If humidifiers are on, also turn on IN/OUT fans
            if not self.relay_configs['relay7']['override']:
                self._set_relay_output('relay7', True)
        
# Special handling for Tub fans and humidifier parallel operation
        if self.relay_configs['relay5']['state']:
            # If humidifiers are on, also turn on Tub fans
            if not self.relay_configs['relay4']['override']:
                self._set_relay_output('relay4', True)
    
    def _should_relay_be_on(self, relay_id, current_time, avg_temp, avg_humidity, co2):
        """Determine if a relay should be on based on automation rules
        
        Args:
            relay_id (str): Relay ID
            current_time (datetime.time): Current time
            avg_temp (float): Average temperature
            avg_humidity (float): Average humidity
            co2 (int): CO2 level
            
        Returns:
            bool: True if relay should be on, False otherwise
        """
        config = self.relay_configs[relay_id]
        
        # If override is active, respect that
        if config['override']:
            return config['state']
        
        # Check if in scheduled time window
        if not self._is_in_schedule(relay_id, current_time):
            return False
        
        # Apply specific logic for each relay
        if relay_id == 'relay1':
            # Main PSU - handled separately
            return config['state']
        
        elif relay_id == 'relay2' or relay_id == 'relay3':
            # UV Light and Grow Light - handled by cycle in _process_automation
            return config['state']
        
        elif relay_id == 'relay4':
            # Tub Fans - Run on cycle or when CO2 is low
            cycle_on = self._should_cycle_be_on(relay_id)
            co2_trigger = co2 < self.thresholds['co2']['tubfans_low']
            humidifier_on = self.relay_configs['relay5']['state']
            
            return cycle_on or co2_trigger or humidifier_on
        
        elif relay_id == 'relay5':
            # Humidifiers - Run when humidity is low
            return avg_humidity < self.thresholds['humidity']['low']
        
        elif relay_id == 'relay6':
            # Heater - Run when temperature is low
            return avg_temp < self.thresholds['temperature']['low']
        
        elif relay_id == 'relay7':
            # IN/OUT Fans - Run on cycle or when CO2 is high
            cycle_on = self._should_cycle_be_on(relay_id)
            co2_trigger = co2 > self.thresholds['co2']['high']
            humidifier_on = self.relay_configs['relay5']['state']
            
            return cycle_on or co2_trigger or humidifier_on
        
        elif relay_id == 'relay8':
            # Reserved - Not used
            return False
        
        # Default
        return False
    
    def _is_in_schedule(self, relay_id, current_time):
        """Check if current time is within the relay's schedule
        
        Args:
            relay_id (str): Relay ID
            current_time (datetime.time): Current time
            
        Returns:
            bool: True if within schedule, False otherwise
        """
        config = self.relay_configs[relay_id]
        schedule = config['schedule']
        
        # Parse schedule times
        start_h, start_m = map(int, schedule['start'].split(':'))
        end_h, end_m = map(int, schedule['end'].split(':'))
        
        start_time = dt_time(start_h, start_m)
        end_time = dt_time(end_h, end_m)
        
        # Handle times across midnight
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return current_time >= start_time or current_time <= end_time
    
    def _should_cycle_be_on(self, relay_id):
        """Check if a relay should be on based on its cycle configuration
        
        Args:
            relay_id (str): Relay ID
            
        Returns:
            bool: True if cycle is in ON phase, False otherwise
        """
        if relay_id not in self.relay_configs:
            return False
        
        config = self.relay_configs[relay_id]
        
        if 'cycle' not in config:
            return False
        
        cycle = config['cycle']
        current_time = time.time()
        
        # Get cycle parameters
        on_duration = cycle['on_duration'] * 60  # Convert to seconds
        interval = cycle['interval'] * 60  # Convert to seconds
        
        # Calculate position in cycle
        cycle_position = current_time % interval
        
        # Return True if in ON part of cycle
        return cycle_position < on_duration
    
    def _set_relay_output(self, relay_id, state):
        """Set the physical relay output
        
        Args:
            relay_id (str): Relay ID
            state (bool): True for ON, False for OFF
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        config = self.relay_configs[relay_id]
        
        # Skip if state hasn't changed
        if config['state'] == state:
            return True
        
        try:
            pin = config['pin']
            
            # Relays are typically active LOW (ON when LOW)
            GPIO.output(pin, not state)  # Invert state for active LOW
            
            # Update state
            self.relay_configs[relay_id]['state'] = state
            
            # Log change
            self.logger.info(f"Relay {config['name']} {'ON' if state else 'OFF'}")
            
            # Check if we need to update a Tapo device
            if self.tapo_integration and relay_id in ['relay1', 'relay6']:
                self.tapo_integration.set_device_by_relay(relay_id, state)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting relay {relay_id}: {str(e)}")
            return False
    
    def _update_tapo_devices(self):
        """Update Tapo devices based on relay states"""
        if not self.tapo_integration:
            return
        
        try:
            # Get all Tapo devices
            devices = self.tapo_integration.get_devices()
            
            # Map devices to relays
            for device_id, device in devices.items():
                relay_id = device.get('relay')
                if relay_id in self.relay_configs:
                    # Check if state differs
                    if device.get('state') != self.relay_configs[relay_id]['state']:
                        # Update device state
                        self.tapo_integration.set_device_by_relay(
                            relay_id, self.relay_configs[relay_id]['state'])
                        
        except Exception as e:
            self.logger.error(f"Error updating Tapo devices: {str(e)}")
    
    def _all_relays_off(self):
        """Turn off all relays"""
        for relay_id in self.relay_configs:
            self._set_relay_output(relay_id, False)
    
    def set_relay_state(self, relay_id, state, override=False, duration=None):
        """Set relay state with optional override
        
        Args:
            relay_id (str): Relay ID
            state (bool): True for ON, False for OFF
            override (bool, optional): Override automation. Defaults to False.
            duration (int, optional): Override duration in seconds. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        config = self.relay_configs[relay_id]
        
        try:
            # Check dependencies for turning ON
            if state and not override:
                for dep in config['dependencies']:
                    if not self.relay_configs[dep]['state']:
                        # Turn on dependency first
                        self.set_relay_state(dep, True)
            
            # Set override parameters
            if override:
                config['override'] = True
                
                # Set override duration
                if duration is None:
                    duration = config['override_duration']
                
                config['override_until'] = time.time() + duration
                self.logger.info(f"Override set for {config['name']} for {duration} seconds")
            
            # Set physical relay state
            result = self._set_relay_output(relay_id, state)
            
            # If turning OFF and there are dependent relays, turn them off too
            if not state:
                for dependent_id, dependent_config in self.relay_configs.items():
                    if relay_id in dependent_config['dependencies'] and dependent_config['state']:
                        self.set_relay_state(dependent_id, False)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error setting relay state for {relay_id}: {str(e)}")
            return False
    
    def get_relay_states(self):
        """Get current states of all relays
        
        Returns:
            dict: Dictionary of relay states
        """
        states = {}
        
        for relay_id, config in self.relay_configs.items():
            states[relay_id] = {
                'name': config['name'],
                'state': config['state'],
                'override': config['override'],
                'override_until': config['override_until'],
                'dependencies': config['dependencies'],
                'visible': config['visible'],
                'pin': config['pin'],
                'schedule': config['schedule']
            }
            
            if 'cycle' in config:
                states[relay_id]['cycle'] = config['cycle']
        
        return states
    
    def set_relay_config(self, relay_id, config_key, value):
        """Update relay configuration
        
        Args:
            relay_id (str): Relay ID
            config_key (str): Configuration key
            value: Configuration value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            if config_key in self.relay_configs[relay_id]:
                self.relay_configs[relay_id][config_key] = value
                self.logger.info(f"Updated {config_key} for {relay_id}")
                return True
            else:
                self.logger.error(f"Invalid config key: {config_key}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting relay config for {relay_id}: {str(e)}")
            return False
    
    def set_schedule(self, relay_id, start_time, end_time):
        """Set relay schedule
        
        Args:
            relay_id (str): Relay ID
            start_time (str): Start time in HH:MM format
            end_time (str): End time in HH:MM format
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            # Validate time format
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
            
            # Update schedule
            self.relay_configs[relay_id]['schedule'] = {
                'start': start_time,
                'end': end_time
            }
            
            self.logger.info(f"Updated schedule for {relay_id} to {start_time}-{end_time}")
            return True
            
        except ValueError:
            self.logger.error(f"Invalid time format. Use HH:MM")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting schedule for {relay_id}: {str(e)}")
            return False
    
    def set_cycle(self, relay_id, on_duration, interval):
        """Set relay cycle
        
        Args:
            relay_id (str): Relay ID
            on_duration (int): ON duration in minutes
            interval (int): Cycle interval in minutes
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            # Validate parameters
            if not isinstance(on_duration, int) or not isinstance(interval, int):
                raise ValueError("Duration and interval must be integers")
            
            if on_duration <= 0 or interval <= 0:
                raise ValueError("Duration and interval must be positive")
            
            if on_duration > interval:
                raise ValueError("Duration cannot be greater than interval")
            
            # Check if cycle exists
            if 'cycle' not in self.relay_configs[relay_id]:
                self.relay_configs[relay_id]['cycle'] = {
                    'on_duration': on_duration,
                    'interval': interval,
                    'last_toggle': 0
                }
            else:
                self.relay_configs[relay_id]['cycle']['on_duration'] = on_duration
                self.relay_configs[relay_id]['cycle']['interval'] = interval
            
            self.logger.info(f"Updated cycle for {relay_id} to {on_duration}m every {interval}m")
            return True
            
        except ValueError as ve:
            self.logger.error(f"Invalid cycle parameters: {str(ve)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting cycle for {relay_id}: {str(e)}")
            return False
    
    def set_thresholds(self, threshold_type, low, high):
        """Set temperature, humidity, or CO2 thresholds
        
        Args:
            threshold_type (str): 'temperature', 'humidity', or 'co2'
            low (float): Low threshold
            high (float): High threshold
            
        Returns:
            bool: True if successful, False otherwise
        """
        if threshold_type not in ['temperature', 'humidity', 'co2']:
            self.logger.error(f"Invalid threshold type: {threshold_type}")
            return False
        
        try:
            # Validate thresholds
            if not (isinstance(low, (int, float)) and isinstance(high, (int, float))):
                raise ValueError("Thresholds must be numbers")
            
            if low >= high:
                raise ValueError("Low threshold must be less than high threshold")
            
            # Update thresholds
            self.thresholds[threshold_type]['low'] = low
            self.thresholds[threshold_type]['high'] = high
            
            self.logger.info(f"Updated {threshold_type} thresholds to {low}-{high}")
            return True
            
        except ValueError as ve:
            self.logger.error(f"Invalid threshold parameters: {str(ve)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting thresholds for {threshold_type}: {str(e)}")
            return False
    
    def clear_overrides(self):
        """Clear all overrides"""
        for relay_id, config in self.relay_configs.items():
            config['override'] = False
            config['override_until'] = 0
        
        self.logger.info("All relay overrides cleared")
    
    def test_relay(self, relay_id):
        """Test a specific relay by turning it on for 1 second
        
        Args:
            relay_id (str): Relay ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if relay_id not in self.relay_configs:
            self.logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            # Turn relay on
            self._set_relay_output(relay_id, True)
            
            # Wait for 1 second
            time.sleep(1)
            
            # Turn relay off
            self._set_relay_output(relay_id, False)
            
            self.logger.info(f"Relay {relay_id} test completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error testing relay {relay_id}: {str(e)}")
            return False
    
    def test_all_relays(self):
        """Test all relays one by one
        
        Returns:
            dict: Test results
        """
        results = {}
        
        for relay_id in self.relay_configs:
            try:
                # Test relay
                self._set_relay_output(relay_id, True)
                time.sleep(1)
                self._set_relay_output(relay_id, False)
                
                results[relay_id] = {
                    'status': 'passed',
                    'message': f"Relay {relay_id} working"
                }
                
            except Exception as e:
                results[relay_id] = {
                    'status': 'failed',
                    'message': str(e)
                }
        
        self.logger.info(f"Relay test results: {json.dumps(results)}")
        return results
    
    def factory_reset(self):
        """Reset all relays to default configuration
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Turn off all relays
            self._all_relays_off()
            
            # Reset override flags
            self.clear_overrides()
            
            # Reset thresholds to defaults
            self.thresholds = {
                'humidity': {'low': 50, 'high': 85},
                'temperature': {'low': 20, 'high': 24},
                'co2': {'low': 1000, 'tubfans_low': 1100, 'high': 1600}
            }
            
            self.logger.info("Relay configurations reset to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting relay configurations: {str(e)}")
            return False