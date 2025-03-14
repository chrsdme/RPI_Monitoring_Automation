#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web API Manager Module

This module handles the web server and API endpoints for the application.
"""

import os
import json
import logging
import threading
from flask import Flask, request, jsonify, send_from_directory, render_template

class WebApiManager:
    """Web API Manager class for managing the web server and API endpoints"""
    
    def __init__(self, app):
        """Initialize the Web API Manager
        
        Args:
            app: Main application instance
        """
        self.app = app
        self.logger = logging.getLogger('WebApiManager')
        
        # Flask application
        self.flask_app = Flask(__name__,
                              static_folder='../web/static',
                              template_folder='../web/templates')
        
        # Web server thread
        self.web_server_thread = None
        
        # Running state
        self.running = False
        
        # Set up API endpoints
        self._setup_endpoints()
    
    def _setup_endpoints(self):
        """Set up API endpoints"""
        # Static files and frontend
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self.flask_app.route('/<path:path>')
        def serve_static(path):
            if path.endswith('.html'):
                return render_template(path)
            return send_from_directory('../web/static', path)
        
        # API endpoints
        @self.flask_app.route('/api/sensors', methods=['GET'])
        def get_sensors():
            try:
                # Get sensor data
                sensor_data = self.app.component_manager.sensor_manager.get_all_readings()
                return jsonify(sensor_data)
            except Exception as e:
                self.logger.error(f"Error in /api/sensors: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/relays', methods=['GET'])
        def get_relays():
            try:
                # Get relay states
                relay_states = self.app.component_manager.relay_manager.get_relay_states()
                return jsonify(relay_states)
            except Exception as e:
                self.logger.error(f"Error in /api/relays: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/relays/<relay_id>', methods=['GET'])
        def get_relay(relay_id):
            try:
                # Get specific relay state
                relay_states = self.app.component_manager.relay_manager.get_relay_states()
                
                if relay_id not in relay_states:
                    return jsonify({'error': f"Relay '{relay_id}' not found"}), 404
                
                return jsonify(relay_states[relay_id])
            except Exception as e:
                self.logger.error(f"Error in /api/relays/{relay_id}: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/relays/<relay_id>', methods=['POST'])
        def set_relay(relay_id):
            try:
                # Parse request data
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': "Invalid request data"}), 400
                
                state = data.get('state')
                override = data.get('override', False)
                
                if state is None:
                    return jsonify({'error': "Missing 'state' parameter"}), 400
                
                # Set relay state
                result = self.app.component_manager.relay_manager.set_relay(
                    relay_id, state, override=override)
                
                if not result:
                    return jsonify({'error': f"Failed to set relay '{relay_id}'"}), 500
                
                # Get updated relay state
                relay_states = self.app.component_manager.relay_manager.get_relay_states()
                
                if relay_id not in relay_states:
                    return jsonify({'error': f"Relay '{relay_id}' not found"}), 404
                
                return jsonify({
                    'success': True,
                    'relay': relay_id,
                    'state': relay_states[relay_id]['state'],
                    'auto_control': relay_states[relay_id]['auto_control'],
                    'override_until': relay_states[relay_id]['override_until']
                })
            except Exception as e:
                self.logger.error(f"Error in /api/relays/{relay_id} POST: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/settings', methods=['GET'])
        def get_settings():
            try:
                # Get system settings
                system_settings = self.app.system_manager.get_config('system')
                
                # Get active profile
                active_profile = self.app.system_manager.get_active_profile()
                
                # Combine settings
                settings = {**system_settings, **active_profile}
                
                return jsonify(settings)
            except Exception as e:
                self.logger.error(f"Error in /api/settings: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/settings', methods=['POST'])
        def update_settings():
            try:
                # Parse request data
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': "Invalid request data"}), 400
                
                # Update system settings
                for key, value in data.items():
                    if key in ['name', 'version', 'log_level', 'log_max_size', 
                              'log_flush_interval', 'sensor_error_threshold',
                              'reboot_day', 'reboot_time', 'sleep_mode',
                              'sleep_start_time', 'sleep_end_time']:
                        self.app.system_manager.set_config('system', key, value)
                
                # Get active profile
                profile_name = self.app.system_manager.get_config('active_profile')
                profile_data = self.app.system_manager.get_profile(profile_name)
                
                # Update profile settings
                profile_updated = False
                for key, value in data.items():
                    if key in ['graph_update_interval', 'graph_max_points',
                              'dht_sensor_interval', 'scd40_sensor_interval',
                              'humidity_low_threshold', 'humidity_high_threshold',
                              'temperature_low_threshold', 'temperature_high_threshold',
                              'co2_low_threshold', 'co2_high_threshold',
                              'fan_cycle', 'fan_schedule', 'light_cycle', 'light_schedule']:
                        profile_data[key] = value
                        profile_updated = True
                
                # Save updated profile
                if profile_updated:
                    self.app.system_manager.save_profile(profile_name, profile_data)
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/settings POST: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/profiles', methods=['GET'])
        def get_profiles():
            try:
                # Get list of profiles
                profiles = self.app.system_manager.get_profiles()
                
                # Get active profile
                active_profile = self.app.system_manager.get_config('active_profile')
                
                return jsonify({
                    'profiles': profiles,
                    'active': active_profile
                })
            except Exception as e:
                self.logger.error(f"Error in /api/profiles: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/profiles/<profile_name>', methods=['GET'])
        def get_profile(profile_name):
            try:
                # Get profile
                profile = self.app.system_manager.get_profile(profile_name)
                
                if not profile:
                    return jsonify({'error': f"Profile '{profile_name}' not found"}), 404
                
                return jsonify(profile)
            except Exception as e:
                self.logger.error(f"Error in /api/profiles/{profile_name}: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/profiles/<profile_name>', methods=['POST'])
        def update_profile(profile_name):
            try:
                # Parse request data
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': "Invalid request data"}), 400
                
                # Save profile
                result = self.app.system_manager.save_profile(profile_name, data)
                
                if not result:
                    return jsonify({'error': f"Failed to save profile '{profile_name}'"}), 500
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/profiles/{profile_name} POST: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/profiles/export', methods=['GET'])
        def export_profiles():
            try:
                # Export profiles
                profiles_json = self.app.system_manager.export_profiles()
                
                if not profiles_json:
                    return jsonify({'error': "Failed to export profiles"}), 500
                
                # Create response
                response = self.flask_app.response_class(
                    response=profiles_json,
                    status=200,
                    mimetype='application/json'
                )
                
                # Set content disposition header
                response.headers["Content-Disposition"] = "attachment; filename=profiles.json"
                
                return response
            except Exception as e:
                self.logger.error(f"Error in /api/profiles/export: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/profiles/import', methods=['POST'])
        def import_profiles():
            try:
                # Check if file was uploaded
                if 'file' not in request.files:
                    return jsonify({'error': "No file uploaded"}), 400
                
                file = request.files['file']
                
                if file.filename == '':
                    return jsonify({'error': "No file selected"}), 400
                
                if not file.filename.endswith('.json'):
                    return jsonify({'error': "Invalid file format, must be JSON"}), 400
                
                # Read file content
                profiles_json = file.read().decode('utf-8')
                
                # Import profiles
                result = self.app.system_manager.import_profiles(profiles_json)
                
                if not result:
                    return jsonify({'error': "Failed to import profiles"}), 500
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/profiles/import: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/system/status', methods=['GET'])
        def get_system_status():
            try:
                # Get system info
                system_info = self.app.system_manager.get_system_info()
                
                return jsonify(system_info)
            except Exception as e:
                self.logger.error(f"Error in /api/system/status: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/system/reboot', methods=['POST'])
        def reboot_system():
            try:
                # Reboot system
                result = self.app.system_manager.reboot_system()
                
                if not result:
                    return jsonify({'error': "Failed to reboot system"}), 500
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/system/reboot: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/system/reset', methods=['POST'])
        def reset_system():
            try:
                # Factory reset
                result = self.app.system_manager.factory_reset()
                
                if not result:
                    return jsonify({'error': "Failed to reset system"}), 500
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/system/reset: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/logs', methods=['GET'])
        def get_logs():
            try:
                # Get parameters
                limit = request.args.get('limit', 100, type=int)
                level = request.args.get('level')
                component = request.args.get('component')
                
                # Get logs
                logs = self.app.system_manager.get_logs(limit, level, component)
                
                return jsonify(logs)
            except Exception as e:
                self.logger.error(f"Error in /api/logs: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/network/status', methods=['GET'])
        def get_network_status():
            try:
                # Get WiFi info
                wifi_info = self.app.network_manager.get_wifi_info()
                
                # Get MQTT status
                mqtt_status = {
                    'enabled': self.app.system_manager.get_config('network', 'mqtt', 'enabled', False),
                    'connected': self.app.network_manager.mqtt_connected
                }
                
                return jsonify({
                    'wifi': wifi_info,
                    'mqtt': mqtt_status
                })
            except Exception as e:
                self.logger.error(f"Error in /api/network/status: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/network/scan', methods=['GET'])
        def scan_networks():
            try:
                # Scan WiFi networks
                networks = self.app.network_manager.scan_wifi_networks()
                
                return jsonify(networks)
            except Exception as e:
                self.logger.error(f"Error in /api/network/scan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/network/config', methods=['POST'])
        def update_network_config():
            try:
                # Parse request data
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': "Invalid request data"}), 400
                
                # Process WiFi credentials
                if 'wifi' in data:
                    wifi_credentials = []
                    
                    for i in range(1, 4):
                        ssid_key = f'wifi{i}_ssid'
                        pass_key = f'wifi{i}_password'
                        
                        if ssid_key in data['wifi'] and pass_key in data['wifi']:
                            wifi_credentials.append((data['wifi'][ssid_key], data['wifi'][pass_key]))
                    
                    # Save WiFi credentials
                    self.app.network_manager._save_wifi_credentials(wifi_credentials)
                
                # Process static IP configuration
                if 'static_ip' in data:
                    self.app.system_manager.set_config('network', 'static_ip', data['static_ip'])
                
                # Process hostname
                if 'hostname' in data:
                    self.app.system_manager.set_config('network', 'hostname', data['hostname'])
                
                # Process WiFi watchdog settings
                if 'wifi_min_rssi' in data:
                    self.app.system_manager.set_config('network', 'wifi_min_rssi', data['wifi_min_rssi'])
                
                if 'wifi_check_interval' in data:
                    self.app.system_manager.set_config('network', 'wifi_check_interval', data['wifi_check_interval'])
                
                # Process MQTT configuration
                if 'mqtt' in data:
                    # Update MQTT config
                    self.app.system_manager.set_config('network', 'mqtt', data['mqtt'])
                    
                    # Restart MQTT if needed
                    if data['mqtt'].get('enabled', False):
                        if not self.app.network_manager.mqtt_connected:
                            self.app.network_manager._start_mqtt()
                    else:
                        if self.app.network_manager.mqtt_connected:
                            self.app.network_manager._stop_mqtt()
                
                # Apply changes
                if 'apply' in data and data['apply']:
                    # Restart network services
                    self.app.network_manager._stop_mdns()
                    
                    # Reconnect to WiFi if needed
                    if 'reconnect' in data and data['reconnect']:
                        self.app.network_manager._connect_wifi()
                    
                    # Restart mDNS
                    self.app.network_manager._start_mdns()
                
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error in /api/network/config: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """Start the Web API Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start web server in a separate thread
        self.web_server_thread = threading.Thread(target=self._web_server_loop)
        self.web_server_thread.daemon = True
        self.web_server_thread.start()
        
        self.logger.info("Web API Manager started")
    
    def stop(self):
        """Stop the Web API Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop web server
        # Note: Flask development server doesn't have a clean shutdown method
        # For production, use a proper WSGI server like Gunicorn
        
        # Wait for thread to terminate
        if self.web_server_thread and self.web_server_thread.is_alive():
            self.web_server_thread.join(timeout=2)
        
        self.logger.info("Web API Manager stopped")
    
    def _web_server_loop(self):
        """Web server thread loop"""
        try:
            # Get server IP address
            ip_addr = "0.0.0.0"  # Bind to all interfaces
            
            # Run Flask application
            self.flask_app.run(host=ip_addr, port=80, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Error in web server: {str(e)}")