/**
 * settings.js
 * Handles application settings for the Mushroom Tent Controller
 */

// Global variables
let settings = {
    log: {
        level: 'DEBUG',
        maxFileSize: 5, // MB
        remoteAddress: '',
        flushInterval: 60 // seconds
    },
    sensor: {
        errorCount: 3
    },
    reboot: {
        dayOfWeek: 0, // Sunday
        time: '03:00'
    },
    sleep: {
        mode: 'No Sleep',
        startTime: '00:00',
        endTime: '00:00'
    },
    notifications: {
        enabled: false,
        type: 'telegram',
        params: {
            token: '',
            chatId: ''
        }
    }
};

/**
 * Initialize settings
 */
function initSettings() {
    console.log("Initializing settings...");
    
    // Fetch settings from server
    fetchSettings();
    
    // Set up UI elements
    setupSettingsUI();
}

/**
 * Fetch settings from server
 */
function fetchSettings() {
    fetch('/api/settings')
        .then(response => response.json())
        .then(data => {
            console.log("Settings loaded:", data);
            
            // Update settings
            settings = data;
            
            // Update UI
            updateSettingsUI();
        })
        .catch(error => {
            console.error("Error loading settings:", error);
        });
}

/**
 * Set up settings UI elements
 */
function setupSettingsUI() {
    // Log level dropdown
    const logLevelSelect = document.getElementById('log-level');
    if (logLevelSelect) {
        logLevelSelect.addEventListener('change', function() {
            settings.log.level = this.value;
        });
    }
    
    // Log max file size
    const logFileSizeInput = document.getElementById('log-file-size');
    if (logFileSizeInput) {
        logFileSizeInput.addEventListener('change', function() {
            settings.log.maxFileSize = parseFloat(this.value);
        });
    }
    
    // Log remote address
    const logRemoteAddressInput = document.getElementById('log-remote-address');
    if (logRemoteAddressInput) {
        logRemoteAddressInput.addEventListener('change', function() {
            settings.log.remoteAddress = this.value;
        });
    }
    
    // Log flush interval
    const logFlushIntervalInput = document.getElementById('log-flush-interval');
    if (logFlushIntervalInput) {
        logFlushIntervalInput.addEventListener('change', function() {
            settings.log.flushInterval = parseInt(this.value);
        });
    }
    
    // Sensor error count
    const sensorErrorCountInput = document.getElementById('sensor-error-count');
    if (sensorErrorCountInput) {
        sensorErrorCountInput.addEventListener('change', function() {
            settings.sensor.errorCount = parseInt(this.value);
        });
    }
    
    // Reboot day of week
    const rebootDaySelect = document.getElementById('reboot-day');
    if (rebootDaySelect) {
        rebootDaySelect.addEventListener('change', function() {
            settings.reboot.dayOfWeek = parseInt(this.value);
        });
    }
    
    // Reboot time
    const rebootTimeInput = document.getElementById('reboot-time');
    if (rebootTimeInput) {
        rebootTimeInput.addEventListener('change', function() {
            settings.reboot.time = this.value;
        });
    }
    
    // Sleep mode
    const sleepModeSelect = document.getElementById('sleep-mode');
    if (sleepModeSelect) {
        sleepModeSelect.addEventListener('change', function() {
            settings.sleep.mode = this.value;
            
            // Show/hide time fields based on selection
            const sleepTimeFields = document.getElementById('sleep-time-fields');
            if (sleepTimeFields) {
                sleepTimeFields.style.display = this.value === 'No Sleep' ? 'none' : 'block';
            }
        });
    }
    
    // Sleep start time
    const sleepStartTimeInput = document.getElementById('sleep-start-time');
    if (sleepStartTimeInput) {
        sleepStartTimeInput.addEventListener('change', function() {
            settings.sleep.startTime = this.value;
        });
    }
    
    // Sleep end time
    const sleepEndTimeInput = document.getElementById('sleep-end-time');
    if (sleepEndTimeInput) {
        sleepEndTimeInput.addEventListener('change', function() {
            settings.sleep.endTime = this.value;
        });
    }
    
    // Notifications enabled
    const notificationsEnabledInput = document.getElementById('notifications-enabled');
    if (notificationsEnabledInput) {
        notificationsEnabledInput.addEventListener('change', function() {
            settings.notifications.enabled = this.checked;
            
            // Show/hide notification settings based on checkbox
            const notificationSettings = document.getElementById('notification-settings');
            if (notificationSettings) {
                notificationSettings.style.display = this.checked ? 'block' : 'none';
            }
        });
    }
    
    // Notification type
    const notificationTypeSelect = document.getElementById('notification-type');
    if (notificationTypeSelect) {
        notificationTypeSelect.addEventListener('change', function() {
            settings.notifications.type = this.value;
            
            // Update parameter fields based on type
            updateNotificationFields();
        });
    }
    
    // Save button
    const saveButton = document.getElementById('settings-save-btn');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            saveSettings();
        });
    }
    
    // Reboot now button
    const rebootNowButton = document.getElementById('reboot-now-btn');
    if (rebootNowButton) {
        rebootNowButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to reboot the system now?')) {
                rebootSystem();
            }
        });
    }
    
    // Factory reset button
    const factoryResetButton = document.getElementById('factory-reset-btn');
    if (factoryResetButton) {
        factoryResetButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to reset to factory settings? This will erase all your configurations.')) {
                factoryReset();
            }
        });
    }
    
    // Test sensors button
    const testSensorsButton = document.getElementById('test-sensors-btn');
    if (testSensorsButton) {
        testSensorsButton.addEventListener('click', function() {
            testSensors();
        });
    }
    
    // Test relays button
    const testRelaysButton = document.getElementById('test-relays-btn');
    if (testRelaysButton) {
        testRelaysButton.addEventListener('click', function() {
            testRelays();
        });
    }
}

