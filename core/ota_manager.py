#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTA Manager Module

This module handles over-the-air updates for the application.
"""

import os
import io
import json
import time
import logging
import threading
import zipfile
import shutil
import hashlib
import requests

class OTAManager:
    """OTA Manager class for handling over-the-air updates"""
    
    def __init__(self, app):
        """Initialize the OTA Manager
        
        Args:
            app: Main application instance
        """
        self.app = app
        self.logger = logging.getLogger('OTAManager')
        
        # Current version info
        self.current_version = {
            'system': self.app.system_manager.get_config('system', 'version', '1.0.0'),
            'firmware': '1.0.0'
        }
        
        # Update status
        self.update_status = {
            'in_progress': False,
            'progress': 0,
            'message': '',
            'error': '',
            'success': False,
            'last_check': 0
        }
        
        # Update thread
        self.update_thread = None
        
        # Running state
        self.running = False
    
    def start(self):
        """Start the OTA Manager"""
        if self.running:
            return
        
        self.running = True
        
        # Schedule version check
        self._schedule_version_check()
        
        self.logger.info("OTA Manager started")
    
    def stop(self):
        """Stop the OTA Manager"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for thread to terminate
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        
        self.logger.info("OTA Manager stopped")
    
    def _schedule_version_check(self):
        """Schedule periodic version check"""
        if not self.running:
            return
        
        try:
            # Check for updates
            self._check_for_updates()
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {str(e)}")
        
        # Schedule next check in 24 hours
        timer = threading.Timer(86400, self._schedule_version_check)
        timer.daemon = True
        timer.start()
    
    def _check_for_updates(self):
        """Check for available updates
        
        Returns:
            bool: True if updates available, False otherwise
        """
        try:
            # Update last check timestamp
            self.update_status['last_check'] = int(time.time())
            
            # TODO: Implement update check logic
            # This would involve fetching version info from a remote server
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {str(e)}")
            return False
    
    def get_update_status(self):
        """Get current update status
        
        Returns:
            dict: Update status
        """
        return {
            **self.update_status,
            'current_version': self.current_version
        }
    
    def install_update(self, file_path, restart=True):
        """Install update from file
        
        Args:
            file_path (str): Path to update file
            restart (bool, optional): Whether to restart after update. Defaults to True.
            
        Returns:
            bool: True if update started, False otherwise
        """
        try:
            # Check if update already in progress
            if self.update_status['in_progress']:
                self.logger.warning("Update already in progress")
                return False
            
            # Start update in a separate thread
            self.update_thread = threading.Thread(
                target=self._update_process, args=(file_path, restart))
            self.update_thread.daemon = True
            self.update_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting update: {str(e)}")
            
            self.update_status['in_progress'] = False
            self.update_status['error'] = str(e)
            self.update_status['success'] = False
            
            return False
    
    def _update_process(self, file_path, restart):
        """Process update file
        
        Args:
            file_path (str): Path to update file
            restart (bool): Whether to restart after update
        """
        try:
            self.update_status['in_progress'] = True
            self.update_status['progress'] = 0
            self.update_status['message'] = "Starting update process"
            self.update_status['error'] = ""
            self.update_status['success'] = False
            
            self.logger.info(f"Starting update from {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise Exception(f"Update file not found: {file_path}")
            
            # Check file type (must be ZIP)
            if not file_path.endswith('.zip'):
                raise Exception("Update file must be a ZIP archive")
            
            # Extract update package
            self.update_status['progress'] = 10
            self.update_status['message'] = "Extracting update package"
            
            update_dir = '/tmp/mushroom_update'
            
            # Clean up existing directory if it exists
            if os.path.exists(update_dir):
                shutil.rmtree(update_dir)
            
            # Create update directory
            os.makedirs(update_dir, exist_ok=True)
            
            # Extract ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(update_dir)
            
            # Check for update manifest
            manifest_path = os.path.join(update_dir, 'manifest.json')
            if not os.path.exists(manifest_path):
                raise Exception("Update package does not contain manifest.json")
            
            # Read manifest
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check manifest format
            if 'version' not in manifest:
                raise Exception("Invalid manifest format: missing version")
            
            if 'files' not in manifest:
                raise Exception("Invalid manifest format: missing files list")
            
            # Check version
            new_version = manifest['version']
            self.logger.info(f"Update version: {new_version}")
            
            # Create backup
            self.update_status['progress'] = 20
            self.update_status['message'] = "Creating backup"
            
            backup_dir = '/tmp/mushroom_backup'
            
            # Clean up existing backup if it exists
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy current files to backup
            for file_info in manifest['files']:
                src_path = file_info['path']
                if os.path.exists(src_path):
                    # Create target directory structure
                    os.makedirs(os.path.dirname(os.path.join(backup_dir, src_path)), exist_ok=True)
                    
                    # Copy file to backup
                    shutil.copy2(src_path, os.path.join(backup_dir, src_path))
            
            # Install update files
            self.update_status['progress'] = 40
            self.update_status['message'] = "Installing update files"
            
            file_count = len(manifest['files'])
            for i, file_info in enumerate(manifest['files']):
                src_path = os.path.join(update_dir, file_info['path'])
                dst_path = file_info['path']
                
                # Check if source file exists
                if not os.path.exists(src_path):
                    raise Exception(f"Update file not found: {file_info['path']}")
                
                # Create target directory if it doesn't exist
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_path, dst_path)
                
                # Verify checksum if provided
                if 'checksum' in file_info:
                    with open(dst_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash != file_info['checksum']:
                        raise Exception(f"Checksum mismatch for {file_info['path']}")
                
                # Update progress
                self.update_status['progress'] = 40 + int((i + 1) / file_count * 50)
                self.update_status['message'] = f"Installing file {i + 1} of {file_count}"
            
            # Update version in config
            self.app.system_manager.set_config('system', 'version', new_version)
            self.current_version['system'] = new_version
            
            # Clean up
            self.update_status['progress'] = 95
            self.update_status['message'] = "Cleaning up"
            
            # Delete update directory
            shutil.rmtree(update_dir)
            
            # Delete update file
            os.remove(file_path)
            
            # Update complete
            self.update_status['progress'] = 100
            self.update_status['message'] = "Update completed successfully"
            self.update_status['success'] = True
            
            self.logger.info(f"Update to version {new_version} completed successfully")
            
            # Restart if requested
            if restart:
                self.logger.info("Restarting system...")
                time.sleep(2)
                self.app.system_manager.reboot_system()
            
        except Exception as e:
            self.logger.error(f"Error during update: {str(e)}")
            
            self.update_status['error'] = str(e)
            self.update_status['message'] = "Update failed"
            self.update_status['success'] = False
            
            # Try to restore from backup if available
            try:
                backup_dir = '/tmp/mushroom_backup'
                if os.path.exists(backup_dir):
                    self.logger.info("Restoring from backup...")
                    
                    # Copy backup files back
                    for root, _, files in os.walk(backup_dir):
                        for file in files:
                            backup_path = os.path.join(root, file)
                            rel_path = os.path.relpath(backup_path, backup_dir)
                            orig_path = os.path.join('/', rel_path)
                            
                            # Create target directory if it doesn't exist
                            os.makedirs(os.path.dirname(orig_path), exist_ok=True)
                            
                            # Copy file back
                            shutil.copy2(backup_path, orig_path)
                    
                    self.logger.info("Backup restored successfully")
            except Exception as restore_error:
                self.logger.error(f"Error restoring backup: {str(restore_error)}")
        
        finally:
            # Update in-progress flag
            self.update_status['in_progress'] = False