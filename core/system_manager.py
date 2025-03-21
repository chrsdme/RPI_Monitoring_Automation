#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Manager Module

This module handles all system-related functionality including:
- Storage management
- Time synchronization
- Maintenance and diagnostics
- Logging
- Power management
- Notifications
- Profile management
"""

import os
import json
import time
import logging
import threading
import sqlite3
import subprocess
from datetime import datetime
import ntplib
import psutil
import RPi.GPIO as GPIO

class SystemManager:
    """System Manager class for managing system-related functionality"""
    
    def __init__(self, app, config_path=None):
        """Initialize the System Manager
        
        Args:
            app: Main application instance
            config_path (str, optional): Path to configuration file. Defaults to None.
        """
        self.app = app
        self.logger = logging.getLogger('SystemManager')
        self.config_path = config_path or 'config/config.json'
        self.db_path = 'data/mushroom_controller.db'
        self.config = {}
        self.running = False
        
        # Initialize threads
        self.maintenance_thread = None
        self.time_sync_thread = None
        self.reboot_scheduler_thread = None
        self.fan_control_thread = None
        
        # Initialize database
        self._init_database()
        
        # Load configuration
        self._load_config()
        
        # Initialize fan control
        self.fan_pin = self.get_config('pins', 'FAN_PIN', 12)
    
    def _init_database(self):
        """Initialize the SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    sensor TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    co2 REAL,
                    errors INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relay_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    relay_id TEXT NOT NULL,
                    state INTEGER NOT NULL,
                    auto_control INTEGER NOT NULL,
                    override INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            
            # Create default profiles if they don't exist
            current_time = int(time.time())
            default_profiles = [
                ('test', json.dumps(self._get_default_profile('test')), current_time, current_time),
                ('colonisation', json.dumps(self._get_default_profile('colonisation')), current_time, current_time),
                ('fruiting', json.dumps(self._get_default_profile('fruiting')), current_time, current_time)
            ]
            
            for profile in default_profiles:
                cursor.execute('''
                    INSERT OR IGNORE INTO profiles (name, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', profile)
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
    
    def _get_default_profile(self, profile_name):
        """Get default profile settings
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            dict: Default profile settings
        """
        # Common settings
        base_settings = {
            'graph_update_interval': 60,  # seconds
            'graph_max_points': 60,
            'dht_sensor_interval': 30,    # seconds
            'scd40_sensor_interval': 30,  # seconds
            'humidity_low_threshold': 50, # percent
            'humidity_high_threshold': 85,# percent
            'fan_cycle': {
                'duration': 15,           # minutes
                'interval': 60            # minutes
            },
            'fan_schedule': {
                'start': '00:00',
                'end': '23:59'
            },
            'light_cycle': {
                'duration': 30,           # minutes
                'interval': 60            # minutes
            }
        }
        
        # Profile-specific settings
        if profile_name == 'test':
            # Test profile - conservative settings
            return {
                **base_settings,
                'temperature_low_threshold': 20,
                'temperature_high_threshold': 24,
                'co2_low_threshold': 1000,
                'co2_high_threshold': 1600,
                'light_schedule': {
                    'start': '09:00',
                    'end': '21:00'
                }
            }
        
        elif profile_name == 'colonisation':
            # Colonisation profile - higher temperature, no light
            return {
                **base_settings,
                'temperature_low_threshold': 24,
                'temperature_high_threshold': 27,
                'co2_low_threshold': 1500,
                'co2_high_threshold': 3000,
                'light_schedule': {
                    'start': '00:00',
                    'end': '00:00'  # No light
                }
            }
        
        elif profile_name == 'fruiting':
            # Fruiting profile - lower temperature, more light
            return {
                **base_settings,
                'temperature_low_threshold': 18,
                'temperature_high_threshold': 22,
                'co2_low_threshold': 800,
                'co2_high_threshold': 1200,
                'light_schedule': {
                    'start': '08:00',
                    'end': '22:00'  # Longer light period
                }
            }
        
        # Default fallback
        return base_settings
    
    def _load_config(self):
        """Load configuration from file or use defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'system': {
                'name': 'Mushroom Tent Controller',
                'version': '1.0.0',
                'log_level': 'INFO',
                'log_max_size': 1024,    # KB
                'log_flush_interval': 60, # seconds
                'sensor_error_threshold': 5,
                'reboot_day': 0,         # Sunday
                'reboot_time': '04:00',
                'sleep_mode': 'none',
                'sleep_start_time': '00:00',
                'sleep_end_time': '00:00'
            },
            'network': {
                'hostname': 'mushroom-controller',
                'wifi_check_interval': 60, # seconds
                'wifi_min_rssi': -75,
                'mqtt': {
                    'enabled': False,
                    'broker': '',
                    'port': 1883,
                    'username': '',
                    'password': '',
                    'topic': 'mushroom/tent'
                }
            },
            'pins': {
                'UpperDHT_PIN': 17,
                'LowerDHT_PIN': 23,
                'SCD_SDA_PIN': 2,
                'SCD_SCL_PIN': 3,
                'Display_SDA_PIN': 4,
                'Display_SCL_PIN': 5,
                'FAN_PIN': 12,
                'Relay1_PIN': 18,
                'Relay2_PIN': 24,
                'Relay3_PIN': 25,
                'Relay4_PIN': 6,
                'Relay5_PIN': 26,
                'Relay6_PIN': 19,
                'Relay7_PIN': 13,
                'Relay8_PIN': 16
            },
            'tapo': {
                'enabled': False,
                'devices': []
            },
            'active_profile': 'test'
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            self.config = default_config
            self.logger.info(f"Default configuration created at {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error creating default configuration: {str(e)}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get_config(self, section=None, key=None, default=None):
        """Get configuration value
        
        Args:
            section (str, optional): Configuration section. Defaults to None.
            key (str, optional): Configuration key. Defaults to None.
            default (any, optional): Default value if key is not found. Defaults to None.
            
        Returns:
            any: Configuration value or default
        """
        if section is None:
            return self.config
        
        if key is None:
            return self.config.get(section, {})
        
        return self.config.get(section, {}).get(key, default)
    
    def set_config(self, section, key, value):
        """Set configuration value
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            value (any): Configuration value
            
        Returns:
            bool: True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        return self.save_config()
    
    def get_active_profile(self):
        """Get the active profile
        
        Returns:
            dict: Active profile settings
        """
        profile_name = self.get_config('active_profile', default='test')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data FROM profiles WHERE name = ?
            ''', (profile_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            else:
                self.logger.warning(f"Active profile '{profile_name}' not found, using default")
                return self._get_default_profile('test')
                
        except Exception as e:
            self.logger.error(f"Error getting active profile: {str(e)}")
            return self._get_default_profile('test')
    
    def set_active_profile(self, profile_name):
        """Set the active profile
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if profile exists
            cursor.execute('''
                SELECT COUNT(*) FROM profiles WHERE name = ?
            ''', (profile_name,))
            
            if cursor.fetchone()[0] == 0:
                self.logger.warning(f"Profile '{profile_name}' not found")
                conn.close()
                return False
            
            conn.close()
            
            # Update active profile in config
            result = self.set_config('active_profile', profile_name)
            
            if result:
                self.logger.info(f"Active profile set to '{profile_name}'")
                
                # Notify other components that profile has changed
                if hasattr(self.app, 'component_manager') and self.app.component_manager:
                    # Update relay configurations
                    if hasattr(self.app.component_manager, 'relay_manager'):
                        self.app.component_manager.relay_manager._update_config_from_profile()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error setting active profile: {str(e)}")
            return False
    
    def get_profiles(self):
        """Get all profiles
        
        Returns:
            list: List of profile names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name FROM profiles
            ''')
            
            result = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting profiles: {str(e)}")
            return []
    
    def get_profile(self, profile_name):
        """Get a specific profile
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            dict: Profile settings or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data FROM profiles WHERE name = ?
            ''', (profile_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            else:
                self.logger.warning(f"Profile '{profile_name}' not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting profile: {str(e)}")
            return None
    
    def save_profile(self, profile_name, profile_data):
        """Save a profile
        
        Args:
            profile_name (str): Profile name
            profile_data (dict): Profile settings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = int(time.time())
            
            # Check if profile exists
            cursor.execute('''
                SELECT COUNT(*) FROM profiles WHERE name = ?
            ''', (profile_name,))
            
            if cursor.fetchone()[0] == 0:
                # Create new profile
                cursor.execute('''
                    INSERT INTO profiles (name, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (profile_name, json.dumps(profile_data), current_time, current_time))
            else:
                # Update existing profile
                cursor.execute('''
                    UPDATE profiles SET data = ?, updated_at = ?
                    WHERE name = ?
                ''', (json.dumps(profile_data), current_time, profile_name))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Profile '{profile_name}' saved")
            
            # If this is the active profile, update components
            if profile_name == self.get_config('active_profile'):
                # Update relay configurations
                if hasattr(self.app, 'component_manager') and self.app.component_manager:
                    if hasattr(self.app.component_manager, 'relay_manager'):
                        self.app.component_manager.relay_manager._update_config_from_profile()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving profile: {str(e)}")
            return False
    
    def rename_profile(self, old_name, new_name):
        """Rename a profile
        
        Args:
            old_name (str): Current profile name
            new_name (str): New profile name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if new name already exists
            cursor.execute('''
                SELECT COUNT(*) FROM profiles WHERE name = ?
            ''', (new_name,))
            
            if cursor.fetchone()[0] > 0:
                self.logger.warning(f"Profile '{new_name}' already exists")
                conn.close()
                return False
            
            # Rename profile
            cursor.execute('''
                UPDATE profiles SET name = ?
                WHERE name = ?
            ''', (new_name, old_name))
            
            conn.commit()
            conn.close()
            
            # Update active profile if needed
            if self.get_config('active_profile') == old_name:
                self.set_config('active_profile', new_name)
            
            self.logger.info(f"Profile renamed from '{old_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error renaming profile: {str(e)}")
            return False
    
    def delete_profile(self, profile_name):
        """Delete a profile
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Don't allow deleting default profiles
            if profile_name in ['test', 'colonisation', 'fruiting']:
                self.logger.warning(f"Cannot delete default profile '{profile_name}'")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete profile
            cursor.execute('''
                DELETE FROM profiles WHERE name = ?
            ''', (profile_name,))
            
            conn.commit()
            conn.close()
            
            # Update active profile if needed
            if self.get_config('active_profile') == profile_name:
                self.set_config('active_profile', 'test')
            
            self.logger.info(f"Profile '{profile_name}' deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting profile: {str(e)}")
            return False
    
    def export_profiles(self):
        """Export all profiles
        
        Returns:
            str: JSON string of all profiles or None if error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, data FROM profiles
            ''')
            
            result = cursor.fetchall()
            conn.close()
            
            profiles = {}
            for row in result:
                profiles[row[0]] = json.loads(row[1])
            
            return json.dumps(profiles, indent=4)
            
        except Exception as e:
            self.logger.error(f"Error exporting profiles: {str(e)}")
            return None
    
    def import_profiles(self, profiles_json):
        """Import profiles from JSON
        
        Args:
            profiles_json (str): JSON string of profiles
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profiles = json.loads(profiles_json)
            
            if not isinstance(profiles, dict):
                self.logger.error("Invalid profiles format")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = int(time.time())
            
            for name, data in profiles.items():
                # Check if profile exists
                cursor.execute('''
                    SELECT COUNT(*) FROM profiles WHERE name = ?
                ''', (name,))
                
                if cursor.fetchone()[0] == 0:
                    # Create new profile
                    cursor.execute('''
                        INSERT INTO profiles (name, data, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (name, json.dumps(data), current_time, current_time))
                else:
                    # Update existing profile
                    cursor.execute('''
                        UPDATE profiles SET data = ?, updated_at = ?
                        WHERE name = ?
                    ''', (json.dumps(data), current_time, name))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Imported {len(profiles)} profiles")
            
            # Update active profile if it exists in imported profiles
            active_profile = self.get_config('active_profile')
            if active_profile in profiles:
                # Update relay configurations
                if hasattr(self.app, 'component_manager') and self.app.component_manager:
                    if hasattr(self.app.component_manager, 'relay_manager'):
                        self.app.component_manager.relay_manager._update_config_from_profile()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing profiles: {str(e)}")
            return False
    
    def log_to_database(self, level, component, message):
        """Log a message to the database
        
        Args:
            level (str): Log level
            component (str): Component name
            message (str): Log message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_logs (timestamp, level, component, message)
                VALUES (?, ?, ?, ?)
            ''', (int(time.time()), level, component, message))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging to database: {str(e)}")
            return False
    
    def get_logs(self, limit=100, level=None, component=None):
        """Get logs from the database
        
        Args:
            limit (int, optional): Maximum number of logs to return. Defaults to 100.
            level (str, optional): Filter by log level. Defaults to None.
            component (str, optional): Filter by component. Defaults to None.
            
        Returns:
            list: List of log entries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT timestamp, level, component, message
                FROM system_logs
            '''
            
            params = []
            where_clauses = []
            
            if level:
                where_clauses.append("level = ?")
                params.append(level)
            
            if component:
                where_clauses.append("component = ?")
                params.append(component)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            result = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in result:
                logs.append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'),
                    'level': row[1],
                    'component': row[2],
                    'message': row[3]
                })
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting logs: {str(e)}")
            return []
    
    def clear_logs(self):
        """Clear all logs from the database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM system_logs
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Logs cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing logs: {str(e)}")
            return False
    
    def sync_time(self):
        """Synchronize system time with NTP server
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org', version=3)
            
            # Set system time
            subprocess.call(['sudo', 'date', '-s', 
                            datetime.fromtimestamp(response.tx_time).strftime('%Y-%m-%d %H:%M:%S')])
            
            self.logger.info(f"Time synchronized with NTP server")
            return True
            
        except Exception as e:
            self.logger.error(f"Error synchronizing time: {str(e)}")
            return False
    
    def _time_sync_loop(self):
        """Thread function for periodic time synchronization"""
        self.logger.info("Time synchronization loop started")
        
        while self.running:
            try:
                self.sync_time()
            except Exception as e:
                self.logger.error(f"Error in time sync loop: {str(e)}")
                
            # Sync every 24 hours
            time.sleep(86400)
    
    def _maintenance_loop(self):
        """Thread function for periodic maintenance tasks"""
        self.logger.info("Maintenance loop started")
        
        while self.running:
            try:
                # Check log file size
                log_max_size = self.get_config('system', 'log_max_size', 1024) * 1024  # Convert to bytes
                
                # Prune logs if needed
                self._prune_logs(log_max_size)
                
                # Vacuum database
                self._vacuum_database()
                
                # Check disk space
                self._check_disk_space()
                
            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {str(e)}")
                
            # Run maintenance every hour
            time.sleep(3600)
    
    def _reboot_scheduler_loop(self):
        """Thread function for scheduled reboots"""
        self.logger.info("Reboot scheduler loop started")
        
        while self.running:
            try:
                # Get reboot schedule
                reboot_day = self.get_config('system', 'reboot_day', 0)  # Default: Sunday
                reboot_time = self.get_config('system', 'reboot_time', '04:00')
                
                # Parse reboot time
                reboot_hour, reboot_minute = map(int, reboot_time.split(':'))
                
                # Get current time
                now = datetime.now()
                
                # Check if it's time to reboot
                if (now.weekday() == reboot_day and 
                    now.hour == reboot_hour and 
                    now.minute == reboot_minute):
                    self.logger.info("Scheduled reboot initiated")
                    self.reboot_system()
                
            except Exception as e:
                self.logger.error(f"Error in reboot scheduler loop: {str(e)}")
                
            # Check every minute
            time.sleep(60)
    
    def _fan_control_loop(self):
        """Thread function for CPU fan control"""
        self.logger.info("Fan control loop started")
        
        # Set up fan pin
        GPIO.setup(self.fan_pin, GPIO.OUT)
        
        # Set up PWM
        fan_pwm = GPIO.PWM(self.fan_pin, 100)  # 100 Hz frequency
        fan_pwm.start(0)  # Start with 0% duty cycle (off)
        
        while self.running:
            try:
                # Read CPU temperature
                cpu_temp = self._get_cpu_temperature()
                
                # Set fan speed based on temperature
                duty_cycle = self._calculate_fan_duty_cycle(cpu_temp)
                
                # Apply PWM
                fan_pwm.ChangeDutyCycle(duty_cycle)
                
                # Log temperature and fan speed periodically
                self.logger.debug(f"CPU Temperature: {cpu_temp:.1f}°C, Fan Speed: {duty_cycle}%")
                
            except Exception as e:
                self.logger.error(f"Error in fan control loop: {str(e)}")
                
            # Check every 5 seconds
            time.sleep(5)
        
        # Clean up
        fan_pwm.stop()
    
    def _get_cpu_temperature(self):
        """Get CPU temperature
        
        Returns:
            float: CPU temperature in degrees Celsius
        """
        try:
            # Read temperature from system file
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
            
            return temp
            
        except Exception as e:
            self.logger.error(f"Error reading CPU temperature: {str(e)}")
            return 0.0
    
    def _calculate_fan_duty_cycle(self, cpu_temp):
        """Calculate fan duty cycle based on CPU temperature
        
        Args:
            cpu_temp (float): CPU temperature in degrees Celsius
            
        Returns:
            int: Fan duty cycle (0-100)
        """
        # Define temperature thresholds
        temp_min = 40.0  # Below this temperature, fan is off
        temp_max = 70.0  # Above this temperature, fan is at 100%
        
        # Calculate duty cycle
        if cpu_temp < temp_min:
            return 0
        elif cpu_temp > temp_max:
            return 100
        else:
            # Linear interpolation between min and max
            return int((cpu_temp - temp_min) / (temp_max - temp_min) * 100)
    
    def _prune_logs(self, max_size):
        """Prune logs if they exceed the maximum size
        
        Args:
            max_size (int): Maximum log size in bytes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current log size
            cursor.execute('''
                SELECT COUNT(*) FROM system_logs
            ''')
            
            log_count = cursor.fetchone()[0]
            
            # Estimate log size (assuming average 200 bytes per log entry)
            estimated_size = log_count * 200
            
            if estimated_size > max_size:
                # Calculate how many logs to delete
                logs_to_delete = int((estimated_size - max_size * 0.8) / 200)
                
                # Keep at least 100 logs
                logs_to_delete = min(logs_to_delete, log_count - 100)
                
                if logs_to_delete > 0:
                    # Delete oldest logs
                    cursor.execute('''
                        DELETE FROM system_logs
                        WHERE id IN (
                            SELECT id FROM system_logs
                            ORDER BY timestamp ASC
                            LIMIT ?
                        )
                    ''', (logs_to_delete,))
                    
                    conn.commit()
                    self.logger.info(f"Pruned {logs_to_delete} old log entries")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error pruning logs: {str(e)}")
    
    def _vacuum_database(self):
        """Vacuum SQLite database to reclaim space"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            
            self.logger.debug("Database vacuumed")
            
        except Exception as e:
            self.logger.error(f"Error vacuuming database: {str(e)}")
    
    def _check_disk_space(self):
        """Check available disk space and log warning if low"""
        try:
            stat = os.statvfs('/')
            
            # Calculate free space in MB
            free_space = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            
            if free_space < 100:  # Less than 100 MB
                self.logger.warning(f"Low disk space: {free_space:.2f} MB available")
                
                # Send notification if very low
                if free_space < 50:  # Less than 50 MB
                    self.send_notification("Low Disk Space", f"Only {free_space:.2f} MB available")
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {str(e)}")
    
    def send_notification(self, title, message):
        """Send system notification
        
        Args:
            title (str): Notification title
            message (str): Notification message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log notification
            self.logger.info(f"Notification: {title} - {message}")
            
            # Store in database
            self.log_to_database("NOTIFICATION", "SystemManager", f"{title}: {message}")
            
            # TODO: Implement actual notification methods (Telegram, etc.)
            # For now, just log it
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def reboot_system(self):
        """Reboot the system
        
        Returns:
            bool: True if reboot initiated, False otherwise
        """
        try:
            self.logger.info("System reboot initiated")
            
            # Perform clean shutdown
            self.app.stop()
            
            # Reboot system
            subprocess.call(['sudo', 'reboot'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error rebooting system: {str(e)}")
            return False
    
    def factory_reset(self):
        """Reset system to factory defaults
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Factory reset initiated")
            
            # Delete database
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            
            # Delete configuration
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            
            # Delete WiFi credentials
            wifi_credentials_path = 'config/wifi_credentials.json'
            if os.path.exists(wifi_credentials_path):
                os.remove(wifi_credentials_path)
            
            # Reinitialize database
            self._init_database()
            
            # Create default configuration
            self._create_default_config()
            
            # Reboot system
            return self.reboot_system()
            
        except Exception as e:
            self.logger.error(f"Error performing factory reset: {str(e)}")
            return False
    
    def get_system_info(self):
        """Get system information
        
        Returns:
            dict: System information
        """
        try:
            # Get system uptime
            uptime_seconds = float(open('/proc/uptime', 'r').readline().split()[0])
            uptime_days = int(uptime_seconds / 86400)
            uptime_hours = int((uptime_seconds % 86400) / 3600)
            uptime_minutes = int((uptime_seconds % 3600) / 60)
            
            # Format uptime
            uptime = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
            
            # Get memory info
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 * 1024)  # MB
            memory_used = memory.used / (1024 * 1024)    # MB
            memory_free = memory.available / (1024 * 1024)  # MB
            memory_percent = memory.percent
            
            # Get disk info
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 * 1024)  # MB
            disk_used = disk.used / (1024 * 1024)    # MB
            disk_free = disk.free / (1024 * 1024)    # MB
            disk_percent = disk.percent
            
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_temp = self._get_cpu_temperature()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
            
            # Get network info
            network_info = {}
            try:
                # Get current WiFi info
                if hasattr(self.app, 'network_manager'):
                    wifi_info = self.app.network_manager.get_wifi_info()
                    if wifi_info:
                        network_info = wifi_info
            except:
                pass
            
            # Get version info
            version_info = {
                'system': self.get_config('system', 'version', '1.0.0'),
                'firmware': '1.0.0'  # TODO: Implement OTA version tracking
            }
            
            return {
                'uptime': uptime,
                'memory': {
                    'total': round(memory_total, 2),
                    'used': round(memory_used, 2),
                    'free': round(memory_free, 2),
                    'percent': memory_percent
                },
                'disk': {
                    'total': round(disk_total, 2),
                    'used': round(disk_used, 2),
                    'free': round(disk_free, 2),
                    'percent': disk_percent
                },
                'cpu': {
                    'percent': cpu_percent,
                    'temperature': round(cpu_temp, 1),
                    'frequency': round(cpu_freq, 1)
                },
                'network': network_info,
                'version': version_info
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {
                'error': str(e)
            }
    
    def start(self):
        """Start the System Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start time synchronization thread
        self.time_sync_thread = threading.Thread(target=self._time_sync_loop)
        self.time_sync_thread.daemon = True
        self.time_sync_thread.start()
        
        # Start maintenance thread
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop)
        self.maintenance_thread.daemon = True
        self.maintenance_thread.start()
        
        # Start reboot scheduler thread
        self.reboot_scheduler_thread = threading.Thread(target=self._reboot_scheduler_loop)
        self.reboot_scheduler_thread.daemon = True
        self.reboot_scheduler_thread.start()
        
        # Start fan control thread
        self.fan_control_thread = threading.Thread(target=self._fan_control_loop)
        self.fan_control_thread.daemon = True
        self.fan_control_thread.start()
        
        self.logger.info("System Manager started")
    
    def stop(self):
        """Stop the System Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for threads to terminate
        if self.time_sync_thread and self.time_sync_thread.is_alive():
            self.time_sync_thread.join(timeout=2)
        
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            self.maintenance_thread.join(timeout=2)
        
        if self.reboot_scheduler_thread and self.reboot_scheduler_thread.is_alive():
            self.reboot_scheduler_thread.join(timeout=2)
        
        if self.fan_control_thread and self.fan_control_thread.is_alive():
            self.fan_control_thread.join(timeout=2)
        
        self.logger.info("System Manager stopped")