/**
 * Update settings UI with current values
 */
function updateSettingsUI() {
    // Log level
    const logLevelSelect = document.getElementById('log-level');
    if (logLevelSelect && settings.log.level) {
        logLevelSelect.value = settings.log.level;
    }
    
    // Log max file size
    const logFileSizeInput = document.getElementById('log-file-size');
    if (logFileSizeInput) {
        logFileSizeInput.value = settings.log.maxFileSize;
    }
    
    // Log remote address
    const logRemoteAddressInput = document.getElementById('log-remote-address');
    if (logRemoteAddressInput) {
        logRemoteAddressInput.value = settings.log.remoteAddress;
    }
    
    // Log flush interval
    const logFlushIntervalInput = document.getElementById('log-flush-interval');
    if (logFlushIntervalInput) {
        logFlushIntervalInput.value = settings.log.flushInterval;
    }
    
    // Sensor error count
    const sensorErrorCountInput = document.getElementById('sensor-error-count');
    if (sensorErrorCountInput) {
        sensorErrorCountInput.value = settings.sensor.errorCount;
    }
    
    // Reboot day of week
    const rebootDaySelect = document.getElementById('reboot-day');
    if (rebootDaySelect) {
        rebootDaySelect.value = settings.reboot.dayOfWeek;
    }
    
    // Reboot time
    const rebootTimeInput = document.getElementById('reboot-time');
    if (rebootTimeInput) {
        rebootTimeInput.value = settings.reboot.time;
    }
    
    // Sleep mode
    const sleepModeSelect = document.getElementById('sleep-mode');
    if (sleepModeSelect) {
        sleepModeSelect.value = settings.sleep.mode;
        
        // Show/hide time fields based on selection
        const sleepTimeFields = document.getElementById('sleep-time-fields');
        if (sleepTimeFields) {
            sleepTimeFields.style.display = settings.sleep.mode === 'No Sleep' ? 'none' : 'block';
        }
    }
    
    // Sleep start time
    const sleepStartTimeInput = document.getElementById('sleep-start-time');
    if (sleepStartTimeInput) {
        sleepStartTimeInput.value = settings.sleep.startTime;
    }
    
    // Sleep end time
    const sleepEndTimeInput = document.getElementById('sleep-end-time');
    if (sleepEndTimeInput) {
        sleepEndTimeInput.value = settings.sleep.endTime;
    }
    
    // Notifications enabled
    const notificationsEnabledInput = document.getElementById('notifications-enabled');
    if (notificationsEnabledInput) {
        notificationsEnabledInput.checked = settings.notifications.enabled;
        
        // Show/hide notification settings based on checkbox
        const notificationSettings = document.getElementById('notification-settings');
        if (notificationSettings) {
            notificationSettings.style.display = settings.notifications.enabled ? 'block' : 'none';
        }
    }
    
    // Notification type
    const notificationTypeSelect = document.getElementById('notification-type');
    if (notificationTypeSelect) {
        notificationTypeSelect.value = settings.notifications.type;
    }
    
    // Update notification parameter fields
    updateNotificationFields();
}

