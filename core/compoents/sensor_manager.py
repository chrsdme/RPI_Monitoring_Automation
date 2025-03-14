class SensorManager:
    def __init__(self, component_manager):
        self.component_manager = component_manager
        self.app = component_manager.app
        self.config = self.app.config
        
        self.dht22_upper = None
        self.dht22_lower = None
        self.scd40 = None
        self.display = None
        
        self.dht_thread = None
        self.scd_thread = None
        self.display_thread = None
        
        self.running = False
        self.readings = {
            'upper_dht': {'temperature': 0, 'humidity': 0, 'last_read': 0, 'errors': 0},
            'lower_dht': {'temperature': 0, 'humidity': 0, 'last_read': 0, 'errors': 0},
            'scd40': {'temperature': 0, 'humidity': 0, 'co2': 0, 'last_read': 0, 'errors': 0}
        }
        
    def initialize(self):
        """Initialize all sensors"""
        try:
            # Initialize DHT22 sensors
            import adafruit_dht
            import board
            
            # Get pin configurations from config
            upper_dht_pin = self.config.get('pins', 'UpperDHT_PIN')
            lower_dht_pin = self.config.get('pins', 'LowerDHT_PIN')
            
            # Initialize sensors
            self.dht22_upper = adafruit_dht.DHT22(getattr(board, f"D{upper_dht_pin}"))
            self.dht22_lower = adafruit_dht.DHT22(getattr(board, f"D{lower_dht_pin}"))
            
            # Initialize SCD40 sensor
            import adafruit_scd4x
            import busio
            
            # Get I2C configurations
            scd_sda_pin = self.config.get('pins', 'SCD_SDA_PIN')
            scd_scl_pin = self.config.get('pins', 'SCD_SCL_PIN')
            
            # Create I2C interface
            i2c = busio.I2C(getattr(board, f"D{scd_scl_pin}"), getattr(board, f"D{scd_sda_pin}"))
            self.scd40 = adafruit_scd4x.SCD4X(i2c)
            self.scd40.start_periodic_measurement()
            
            # Initialize display
            import adafruit_ssd1306
            
            # Get display configurations
            display_width = 128
            display_height = 64
            display_sda_pin = self.config.get('pins', 'Display_SDA_PIN') 
            display_scl_pin = self.config.get('pins', 'Display_SCL_PIN')
            
            # Create I2C interface for display
            display_i2c = busio.I2C(getattr(board, f"D{display_scl_pin}"), 
                                    getattr(board, f"D{display_sda_pin}"))
            
            # Create the SSD1306 OLED display
            self.display = adafruit_ssd1306.SSD1306_I2C(display_width, display_height, display_i2c)
            self.display.fill(0)
            self.display.show()
            
            return True
            
        except Exception as e:
            self.app.system_manager.logger.error(f"Error initializing sensors: {str(e)}")
            return False
    
    def start(self):
        """Start sensor reading threads"""
        if not self.running:
            self.running = True
            
            # Start DHT reading thread
            self.dht_thread = threading.Thread(target=self._dht_reading_loop)
            self.dht_thread.daemon = True
            self.dht_thread.start()
            
            # Start SCD40 reading thread
            self.scd_thread = threading.Thread(target=self._scd_reading_loop)
            self.scd_thread.daemon = True
            self.scd_thread.start()
            
            # Start display update thread
            self.display_thread = threading.Thread(target=self._display_update_loop)
            self.display_thread.daemon = True
            self.display_thread.start()
            
            self.app.system_manager.logger.info("Sensor manager started")
    
    def stop(self):
        """Stop sensor reading"""
        self.running = False
        
        # Wait for threads to terminate
        if self.dht_thread and self.dht_thread.is_alive():
            self.dht_thread.join(timeout=2)
        
        if self.scd_thread and self.scd_thread.is_alive():
            self.scd_thread.join(timeout=2)
            
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)
            
        self.app.system_manager.logger.info("Sensor manager stopped")
    
    def _dht_reading_loop(self):
        """Thread function for reading DHT sensors"""
        # 5 second warm-up
        time.sleep(5)
        
        while self.running:
            try:
                # Get reading interval from config
                interval = self.config.get('sensors', 'dht_interval', 30)  # Default 30 seconds
                
                # Read upper DHT
                upper_temp = self.dht22_upper.temperature
                upper_humidity = self.dht22_upper.humidity
                
                if upper_temp is not None and upper_humidity is not None:
                    self.readings['upper_dht']['temperature'] = upper_temp
                    self.readings['upper_dht']['humidity'] = upper_humidity
                    self.readings['upper_dht']['last_read'] = time.time()
                    self.readings['upper_dht']['errors'] = 0
                    
                    self.app.system_manager.logger.debug(
                        f"Upper DHT: Temp={upper_temp}°C, Humidity={upper_humidity}%")
                
                # Read lower DHT
                lower_temp = self.dht22_lower.temperature
                lower_humidity = self.dht22_lower.humidity
                
                if lower_temp is not None and lower_humidity is not None:
                    self.readings['lower_dht']['temperature'] = lower_temp
                    self.readings['lower_dht']['humidity'] = lower_humidity
                    self.readings['lower_dht']['last_read'] = time.time()
                    self.readings['lower_dht']['errors'] = 0
                    
                    self.app.system_manager.logger.debug(
                        f"Lower DHT: Temp={lower_temp}°C, Humidity={lower_humidity}%")
                
                # Publish readings to MQTT if configured
                if self.app.network_manager.mqtt_connected:
                    self.app.network_manager.publish_sensor_data()
                
                # Update component automation based on readings
                self.component_manager.relay_manager.update_automations()
                
            except Exception as e:
                self.app.system_manager.logger.error(f"Error reading DHT sensors: {str(e)}")
                self.readings['upper_dht']['errors'] += 1
                self.readings['lower_dht']['errors'] += 1
                
                # Attempt recovery if error threshold exceeded
                error_threshold = self.config.get('sensors', 'error_threshold', 5)
                if (self.readings['upper_dht']['errors'] > error_threshold or
                    self.readings['lower_dht']['errors'] > error_threshold):
                    self.app.system_manager.logger.warning("Attempting DHT sensor recovery...")
                    # Re-initialize the sensors
                    self._recover_dht_sensors()
            
            # Sleep until next reading
            time.sleep(interval)
    
    def _scd_reading_loop(self):
        """Thread function for reading SCD40 sensor"""
        # Implementation similar to DHT reading loop
        
    def _display_update_loop(self):
        """Thread function for updating the display"""
        # Implementation for updating the OLED display with latest readings
        
    def _recover_dht_sensors(self):
        """Attempt to recover DHT sensors after errors"""
        # Implementation for sensor recovery
        
    def get_all_readings(self):
        """Get all current sensor readings"""
        return self.readings
    
    def get_average_temperature(self):
        """Calculate average temperature from all sensors"""
        temps = [
            self.readings['upper_dht']['temperature'],
            self.readings['lower_dht']['temperature'],
            self.readings['scd40']['temperature']
        ]
        valid_temps = [t for t in temps if t != 0]
        return sum(valid_temps) / len(valid_temps) if valid_temps else 0
    
    def get_average_humidity(self):
        """Calculate average humidity from all sensors"""
        humidities = [
            self.readings['upper_dht']['humidity'],
            self.readings['lower_dht']['humidity'],
            self.readings['scd40']['humidity']
        ]
        valid_humidities = [h for h in humidities if h != 0]
        return sum(valid_humidities) / len(valid_humidities) if valid_humidities else 0