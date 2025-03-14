class RelayManager:
    def __init__(self, component_manager):
        self.component_manager = component_manager
        self.app = component_manager.app
        self.config = self.app.config
        
        # Relay pins from config
        self.relay_pins = {
            'relay1': self.config.get('pins', 'Relay1_PIN', 18),  # Main PSU
            'relay2': self.config.get('pins', 'Relay2_PIN', 24),  # UV Light
            'relay3': self.config.get('pins', 'Relay3_PIN', 25),  # Grow Light
            'relay4': self.config.get('pins', 'Relay4_PIN', 6),   # Tub Fans
            'relay5': self.config.get('pins', 'Relay5_PIN', 26),  # Humidifiers
            'relay6': self.config.get('pins', 'Relay6_PIN', 19),  # Heater
            'relay7': self.config.get('pins', 'Relay7_PIN', 13),  # IN/OUT Fans
            'relay8': self.config.get('pins', 'Relay8_PIN', 16)   # Reserved
        }
        
        # Relay states and configurations
        self.relay_states = {
            'relay1': {
                'name': 'Main PSU',
                'state': False,
                'auto_control': True,
                'visible': False,
                'pin': self.relay_pins['relay1'],
                'dependencies': [],
                'override': False,
                'override_until': 0,
                'schedule': {'start': '00:00', 'end': '23:59'}
            },
            'relay2': {
                'name': 'UV Light',
                'state': False,
                'auto_control': True,
                'visible': True,
                'pin': self.relay_pins['relay2'],
                'dependencies': ['relay1'],
                'override': False,
                'override_until': 0,
                'schedule': {'start': '00:00', 'end': '23:59'},
                'cycle': {'duration': 30, 'interval': 60}
            },
            # Additional relay configurations similar to above
        }
        
        self.running = False
        self.automation_thread = None
        self.tapo_integration = None
        
    def initialize(self):
        """Initialize all relays"""
        try:
            import RPi.GPIO as GPIO
            
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup all relay pins as outputs
            for relay_id, relay_data in self.relay_states.items():
                pin = relay_data['pin']
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)  # Relays are active LOW
                self.app.system_manager.logger.debug(f"Initialized {relay_data['name']} on pin {pin}")
            
            # Initialize Tapo integration if configured
            tapo_enabled = self.config.get('tapo', 'enabled', False)
            if tapo_enabled:
                self.tapo_integration = TapoIntegration(self)
                self.tapo_integration.initialize()
            
            return True
            
        except Exception as e:
            self.app.system_manager.logger.error(f"Error initializing relays: {str(e)}")
            return False
    
    def start(self):
        """Start relay automation thread"""
        if not self.running:
            self.running = True
            
            # Start automation thread
            self.automation_thread = threading.Thread(target=self._automation_loop)
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
            self.app.system_manager.logger.info("Relay manager started")
    
    def stop(self):
        """Stop relay automation"""
        self.running = False
        
        # Wait for thread to terminate
        if self.automation_thread and self.automation_thread.is_alive():
            self.automation_thread.join(timeout=2)
            
        # Turn off all relays
        self._all_relays_off()
        
        self.app.system_manager.logger.info("Relay manager stopped")
    
    def set_relay(self, relay_id, state, override=False, duration=300):
        """Set relay state with optional override"""
        if relay_id not in self.relay_states:
            return False
        
        try:
            import RPi.GPIO as GPIO
            
            relay = self.relay_states[relay_id]
            
            # Check dependencies
            if state and not self._check_dependencies(relay_id):
                self.app.system_manager.logger.warning(
                    f"Cannot turn on {relay['name']}: dependencies not met")
                return False
            
            # Set override if requested
            if override:
                relay['override'] = True
                relay['override_until'] = time.time() + duration
                self.app.system_manager.logger.info(
                    f"Override set for {relay['name']} for {duration} seconds")
            
            # Update relay state
            relay['state'] = state
            
            # Set GPIO output
            GPIO.output(relay['pin'], not state)  # Relay is active LOW
            
            # If this is relay1 and turning off, check dependents
            if relay_id == 'relay1' and not state:
                self._handle_dependency_chain('relay1')
            
            # Update special cases for Tapo integration
            if self.tapo_integration and relay_id in ['relay1', 'relay6']:
                self.tapo_integration.update_device(relay_id, state)
            
            self.app.system_manager.logger.info(
                f"Relay {relay['name']} set to {'ON' if state else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.app.system_manager.logger.error(f"Error setting relay {relay_id}: {str(e)}")
            return False
    
    def _check_dependencies(self, relay_id):
        """Check if all dependencies for a relay are met"""
        relay = self.relay_states[relay_id]
        
        for dep_id in relay['dependencies']:
            if not self.relay_states[dep_id]['state']:
                return False
                
        return True
    
    def _handle_dependency_chain(self, relay_id):
        """Handle turning off dependent relays when a dependency is turned off"""
        # Find all relays that depend on this one
        for dep_relay_id, dep_relay in self.relay_states.items():
            if relay_id in dep_relay['dependencies'] and dep_relay['state']:
                # Turn off dependent relay
                self.set_relay(dep_relay_id, False)
    
    def _all_relays_off(self):
        """Turn off all relays"""
        for relay_id in self.relay_states:
            self.set_relay(relay_id, False, override=True)
    
    def _automation_loop(self):
        """Thread function for relay automation"""
        while self.running:
            try:
                # Update automation every 10 seconds
                self.update_automations()
                time.sleep(10)
                
            except Exception as e:
                self.app.system_manager.logger.error(f"Error in relay automation: {str(e)}")
                time.sleep(30)  # Longer delay after error
    
    def update_automations(self):
        """Update all relay automations based on current time and sensor readings"""
        current_time = datetime.now().time()
        sensor_manager = self.component_manager.sensor_manager
        
        # Check and clear expired overrides
        current_timestamp = time.time()
        for relay_id, relay in self.relay_states.items():
            if relay['override'] and current_timestamp > relay['override_until']:
                relay['override'] = False
                self.app.system_manager.logger.info(f"Override expired for {relay['name']}")
        
        # Handle each relay's automation logic
        self._handle_main_psu_automation(current_time)
        self._handle_light_automation(current_time)
        self._handle_fan_automation(current_time, sensor_manager)
        self._handle_humidifier_automation(current_time, sensor_manager)
        self._handle_heater_automation(sensor_manager)
        self._handle_inout_fan_automation(current_time, sensor_manager)
    
    def _handle_main_psu_automation(self, current_time):
        """Handle automation for the main PSU (Relay 1)"""
        # Implementation for Relay 1 automation
        
    def _handle_light_automation(self, current_time):
        """Handle automation for lights (Relays 2 & 3)"""
        # Implementation for Relays 2 & 3 automation
        
    def _handle_fan_automation(self, current_time, sensor_manager):
        """Handle automation for tub fans (Relay 4)"""
        # Implementation for Relay 4 automation
        
    def _handle_humidifier_automation(self, current_time, sensor_manager):
        """Handle automation for humidifiers (Relay 5)"""
        # Implementation for Relay 5 automation
        
    def _handle_heater_automation(self, sensor_manager):
        """Handle automation for heater (Relay 6)"""
        # Implementation for Relay 6 automation
        
    def _handle_inout_fan_automation(self, current_time, sensor_manager):
        """Handle automation for IN/OUT fans (Relay 7)"""
        # Implementation for Relay 7 automation