/**
 * Update notification parameter fields based on type
 */
function updateNotificationFields() {
    const notificationParamsContainer = document.getElementById('notification-params');
    if (!notificationParamsContainer) return;
    
    // Clear existing fields
    notificationParamsContainer.innerHTML = '';
    
    // Add fields based on type
    switch (settings.notifications.type) {
        case 'telegram':
            // Add Telegram token field
            const tokenGroup = document.createElement('div');
            tokenGroup.classList.add('form-group');
            
            const tokenLabel = document.createElement('label');
            tokenLabel.textContent = 'Bot Token:';
            
            const tokenInput = document.createElement('input');
            tokenInput.type = 'text';
            tokenInput.id = 'telegram-token';
            tokenInput.classList.add('form-control');
            tokenInput.value = settings.notifications.params.token || '';
            tokenInput.addEventListener('change', function() {
                settings.notifications.params.token = this.value;
            });
            
            tokenGroup.appendChild(tokenLabel);
            tokenGroup.appendChild(tokenInput);
            
            // Add Telegram chat ID field
            const chatIdGroup = document.createElement('div');
            chatIdGroup.classList.add('form-group');
            
            const chatIdLabel = document.createElement('label');
            chatIdLabel.textContent = 'Chat ID:';
            
            const chatIdInput = document.createElement('input');
            chatIdInput.type = 'text';
            chatIdInput.id = 'telegram-chat-id';
            chatIdInput.classList.add('form-control');
            chatIdInput.value = settings.notifications.params.chatId || '';
            chatIdInput.addEventListener('change', function() {
                settings.notifications.params.chatId = this.value;
            });
            
            chatIdGroup.appendChild(chatIdLabel);
            chatIdGroup.appendChild(chatIdInput);
            
            // Add button to test Telegram
            const testButton = document.createElement('button');
            testButton.type = 'button';
            testButton.classList.add('btn', 'btn-info');
            testButton.textContent = 'Test Telegram Notification';
            testButton.addEventListener('click', function() {
                testTelegramNotification();
            });
            
            notificationParamsContainer.appendChild(tokenGroup);
            notificationParamsContainer.appendChild(chatIdGroup);
            notificationParamsContainer.appendChild(testButton);
            break;
            
        case 'pushbullet':
            // Add Pushbullet API key field
            const apiKeyGroup = document.createElement('div');
            apiKeyGroup.classList.add('form-group');
            
            const apiKeyLabel = document.createElement('label');
            apiKeyLabel.textContent = 'API Key:';
            
            const apiKeyInput = document.createElement('input');
            apiKeyInput.type = 'text';
            apiKeyInput.id = 'pushbullet-api-key';
            apiKeyInput.classList.add('form-control');
            apiKeyInput.value = settings.notifications.params.apiKey || '';
            apiKeyInput.addEventListener('change', function() {
                settings.notifications.params.apiKey = this.value;
            });
            
            apiKeyGroup.appendChild(apiKeyLabel);
            apiKeyGroup.appendChild(apiKeyInput);
            
            // Add button to test Pushbullet
            const testPushbulletButton = document.createElement('button');
            testPushbulletButton.type = 'button';
            testPushbulletButton.classList.add('btn', 'btn-info');
            testPushbulletButton.textContent = 'Test Pushbullet Notification';
            testPushbulletButton.addEventListener('click', function() {
                testPushbulletNotification();
            });
            
            notificationParamsContainer.appendChild(apiKeyGroup);
            notificationParamsContainer.appendChild(testPushbulletButton);
            break;
            
        // Add other notification types as needed
    }
}

