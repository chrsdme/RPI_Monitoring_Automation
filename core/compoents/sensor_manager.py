#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor Manager Module

This module handles all sensor-related functionality, including:
- DHT22 temperature and humidity sensors (2x)
- SCD40 CO2, temperature, and humidity sensor
- SSD1306 OLED display

Features:
- Comprehensive initialization for all sensors
- Complex error handling and recovery
- Multi-threaded sensor reading
- Data validation and processing
"""

import os
import time
import logging
import threading
import json
import queue
from datetime import datetime
import board
import busio
import RPi.GPIO as GPIO
import adafruit_dht
import adafruit_scd4x
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

class SensorManager:
    """Sensor Manager class for managing hardware sensors"""
    
    def __init__(self, component_manager):
        """Initialize the Sensor Manager
        
        Args:
            component_manager: Component manager instance
        """
        self.component_manager = component_manager
        self.app = component_manager.app
        self.logger = logging.getLogger('SensorManager')
        
        # Get pin configurations from config
        self.config = self.app.system_manager.get_config()
        
        # Initialize sensor objects
        self.upper_dht = None
        self.lower_dht = None
        self.scd40 = None
        self.display = None
        
        # Initialize I2C busses
        self.i2c1 = None  # For SCD40
        self.i2c2 = None  # For Display
        
        # Initialize sensor data
        self.sensor_data = {
            'upper_dht': {
                'temperature': 0,
                'humidity': 0,
                'last_read': 0,
                'errors': 0
            },
            'lower_dht': {
                'temperature': 0,
                'humidity': 0,
                'last_read': 0,
                'errors': 0
            },
            'scd40': {
                'temperature': 0,
                'humidity': 0,
                'co2': 0,
                'last_read': 0,
                'errors': 0
            }
        }
        
        # Initialize flags
        self.running = False
        self.display_running = False
        
        # Initialize threads
        self.dht_thread = None
        self.scd_thread = None
        self.display_thread = None
        
        # Message queue for display
        self.display_queue = queue.Queue(maxsize=5)
        
        # Load display configurations
        self.display_width = 128
        self.display_height = 64
        self.display_address = 0x3C  # Default I2C address for SSD1306
        
        # Reading intervals
        self.dht_interval = 30  # Default: 30 seconds
        self.scd_interval = 30  # Default: 30 seconds
        self.display_interval = 5  # Default: 5 seconds
        
        # Error thresholds
        self.error_threshold = 5  # Default: 5 consecutive errors
        
        # Load fonts for display
        try:
            # Load default font
            self.font = ImageFont.load_default()
            
            # Try to load a nicer font if available
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if os.path.exists(font_path):
                self.font_small = ImageFont.truetype(font_path, 8)
                self.font_medium = ImageFont.truetype(font_path, 10)
                self.font_large = ImageFont.truetype(font_path, 12)
            else:
                self.font_small = self.font
                self.font_medium = self.font
                self.font_large = self.font
                
        except Exception as e:
            self.logger.warning(f"Error loading fonts: {str(e)}, using default font")
            self.font_small = self.font
            self.font_medium = self.font
            self.font_large = self.font
    
    def initialize(self):
        """Initialize all sensors
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Initializing sensors")
        
        try:
            # Update reading intervals from config
            profile = self.app.system_manager.get_active_profile()
            self.dht_interval = profile.get('dht_sensor_interval', 30)
            self.scd_interval = profile.get('scd40_sensor_interval', 30)
            
            # Get error threshold from config
            self.error_threshold = self.app.system_manager.get_config('system', 'sensor_error_threshold', 5)
            
            # Get pin configurations from config
            pins = self.app.system_manager.get_config('pins', {})
            
            # Initialize DHT22 sensors
            upper_dht_pin = pins.get('UpperDHT_PIN', 17)
            lower_dht_pin = pins.get('LowerDHT_PIN', 23)
            
            # Set pins for use with the Adafruit DHT library
            self.upper_dht_pin = upper_dht_pin
            self.lower_dht_pin = lower_dht_pin
            
            # Initialize I2C busses
            scd_sda_pin = pins.get('SCD_SDA_PIN', 2)
            scd_scl_pin = pins.get('SCD_SCL_PIN', 3)
            
            display_sda_pin = pins.get('Display_SDA_PIN', 4)
            display_scl_pin = pins.get('Display_SCL_PIN', 5)
            
            # Log pin configurations
            self.logger.info(f"Upper DHT pin: {upper_dht_pin}")
            self.logger.info(f"Lower DHT pin: {lower_dht_pin}")
            self.logger.info(f"SCD40 SDA pin: {scd_sda_pin}, SCL pin: {scd_scl_pin}")
            self.logger.info(f"Display SDA pin: {display_sda_pin}, SCL pin: {display_scl_pin}")
            
            # Initialize DHT sensors
            try:
                self.logger.info("Initializing DHT sensors")
                
                # Clean up any existing instances
                if self.upper_dht:
                    self.upper_dht.exit()
                if self.lower_dht:
                    self.lower_dht.exit()
                
                # Create new instances
                self.upper_dht = adafruit_dht.DHT22(getattr(board, f"D{upper_dht_pin}"))
                self.lower_dht = adafruit_dht.DHT22(getattr(board, f"D{lower_dht_pin}"))
                
                self.logger.info("DHT sensors initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing DHT sensors: {str(e)}")
                return False
            
            # Initialize I2C1 for SCD40
            try:
                self.logger.info("Initializing I2C1 for SCD40")
                
                # Create I2C bus for SCD40
                self.i2c1 = busio.I2C(getattr(board, f"D{scd_scl_pin}"), getattr(board, f"D{scd_sda_pin}"))
                
                # Create SCD40 sensor
                self.scd40 = adafruit_scd4x.SCD4X(self.i2c1)
                
                # Stop any measurements that might be running
                self.scd40.stop_periodic_measurement()
                
                # Set up the sensor
                time.sleep(1)
                self.scd40.start_periodic_measurement()
                time.sleep(1)
                
                self.logger.info("SCD40 sensor initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing SCD40 sensor: {str(e)}")
                return False
            
            # Initialize I2C2 for Display
            try:
                self.logger.info("Initializing I2C2 for Display")
                
                # Create I2C bus for Display
                self.i2c2 = busio.I2C(getattr(board, f"D{display_scl_pin}"), getattr(board, f"D{display_sda_pin}"))
                
                # Create display instance
                self.display = adafruit_ssd1306.SSD1306_I2C(
                    self.display_width, self.display_height, self.i2c2, addr=self.display_address)
                
                # Clear the display
                self.display.fill(0)
                self.display.show()
                
                # Display initialization message
                self._draw_text("Mushroom Tent", "Controller", "Initializing...")
                
                self.logger.info("SSD1306 display initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing SSD1306 display: {str(e)}")
                # Display is not critical, continue without it
                self.display = None
            
            self.logger.info("All sensors initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing sensors: {str(e)}")
            return False
    
    def start(self):
        """Start sensor reading threads"""
        if self.running:
            return
        
        self.running = True
        self.display_running = True
        
        # Start DHT reading thread
        self.dht_thread = threading.Thread(target=self._dht_reading_loop)
        self.dht_thread.daemon = True
        self.dht_thread.start()
        
        # Start SCD reading thread
        self.scd_thread = threading.Thread(target=self._scd_reading_loop)
        self.scd_thread.daemon = True
        self.scd_thread.start()
        
        # Start display thread
        if self.display:
            self.display_thread = threading.Thread(target=self._display_loop)
            self.display_thread.daemon = True
            self.display_thread.start()
        
        self.logger.info("Sensor Manager started")
    
    def stop(self):
        """Stop sensor reading threads"""
        if not self.running:
            return
        
        self.running = False
        self.display_running = False
        
        # Wait for threads to terminate
        if self.dht_thread and self.dht_thread.is_alive():
            self.dht_thread.join(timeout=2)
        
        if self.scd_thread and self.scd_thread.is_alive():
            self.scd_thread.join(timeout=2)
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)
        
        # Clean up resources
        try:
            if self.upper_dht:
                self.upper_dht.exit()
            
            if self.lower_dht:
                self.lower_dht.exit()
            
            if self.scd40:
                self.scd40.stop_periodic_measurement()
            
            if self.display:
                self.display.fill(0)
                self.display.show()
        except Exception as e:
            self.logger.error(f"Error cleaning up sensors: {str(e)}")
        
        self.logger.info("Sensor Manager stopped")
    
    def _dht_reading_loop(self):
        """Thread function for reading DHT sensors"""
        self.logger.info("DHT reading loop started")
        
        # Allow 5 seconds for sensor warm-up
        self.logger.info("Waiting 5 seconds for DHT sensors to warm up")
        time.sleep(5)
        
        errors_upper = 0
        errors_lower = 0
        
        while self.running:
            try:
                # Update reading interval from config
                self.dht_interval = self.app.system_manager.get_active_profile().get('dht_sensor_interval', 30)
                
                # Read upper DHT
                try:
                    temperature = self.upper_dht.temperature
                    humidity = self.upper_dht.humidity
                    
                    if temperature is not None and humidity is not None:
                        self.sensor_data['upper_dht']['temperature'] = temperature
                        self.sensor_data['upper_dht']['humidity'] = humidity
                        self.sensor_data['upper_dht']['last_read'] = time.time()
                        errors_upper = 0  # Reset error counter
                        
                        self.logger.debug(f"Upper DHT: Temperature={temperature:.1f}°C, Humidity={humidity:.1f}%")
                    else:
                        errors_upper += 1
                        self.logger.warning(f"Invalid reading from Upper DHT (error {errors_upper})")
                
                except Exception as e:
                    errors_upper += 1
                    self.logger.warning(f"Error reading Upper DHT: {str(e)} (error {errors_upper})")
                
                # Update error count
                self.sensor_data['upper_dht']['errors'] = errors_upper
                
                # Check error threshold for upper DHT
                if errors_upper >= self.error_threshold:
                    self.logger.error(f"Upper DHT exceeded error threshold ({errors_upper}), attempting recovery")
                    try:
                        # Clean up
                        self.upper_dht.exit()
                        time.sleep(1)
                        
                        # Reinitialize
                        self.upper_dht = adafruit_dht.DHT22(getattr(board, f"D{self.upper_dht_pin}"))
                        errors_upper = 0
                        self.logger.info("Upper DHT recovery attempted")
                    except Exception as e:
                        self.logger.error(f"Failed to recover Upper DHT: {str(e)}")
                
                # Sleep a bit before reading the second sensor to avoid I/O conflicts
                time.sleep(2)
                
                # Read lower DHT
                try:
                    temperature = self.lower_dht.temperature
                    humidity = self.lower_dht.humidity
                    
                    if temperature is not None and humidity is not None:
                        self.sensor_data['lower_dht']['temperature'] = temperature
                        self.sensor_data['lower_dht']['humidity'] = humidity
                        self.sensor_data['lower_dht']['last_read'] = time.time()
                        errors_lower = 0  # Reset error counter
                        
                        self.logger.debug(f"Lower DHT: Temperature={temperature:.1f}°C, Humidity={humidity:.1f}%")
                    else:
                        errors_lower += 1
                        self.logger.warning(f"Invalid reading from Lower DHT (error {errors_lower})")
                
                except Exception as e:
                    errors_lower += 1
                    self.logger.warning(f"Error reading Lower DHT: {str(e)} (error {errors_lower})")
                
                # Update error count
                self.sensor_data['lower_dht']['errors'] = errors_lower
                
                # Check error threshold for lower DHT
                if errors_lower >= self.error_threshold:
                    self.logger.error(f"Lower DHT exceeded error threshold ({errors_lower}), attempting recovery")
                    try:
                        # Clean up
                        self.lower_dht.exit()
                        time.sleep(1)
                        
                        # Reinitialize
                        self.lower_dht = adafruit_dht.DHT22(getattr(board, f"D{self.lower_dht_pin}"))
                        errors_lower = 0
                        self.logger.info("Lower DHT recovery attempted")
                    except Exception as e:
                        self.logger.error(f"Failed to recover Lower DHT: {str(e)}")
                
                # Publish readings via MQTT if connected
                if self.app.network_manager.mqtt_connected:
                    self.app.network_manager.publish_sensor_data()
                
                # Update display queue with latest readings
                if self.display:
                    try:
                        # Add to display queue if not full
                        if not self.display_queue.full():
                            self.display_queue.put("sensor_update", block=False)
                    except Exception:
                        pass
                
                # Sleep until next reading
                time.sleep(self.dht_interval)
                
            except Exception as e:
                self.logger.error(f"Error in DHT reading loop: {str(e)}")
                time.sleep(10)  # Longer delay after error
    
    def _scd_reading_loop(self):
        """Thread function for reading SCD40 sensor"""
        self.logger.info("SCD reading loop started")
        
        # Allow 5 seconds for sensor warm-up
        self.logger.info("Waiting 5 seconds for SCD40 sensor to warm up")
        time.sleep(5)
        
        errors = 0
        
        while self.running:
            try:
                # Update reading interval from config
                self.scd_interval = self.app.system_manager.get_active_profile().get('scd40_sensor_interval', 30)
                
                # Check if data is ready
                if self.scd40.data_ready:
                    try:
                        # Read sensor data
                        co2 = self.scd40.CO2
                        temperature = self.scd40.temperature
                        humidity = self.scd40.relative_humidity
                        
                        if co2 is not None and temperature is not None and humidity is not None:
                            self.sensor_data['scd40']['co2'] = co2
                            self.sensor_data['scd40']['temperature'] = temperature
                            self.sensor_data['scd40']['humidity'] = humidity
                            self.sensor_data['scd40']['last_read'] = time.time()
                            errors = 0  # Reset error counter
                            
                            self.logger.debug(f"SCD40: CO2={co2}ppm, Temperature={temperature:.1f}°C, Humidity={humidity:.1f}%")
                        else:
                            errors += 1
                            self.logger.warning(f"Invalid reading from SCD40 (error {errors})")
                    
                    except Exception as e:
                        errors += 1
                        self.logger.warning(f"Error reading SCD40: {str(e)} (error {errors})")
                else:
                    self.logger.debug("SCD40 data not ready yet")
                
                # Update error count
                self.sensor_data['scd40']['errors'] = errors
                
                # Check error threshold
                if errors >= self.error_threshold:
                    self.logger.error(f"SCD40 exceeded error threshold ({errors}), attempting recovery")
                    try:
                        # Stop measurements
                        self.scd40.stop_periodic_measurement()
                        time.sleep(1)
                        
                        # Restart measurements
                        self.scd40.start_periodic_measurement()
                        errors = 0
                        self.logger.info("SCD40 recovery attempted")
                    except Exception as e:
                        self.logger.error(f"Failed to recover SCD40: {str(e)}")
                
                # Sleep until next reading
                time.sleep(self.scd_interval)
                
            except Exception as e:
                self.logger.error(f"Error in SCD reading loop: {str(e)}")
                time.sleep(10)  # Longer delay after error
    
    def _display_loop(self):
        """Thread function for updating the OLED display"""
        self.logger.info("Display loop started")
        
        # Display initialization message
        self._draw_text("Mushroom Tent", "Controller", "Started")
        time.sleep(2)
        
        display_mode = 0  # Rotate between different display modes
        last_update = 0
        
        while self.display_running:
            try:
                # Check if there's an update request in the queue
                try:
                    message = self.display_queue.get(block=False)
                    if message == "sensor_update":
                        last_update = time.time()
                except queue.Empty:
                    pass
                
                # Update display based on current mode
                if display_mode == 0:
                    # Display temperatures
                    temp_upper = self.sensor_data['upper_dht']['temperature']
                    temp_lower = self.sensor_data['lower_dht']['temperature']
                    temp_scd = self.sensor_data['scd40']['temperature']
                    
                    # Calculate average
                    temps = [t for t in [temp_upper, temp_lower, temp_scd] if t != 0]
                    avg_temp = sum(temps) / len(temps) if temps else 0
                    
                    self._draw_text(
                        f"Temp U: {temp_upper:.1f}°C",
                        f"Temp L: {temp_lower:.1f}°C",
                        f"Temp S: {temp_scd:.1f}°C",
                        f"Avg: {avg_temp:.1f}°C"
                    )
                
                elif display_mode == 1:
                    # Display humidity
                    hum_upper = self.sensor_data['upper_dht']['humidity']
                    hum_lower = self.sensor_data['lower_dht']['humidity']
                    hum_scd = self.sensor_data['scd40']['humidity']
                    
                    # Calculate average
                    hums = [h for h in [hum_upper, hum_lower, hum_scd] if h != 0]
                    avg_hum = sum(hums) / len(hums) if hums else 0
                    
                    self._draw_text(
                        f"Hum U: {hum_upper:.1f}%",
                        f"Hum L: {hum_lower:.1f}%",
                        f"Hum S: {hum_scd:.1f}%",
                        f"Avg: {avg_hum:.1f}%"
                    )
                
                elif display_mode == 2:
                    # Display CO2 and system info
                    co2 = self.sensor_data['scd40']['co2']
                    
                    # Get network info
                    ip = "Not connected"
                    ssid = "Not connected"
                    try:
                        network_info = self.app.network_manager.get_wifi_info()
                        if network_info.get('connected'):
                            ip = network_info.get('ip', 'Unknown')
                            ssid = network_info.get('ssid', 'Unknown')
                    except Exception:
                        pass
                    
                    self._draw_text(
                        f"CO2: {co2} ppm",
                        f"SSID: {ssid}",
                        f"IP: {ip}"
                    )
                
                # Rotate display mode every 5 seconds
                display_mode = (display_mode + 1) % 3
                
                # Sleep until next update
                time.sleep(self.display_interval)
                
            except Exception as e:
                self.logger.error(f"Error in display loop: {str(e)}")
                time.sleep(10)  # Longer delay after error
    
    def _draw_text(self, *lines):
        """Draw text on the OLED display
        
        Args:
            *lines: Lines of text to display
        """
        if not self.display:
            return
        
        try:
            # Create image buffer
            image = Image.new("1", (self.display_width, self.display_height))
            draw = ImageDraw.Draw(image)
            
            # Clear the display
            draw.rectangle((0, 0, self.display_width, self.display_height), outline=0, fill=0)
            
            # Draw each line of text
            y_pos = 0
            for line in lines:
                draw.text((0, y_pos), line, font=self.font_medium, fill=255)
                y_pos += 12  # Line spacing
            
            # Display the image
            self.display.image(image)
            self.display.show()
            
        except Exception as e:
            self.logger.error(f"Error drawing to display: {str(e)}")
    
    def get_all_readings(self):
        """Get all sensor readings
        
        Returns:
            dict: Dictionary of all sensor readings
        """
        return self.sensor_data
    
    def get_average_temperature(self):
        """Calculate average temperature from all sensors
        
        Returns:
            float: Average temperature
        """
        temps = [
            self.sensor_data['upper_dht']['temperature'],
            self.sensor_data['lower_dht']['temperature'],
            self.sensor_data['scd40']['temperature']
        ]
        
        # Filter out zero values
        valid_temps = [t for t in temps if t != 0]
        
        # Calculate average
        return sum(valid_temps) / len(valid_temps) if valid_temps else 0
    
    def get_average_humidity(self):
        """Calculate average humidity from all sensors
        
        Returns:
            float: Average humidity
        """
        humidities = [
            self.sensor_data['upper_dht']['humidity'],
            self.sensor_data['lower_dht']['humidity'],
            self.sensor_data['scd40']['humidity']
        ]
        
        # Filter out zero values
        valid_humidities = [h for h in humidities if h != 0]
        
        # Calculate average
        return sum(valid_humidities) / len(valid_humidities) if valid_humidities else 0
    
    def reset_error_counts(self):
        """Reset error counters for all sensors"""
        self.sensor_data['upper_dht']['errors'] = 0
        self.sensor_data['lower_dht']['errors'] = 0
        self.sensor_data['scd40']['errors'] = 0
        
        self.logger.info("Sensor error counts reset")
    
    def display_message(self, *lines):
        """Display a message on the OLED display
        
        Args:
            *lines: Lines of text to display
        """
        if not self.display:
            return False
        
        try:
            # Add to display queue if not full
            if not self.display_queue.full():
                # Remove any pending display updates
                while not self.display_queue.empty():
                    try:
                        self.display_queue.get_nowait()
                    except queue.Empty:
                        break
                
                # Draw text immediately
                self._draw_text(*lines)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error displaying message: {str(e)}")
            return False
    
    def test_sensors(self):
        """Test all sensors
        
        Returns:
            dict: Test results
        """
        results = {
            'upper_dht': {'status': 'failed', 'message': ''},
            'lower_dht': {'status': 'failed', 'message': ''},
            'scd40': {'status': 'failed', 'message': ''},
            'display': {'status': 'failed', 'message': ''}
        }
        
        # Display test message
        if self.display:
            self.display_message("Sensor Testing", "In Progress...")
        
        # Test Upper DHT
        try:
            temperature = self.upper_dht.temperature
            humidity = self.upper_dht.humidity
            
            if temperature is not None and humidity is not None:
                results['upper_dht'] = {
                    'status': 'passed',
                    'message': f"Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%"
                }
            else:
                results['upper_dht'] = {
                    'status': 'failed',
                    'message': "Returned null values"
                }
        except Exception as e:
            results['upper_dht'] = {
                'status': 'failed',
                'message': str(e)
            }
        
        # Test Lower DHT
        try:
            temperature = self.lower_dht.temperature
            humidity = self.lower_dht.humidity
            
            if temperature is not None and humidity is not None:
                results['lower_dht'] = {
                    'status': 'passed',
                    'message': f"Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%"
                }
            else:
                results['lower_dht'] = {
                    'status': 'failed',
                    'message': "Returned null values"
                }
        except Exception as e:
            results['lower_dht'] = {
                'status': 'failed',
                'message': str(e)
            }
        
        # Test SCD40
        try:
            if self.scd40.data_ready:
                co2 = self.scd40.CO2
                temperature = self.scd40.temperature
                humidity = self.scd40.relative_humidity
                
                if co2 is not None and temperature is not None and humidity is not None:
                    results['scd40'] = {
                        'status': 'passed',
                        'message': f"CO2: {co2}ppm, Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%"
                    }
                else:
                    results['scd40'] = {
                        'status': 'failed',
                        'message': "Returned null values"
                    }
            else:
                results['scd40'] = {
                    'status': 'warning',
                    'message': "Data not ready yet"
                }
        except Exception as e:
            results['scd40'] = {
                'status': 'failed',
                'message': str(e)
            }
        
        # Test Display
        if self.display:
            try:
                self._draw_text("Test Successful", datetime.now().strftime("%H:%M:%S"))
                results['display'] = {
                    'status': 'passed',
                    'message': "Display working"
                }
            except Exception as e:
                results['display'] = {
                    'status': 'failed',
                    'message': str(e)
                }
        else:
            results['display'] = {
                'status': 'skipped',
                'message': "Display not initialized"
            }
        
        # Log results
        self.logger.info(f"Sensor test results: {json.dumps(results)}")
        
        # Display test results
        if self.display:
            upper_status = "✓" if results['upper_dht']['status'] == 'passed' else "✗"
            lower_status = "✓" if results['lower_dht']['status'] == 'passed' else "✗"
            scd_status = "✓" if results['scd40']['status'] == 'passed' else "✗"
            
            self.display_message(
                "Sensor Test Results:",
                f"Upper DHT: {upper_status}",
                f"Lower DHT: {lower_status}",
                f"SCD40: {scd_status}"
            )
        
        return results
    
    def calibrate_scd40(self, target_co2=400):
        """Calibrate the SCD40 sensor
        
        Args:
            target_co2 (int): Target CO2 level for calibration (typically 400ppm for fresh air)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.scd40:
            self.logger.error("SCD40 sensor not initialized")
            return False
        
        try:
            self.logger.info(f"Calibrating SCD40 to {target_co2} ppm")
            
            # Display calibration message
            if self.display:
                self.display_message(
                    "SCD40 Calibration",
                    "In Progress...",
                    f"Target: {target_co2} ppm"
                )
            
            # Stop measurements
            self.scd40.stop_periodic_measurement()
            time.sleep(1)
            
            # Perform forced recalibration
            self.scd40.factory_reset()
            time.sleep(1)
            
            # Set forced calibration value
            self.scd40.set_forced_recalibration_reference(target_co2)
            time.sleep(1)
            
            # Restart measurements
            self.scd40.start_periodic_measurement()
            
            self.logger.info("SCD40 calibration completed")
            
            # Display completion message
            if self.display:
                self.display_message(
                    "SCD40 Calibration",
                    "Completed",
                    "Resuming normal operation"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error calibrating SCD40: {str(e)}")
            
            # Display error message
            if self.display:
                self.display_message(
                    "SCD40 Calibration",
                    "Failed",
                    str(e)
                )
            
            # Try to restart measurements
            try:
                self.scd40.start_periodic_measurement()
            except Exception:
                pass
            
            return False
    
    def factory_reset(self):
        """Perform factory reset on sensors
        
        Returns:
            bool: True if successful, False otherwise
        """
        success = True
        
        # Display reset message
        if self.display:
            self.display_message(
                "Factory Reset",
                "In Progress...",
                "Please wait"
            )
        
        # Reset SCD40
        try:
            self.logger.info("Factory resetting SCD40")
            
            # Stop measurements
            self.scd40.stop_periodic_measurement()
            time.sleep(1)
            
            # Factory reset
            self.scd40.factory_reset()
            time.sleep(1)
            
            # Restart measurements
            self.scd40.start_periodic_measurement()
            
            self.logger.info("SCD40 factory reset completed")
        except Exception as e:
            self.logger.error(f"Error factory resetting SCD40: {str(e)}")
            success = False
        
        # Reset DHT sensors (no factory reset available, just reinitialize)
        try:
            self.logger.info("Reinitializing DHT sensors")
            
            # Clean up existing instances
            if self.upper_dht:
                self.upper_dht.exit()
            if self.lower_dht:
                self.lower_dht.exit()
            
            time.sleep(1)
            
            # Create new instances
            self.upper_dht = adafruit_dht.DHT22(getattr(board, f"D{self.upper_dht_pin}"))
            self.lower_dht = adafruit_dht.DHT22(getattr(board, f"D{self.lower_dht_pin}"))
            
            self.logger.info("DHT sensors reinitialized")
        except Exception as e:
            self.logger.error(f"Error reinitializing DHT sensors: {str(e)}")
            success = False
        
        # Display completion message
        if self.display:
            if success:
                self.display_message(
                    "Factory Reset",
                    "Completed",
                    "Resuming operation"
                )
            else:
                self.display_message(
                    "Factory Reset",
                    "Completed with Errors",
                    "Check logs for details"
                )
        
        # Reset sensor data
        self.sensor_data = {
            'upper_dht': {
                'temperature': 0,
                'humidity': 0,
                'last_read': 0,
                'errors': 0
            },
            'lower_dht': {
                'temperature': 0,
                'humidity': 0,
                'last_read': 0,
                'errors': 0
            },
            'scd40': {
                'temperature': 0,
                'humidity': 0,
                'co2': 0,
                'last_read': 0,
                'errors': 0
            }
        }
        
        return success