/**
 * Save settings to server
 */
function saveSettings() {
    console.log("Saving settings:", settings);
    
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(result => {
        console.log("Save settings result:", result);
        
        if (result.success) {
            showNotification('Settings saved successfully', 'success');
        } else {
            showNotification(`Failed to save settings: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error saving settings:", error);
        showNotification('Error saving settings', 'error');
    });
}

/**
 * Test sensors
 */
function testSensors() {
    console.log("Testing sensors...");
    
    fetch('/api/system/test-sensors', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        console.log("Sensor test result:", result);
        
        if (result.success) {
            showNotification('Sensor test completed', 'success');
            
            // Display test results
            const resultsContainer = document.getElementById('sensor-test-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
                
                // Create result table
                const table = document.createElement('table');
                table.classList.add('table', 'table-sm', 'table-bordered');
                
                // Add header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                const sensorHeader = document.createElement('th');
                sensorHeader.textContent = 'Sensor';
                
                const statusHeader = document.createElement('th');
                statusHeader.textContent = 'Status';
                
                const valuesHeader = document.createElement('th');
                valuesHeader.textContent = 'Values';
                
                headerRow.appendChild(sensorHeader);
                headerRow.appendChild(statusHeader);
                headerRow.appendChild(valuesHeader);
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Add body
                const tbody = document.createElement('tbody');
                
                for (const [sensor, data] of Object.entries(result.results)) {
                    const row = document.createElement('tr');
                    
                    const sensorCell = document.createElement('td');
                    sensorCell.textContent = sensor;
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = data.status;
                    statusCell.classList.add(data.status === 'OK' ? 'text-success' : 'text-danger');
                    
                    const valuesCell = document.createElement('td');
                    if (data.values) {
                        let valuesText = '';
                        for (const [key, value] of Object.entries(data.values)) {
                            valuesText += `${key}: ${value}<br>`;
                        }
                        valuesCell.innerHTML = valuesText;
                    } else {
                        valuesCell.textContent = 'N/A';
                    }
                    
                    row.appendChild(sensorCell);
                    row.appendChild(statusCell);
                    row.appendChild(valuesCell);
                    tbody.appendChild(row);
                }
                
                table.appendChild(tbody);
                resultsContainer.appendChild(table);
            }
        } else {
            showNotification(`Sensor test failed: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error testing sensors:", error);
        showNotification('Error testing sensors', 'error');
    });
}

/**
 * Test relays
 */
function testRelays() {
    console.log("Testing relays...");
    
    fetch('/api/system/test-relays', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        console.log("Relay test result:", result);
        
        if (result.success) {
            showNotification('Relay test completed', 'success');
            
            // Display test results
            const resultsContainer = document.getElementById('relay-test-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
                
                // Create result table
                const table = document.createElement('table');
                table.classList.add('table', 'table-sm', 'table-bordered');
                
                // Add header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                const relayHeader = document.createElement('th');
                relayHeader.textContent = 'Relay';
                
                const statusHeader = document.createElement('th');
                statusHeader.textContent = 'Status';
                
                headerRow.appendChild(relayHeader);
                headerRow.appendChild(statusHeader);
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Add body
                const tbody = document.createElement('tbody');
                
                for (const [relay, status] of Object.entries(result.results)) {
                    const row = document.createElement('tr');
                    
                    const relayCell = document.createElement('td');
                    relayCell.textContent = relay;
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = status ? 'OK' : 'Failed';
                    statusCell.classList.add(status ? 'text-success' : 'text-danger');
                    
                    row.appendChild(relayCell);
                    row.appendChild(statusCell);
                    tbody.appendChild(row);
                }
                
                table.appendChild(tbody);
                resultsContainer.appendChild(table);
            }
        } else {
            showNotification(`Relay test failed: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error testing relays:", error);
        showNotification('Error testing relays', 'error');
    });
}

/**
 * Test Telegram notification
 */
function testTelegramNotification() {
    if (!settings.notifications.params.token || !settings.notifications.params.chatId) {
        showNotification('Please enter Bot Token and Chat ID', 'warning');
        return;
    }
    
    console.log("Testing Telegram notification...");
    
    fetch('/api/notifications/test-telegram', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            token: settings.notifications.params.token,
            chatId: settings.notifications.params.chatId
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log("Telegram test result:", result);
        
        if (result.success) {
            showNotification('Telegram notification sent successfully', 'success');
        } else {
            showNotification(`Failed to send Telegram notification: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error testing Telegram notification:", error);
        showNotification('Error testing Telegram notification', 'error');
    });
}

/**
 * Test Pushbullet notification
 */
function testPushbulletNotification() {
    if (!settings.notifications.params.apiKey) {
        showNotification('Please enter API Key', 'warning');
        return;
    }
    
    console.log("Testing Pushbullet notification...");
    
    fetch('/api/notifications/test-pushbullet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            apiKey: settings.notifications.params.apiKey
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log("Pushbullet test result:", result);
        
        if (result.success) {
            showNotification('Pushbullet notification sent successfully', 'success');
        } else {
            showNotification(`Failed to send Pushbullet notification: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error testing Pushbullet notification:", error);
        showNotification('Error testing Pushbullet notification', 'error');
    });
}

/**
 * Reboot system
 */
function rebootSystem() {
    console.log("Rebooting system...");
    
    // Show reboot notification
    showNotification('System is rebooting...', 'info');
    
    fetch('/api/system/reboot', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        console.log("Reboot result:", result);
        
        if (result.success) {
            // Show countdown
            let countdown = 30;
            const countdownInterval = setInterval(() => {
                showNotification(`System is rebooting. Reconnecting in ${countdown} seconds...`, 'info');
                countdown--;
                
                if (countdown <= 0) {
                    clearInterval(countdownInterval);
                    window.location.reload();
                }
            }, 1000);
        } else {
            showNotification(`Failed to reboot system: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error rebooting system:", error);
        showNotification('Error rebooting system', 'error');
    });
}

/**
 * Factory reset
 */
function factoryReset() {
    console.log("Factory resetting system...");
    
    // Show reset notification
    showNotification('Performing factory reset...', 'info');
    
    fetch('/api/system/factory-reset', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        console.log("Factory reset result:", result);
        
        if (result.success) {
            // Show countdown
            let countdown = 30;
            const countdownInterval = setInterval(() => {
                showNotification(`Factory reset complete. System is rebooting. Reconnecting in ${countdown} seconds...`, 'info');
                countdown--;
                
                if (countdown <= 0) {
                    clearInterval(countdownInterval);
                    window.location.reload();
                }
            }, 1000);
        } else {
            showNotification(`Failed to factory reset system: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error factory resetting system:", error);
        showNotification('Error factory resetting system', 'error');
    });
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info, warning)
 */
function showNotification(message, type = 'info') {
    // Check if notification function exists in the global scope
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        // Fallback to alert
        alert(message);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with settings
    if (document.getElementById('settings-save-btn')) {
        initSettings();
    }
});

// Expose functions for use in other scripts
window.settings = {
    getSettings: () => settings,
    updateSettings: (newSettings) => {
        settings = { ...settings, ...newSettings };
        updateSettingsUI();
    },
    saveSettings,
    rebootSystem,
    factoryReset,
    testSensors,
    testRelays
};
 */
function fetch