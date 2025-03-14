/**
 * network.js
 * Handles network configuration for the Mushroom Tent Controller
 */

// Global variables
let networkConfig = {
    wifi: {
        networks: [
            { ssid: '', password: '', mac: '' },
            { ssid: '', password: '', mac: '' },
            { ssid: '', password: '', mac: '' }
        ],
        currentNetwork: 0
    },
    ip: {
        mode: 'dhcp',
        static: {
            ip: '',
            netmask: '',
            gateway: '',
            dns1: '',
            dns2: ''
        }
    },
    mdns: {
        hostname: 'mushroom-controller'
    },
    watchdog: {
        minRssi: -80,
        checkInterval: 60 // seconds
    },
    mqtt: {
        enabled: false,
        broker: '',
        port: 1883,
        topic: 'mushroom/tent',
        username: '',
        password: ''
    }
};

let availableNetworks = [];

/**
 * Initialize network configuration UI
 */
function initNetworkConfig() {
    console.log("Initializing network configuration...");
    
    // Fetch network configuration
    fetchNetworkConfig();
    
    // Set up UI elements
    setupNetworkUI();
}

/**
 * Fetch network configuration from server
 */
function fetchNetworkConfig() {
    fetch('/api/network/config')
        .then(response => response.json())
        .then(config => {
            console.log("Network configuration loaded:", config);
            
            // Update network configuration
            networkConfig = config;
            
            // Update UI
            updateNetworkUI();
        })
        .catch(error => {
            console.error("Error loading network configuration:", error);
        });
}

/**
 * Set up network UI elements
 */
function setupNetworkUI() {
    // WiFi network selection buttons
    for (let i = 1; i <= 3; i++) {
        const selectButton = document.getElementById(`select-wifi${i}-btn`);
        if (selectButton) {
            selectButton.addEventListener('click', function() {
                scanWifiNetworks(i - 1);
            });
        }
    }
    
    // IP Configuration radio buttons
    const dhcpRadio = document.getElementById('ip-mode-dhcp');
    const staticRadio = document.getElementById('ip-mode-static');
    
    if (dhcpRadio && staticRadio) {
        dhcpRadio.addEventListener('change', function() {
            if (this.checked) {
                networkConfig.ip.mode = 'dhcp';
                toggleStaticIpFields(false);
            }
        });
        
        staticRadio.addEventListener('change', function() {
            if (this.checked) {
                networkConfig.ip.mode = 'static';
                toggleStaticIpFields(true);
            }
        });
    }
    
    // mDNS hostname
    const hostnameInput = document.getElementById('mdns-hostname');
    if (hostnameInput) {
        hostnameInput.addEventListener('change', function() {
            networkConfig.mdns.hostname = this.value;
        });
    }
    
    // Watchdog min RSSI
    const minRssiInput = document.getElementById('min-rssi');
    if (minRssiInput) {
        minRssiInput.addEventListener('change', function() {
            networkConfig.watchdog.minRssi = parseInt(this.value);
        });
    }
    
    // Watchdog check interval
    const checkIntervalInput = document.getElementById('watchdog-interval');
    if (checkIntervalInput) {
        checkIntervalInput.addEventListener('change', function() {
            networkConfig.watchdog.checkInterval = parseInt(this.value);
        });
    }
    
    // MQTT toggle
    const mqttOffRadio = document.getElementById('mqtt-off');
    const mqttOnRadio = document.getElementById('mqtt-on');
    
    if (mqttOffRadio && mqttOnRadio) {
        mqttOffRadio.addEventListener('change', function() {
            if (this.checked) {
                networkConfig.mqtt.enabled = false;
                toggleMqttFields(false);
            }
        });
        
        mqttOnRadio.addEventListener('change', function() {
            if (this.checked) {
                networkConfig.mqtt.enabled = true;
                toggleMqttFields(true);
            }
        });
    }
    
    // MQTT fields
    const mqttBrokerInput = document.getElementById('mqtt-broker');
    if (mqttBrokerInput) {
        mqttBrokerInput.addEventListener('change', function() {
            networkConfig.mqtt.broker = this.value;
        });
    }
    
    const mqttPortInput = document.getElementById('mqtt-port');
    if (mqttPortInput) {
        mqttPortInput.addEventListener('change', function() {
            networkConfig.mqtt.port = parseInt(this.value);
        });
    }
    
    const mqttTopicInput = document.getElementById('mqtt-topic');
    if (mqttTopicInput) {
        mqttTopicInput.addEventListener('change', function() {
            networkConfig.mqtt.topic = this.value;
        });
    }
    
    const mqttUsernameInput = document.getElementById('mqtt-username');
    if (mqttUsernameInput) {
        mqttUsernameInput.addEventListener('change', function() {
            networkConfig.mqtt.username = this.value;
        });
    }
    
    const mqttPasswordInput = document.getElementById('mqtt-password');
    if (mqttPasswordInput) {
        mqttPasswordInput.addEventListener('change', function() {
            networkConfig.mqtt.password = this.value;
        });
    }
    
    // Static IP fields
    const staticIpInput = document.getElementById('static-ip');
    if (staticIpInput) {
        staticIpInput.addEventListener('change', function() {
            networkConfig.ip.static.ip = this.value;
        });
    }
    
    const staticNetmaskInput = document.getElementById('static-netmask');
    if (staticNetmaskInput) {
        staticNetmaskInput.addEventListener('change', function() {
            networkConfig.ip.static.netmask = this.value;
        });
    }
    
    const staticGatewayInput = document.getElementById('static-gateway');
    if (staticGatewayInput) {
        staticGatewayInput.addEventListener('change', function() {
            networkConfig.ip.static.gateway = this.value;
        });
    }
    
    const staticDns1Input = document.getElementById('static-dns1');
    if (staticDns1Input) {
        staticDns1Input.addEventListener('change', function() {
            networkConfig.ip.static.dns1 = this.value;
        });
    }
    
    const staticDns2Input = document.getElementById('static-dns2');
    if (staticDns2Input) {
        staticDns2Input.addEventListener('change', function() {
            networkConfig.ip.static.dns2 = this.value;
        });
    }
    
    // Save button
    const saveButton = document.getElementById('network-save-btn');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            saveNetworkConfig();
        });
    }
}

/**
 * Update network UI with current values
 */
function updateNetworkUI() {
    // Update WiFi network labels
    for (let i = 0; i < 3; i++) {
        const wifiLabel = document.getElementById(`wifi${i+1}-label`);
        if (wifiLabel) {
            const network = networkConfig.wifi.networks[i];
            if (network && network.ssid) {
                wifiLabel.textContent = `${network.ssid} (${network.mac || 'Unknown MAC'})`;
            } else {
                wifiLabel.textContent = 'Not configured';
            }
        }
    }
    
    // Update IP mode radio buttons
    const dhcpRadio = document.getElementById('ip-mode-dhcp');
    const staticRadio = document.getElementById('ip-mode-static');
    
    if (dhcpRadio && staticRadio) {
        if (networkConfig.ip.mode === 'dhcp') {
            dhcpRadio.checked = true;
            staticRadio.checked = false;
            toggleStaticIpFields(false);
        } else {
            dhcpRadio.checked = false;
            staticRadio.checked = true;
            toggleStaticIpFields(true);
        }
    }
    
    // Update mDNS hostname
    const hostnameInput = document.getElementById('mdns-hostname');
    if (hostnameInput) {
        hostnameInput.value = networkConfig.mdns.hostname;
    }
    
    // Update Watchdog min RSSI
    const minRssiInput = document.getElementById('min-rssi');
    if (minRssiInput) {
        minRssiInput.value = networkConfig.watchdog.minRssi;
    }
    
    // Update Watchdog check interval
    const checkIntervalInput = document.getElementById('watchdog-interval');
    if (checkIntervalInput) {
        checkIntervalInput.value = networkConfig.watchdog.checkInterval;
    }
    
    // Update MQTT toggle
    const mqttOffRadio = document.getElementById('mqtt-off');
    const mqttOnRadio = document.getElementById('mqtt-on');
    
    if (mqttOffRadio && mqttOnRadio) {
        if (networkConfig.mqtt.enabled) {
            mqttOffRadio.checked = false;
            mqttOnRadio.checked = true;
            toggleMqttFields(true);
        } else {
            mqttOffRadio.checked = true;
            mqttOnRadio.checked = false;
            toggleMqttFields(false);
        }
    }
    
    // Update MQTT fields
    const mqttBrokerInput = document.getElementById('mqtt-broker');
    if (mqttBrokerInput) {
        mqttBrokerInput.value = networkConfig.mqtt.broker;
    }
    
    const mqttPortInput = document.getElementById('mqtt-port');
    if (mqttPortInput) {
        mqttPortInput.value = networkConfig.mqtt.port;
    }
    
    const mqttTopicInput = document.getElementById('mqtt-topic');
    if (mqttTopicInput) {
        mqttTopicInput.value = networkConfig.mqtt.topic;
    }
    
    const mqttUsernameInput = document.getElementById('mqtt-username');
    if (mqttUsernameInput) {
        mqttUsernameInput.value = networkConfig.mqtt.username;
    }
    
    const mqttPasswordInput = document.getElementById('mqtt-password');
    if (mqttPasswordInput) {
        mqttPasswordInput.value = networkConfig.mqtt.password;
    }
    
    // Update Static IP fields
    const staticIpInput = document.getElementById('static-ip');
    if (staticIpInput) {
        staticIpInput.value = networkConfig.ip.static.ip;
    }
    
    const staticNetmaskInput = document.getElementById('static-netmask');
    if (staticNetmaskInput) {
        staticNetmaskInput.value = networkConfig.ip.static.netmask;
    }
    
    const staticGatewayInput = document.getElementById('static-gateway');
    if (staticGatewayInput) {
        staticGatewayInput.value = networkConfig.ip.static.gateway;
    }
    
    const staticDns1Input = document.getElementById('static-dns1');
    if (staticDns1Input) {
        staticDns1Input.value = networkConfig.ip.static.dns1;
    }
    
    const staticDns2Input = document.getElementById('static-dns2');
    if (staticDns2Input) {
        staticDns2Input.value = networkConfig.ip.static.dns2;
    }
}

/**
 * Toggle visibility of static IP fields
 * @param {boolean} show - Whether to show or hide fields
 */
function toggleStaticIpFields(show) {
    const staticIpFields = document.getElementById('static-ip-fields');
    if (staticIpFields) {
        staticIpFields.style.display = show ? 'block' : 'none';
    }
}

/**
 * Toggle visibility of MQTT fields
 * @param {boolean} show - Whether to show or hide fields
 */
function toggleMqttFields(show) {
    const mqttFields = document.getElementById('mqtt-fields');
    if (mqttFields) {
        mqttFields.style.display = show ? 'block' : 'none';
    }
}

/**
 * Scan for WiFi networks
 * @param {number} networkIndex - Index of the WiFi network to configure (0-2)
 */
function scanWifiNetworks(networkIndex) {
    console.log(`Scanning WiFi networks for slot ${networkIndex + 1}...`);
    
    // Show loading spinner
    showNetworkScanSpinner(true);
    
    // Clear previous scan results
    availableNetworks = [];
    
    // Request scan from server
    fetch('/api/network/scan-wifi')
        .then(response => response.json())
        .then(data => {
            console.log("WiFi scan result:", data);
            
            // Hide loading spinner
            showNetworkScanSpinner(false);
            
            if (data.success) {
                // Store networks
                availableNetworks = data.networks;
                
                // Show network selection modal
                showWifiSelectionModal(networkIndex);
            } else {
                showNotification(`Failed to scan WiFi networks: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            console.error("Error scanning WiFi networks:", error);
            showNetworkScanSpinner(false);
            showNotification('Error scanning WiFi networks', 'error');
        });
}

/**
 * Show or hide network scan spinner
 * @param {boolean} show - Whether to show or hide spinner
 */
function showNetworkScanSpinner(show) {
    const spinner = document.getElementById('network-scan-spinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

/**
 * Show WiFi selection modal
 * @param {number} networkIndex - Index of the WiFi network to configure (0-2)
 */
function showWifiSelectionModal(networkIndex) {
    // Create modal content
    const modalContent = document.createElement('div');
    
    // Add title
    const title = document.createElement('h4');
    title.textContent = `Select WiFi Network for Slot ${networkIndex + 1}`;
    modalContent.appendChild(title);
    
    // Add network list
    const networkList = document.createElement('div');
    networkList.className = 'network-list';
    
    if (availableNetworks.length === 0) {
        const noNetworks = document.createElement('p');
        noNetworks.textContent = 'No networks found.';
        networkList.appendChild(noNetworks);
    } else {
        // Add table
        const table = document.createElement('table');
        table.className = 'table table-striped';
        
        // Add table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        const ssidHeader = document.createElement('th');
        ssidHeader.textContent = 'SSID';
        
        const rssiHeader = document.createElement('th');
        rssiHeader.textContent = 'Signal';
        
        const macHeader = document.createElement('th');
        macHeader.textContent = 'MAC';
        
        const securityHeader = document.createElement('th');
        securityHeader.textContent = 'Security';
        
        const actionHeader = document.createElement('th');
        actionHeader.textContent = 'Action';
        
        headerRow.appendChild(ssidHeader);
        headerRow.appendChild(rssiHeader);
        headerRow.appendChild(macHeader);
        headerRow.appendChild(securityHeader);
        headerRow.appendChild(actionHeader);
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Add table body
        const tbody = document.createElement('tbody');
        
        availableNetworks.forEach(network => {
            const row = document.createElement('tr');
            
            const ssidCell = document.createElement('td');
            ssidCell.textContent = network.ssid;
            
            const rssiCell = document.createElement('td');
            // Convert RSSI to signal bars
            const rssiPercent = Math.min(100, Math.max(0, 2 * (network.rssi + 100)));
            const bars = Math.ceil(rssiPercent / 20); // 1-5 bars
            
            let barsHtml = '';
            for (let i = 0; i < 5; i++) {
                if (i < bars) {
                    barsHtml += '<i class="fas fa-signal-alt"></i>';
                } else {
                    barsHtml += '<i class="fas fa-signal-alt-slash"></i>';
                }
            }
            rssiCell.innerHTML = `${barsHtml} (${network.rssi} dBm)`;
            
            const macCell = document.createElement('td');
            macCell.textContent = network.mac;
            
            const securityCell = document.createElement('td');
            securityCell.textContent = network.security;
            
            const actionCell = document.createElement('td');
            const selectButton = document.createElement('button');
            selectButton.className = 'btn btn-sm btn-primary';
            selectButton.textContent = 'Select';
            selectButton.addEventListener('click', function() {
                selectWifiNetwork(networkIndex, network);
            });
            actionCell.appendChild(selectButton);
            
            row.appendChild(ssidCell);
            row.appendChild(rssiCell);
            row.appendChild(macCell);
            row.appendChild(securityCell);
            row.appendChild(actionCell);
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        networkList.appendChild(table);
    }
    
    modalContent.appendChild(networkList);
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'btn btn-secondary';
    closeButton.textContent = 'Cancel';
    closeButton.addEventListener('click', function() {
        closeModal();
    });
    modalContent.appendChild(closeButton);
    
    // Show modal
    showModal('Select WiFi Network', modalContent);
}

/**
 * Select WiFi network
 * @param {number} networkIndex - Index of the WiFi network to configure (0-2)
 * @param {Object} network - Network information
 */
function selectWifiNetwork(networkIndex, network) {
    console.log(`Selected network ${network.ssid} for slot ${networkIndex + 1}`);
    
    // Ask for password if needed
    if (network.security !== 'Open') {
        // Create password input form
        const passwordForm = document.createElement('div');
        
        const passwordLabel = document.createElement('label');
        passwordLabel.textContent = `Enter password for ${network.ssid}:`;
        passwordLabel.setAttribute('for', 'wifi-password');
        
        const passwordInput = document.createElement('input');
        passwordInput.type = 'password';
        passwordInput.id = 'wifi-password';
        passwordInput.className = 'form-control';
        
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'mt-3';
        
        const saveButton = document.createElement('button');
        saveButton.className = 'btn btn-primary';
        saveButton.textContent = 'Save';
        saveButton.addEventListener('click', function() {
            const password = passwordInput.value;
            if (password) {
                saveWifiNetwork(networkIndex, network, password);
            } else {
                showNotification('Please enter a password', 'warning');
            }
        });
        
        const cancelButton = document.createElement('button');
        cancelButton.className = 'btn btn-secondary ml-2';
        cancelButton.textContent = 'Cancel';
        cancelButton.addEventListener('click', function() {
            closeModal();
        });
        
        buttonContainer.appendChild(saveButton);
        buttonContainer.appendChild(cancelButton);
        
        passwordForm.appendChild(passwordLabel);
        passwordForm.appendChild(passwordInput);
        passwordForm.appendChild(buttonContainer);
        
        // Show modal with password form
        showModal(`Enter WiFi Password`, passwordForm);
    } else {
        // Open network, no password needed
        saveWifiNetwork(networkIndex, network, '');
    }
}

/**
 * Save WiFi network
 * @param {number} networkIndex - Index of the WiFi network to configure (0-2)
 * @param {Object} network - Network information
 * @param {string} password - WiFi password
 */
function saveWifiNetwork(networkIndex, network, password) {
    console.log(`Saving network ${network.ssid} with password to slot ${networkIndex + 1}`);
    
    // Update local configuration
    networkConfig.wifi.networks[networkIndex] = {
        ssid: network.ssid,
        password: password,
        mac: network.mac
    };
    
    // Update UI
    updateNetworkUI();
    
    // Close modal
    closeModal();
    
    // Show notification
    showNotification(`WiFi network ${network.ssid} saved to slot ${networkIndex + 1}`, 'success');
}

/**
 * Show modal
 * @param {string} title - Modal title
 * @param {HTMLElement} content - Modal content element
 */
function showModal(title, content) {
    // Get or create modal container
    let modalContainer = document.getElementById('network-modal-container');
    
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.id = 'network-modal-container';
        modalContainer.className = 'modal fade';
        modalContainer.tabIndex = -1;
        modalContainer.role = 'dialog';
        modalContainer.setAttribute('aria-hidden', 'true');
        
        document.body.appendChild(modalContainer);
    }
    
    // Create modal content
    modalContainer.innerHTML = `
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close" onclick="window.network.closeModal()">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body" id="network-modal-body">
                </div>
            </div>
        </div>
    `;
    
    // Add content to modal body
    const modalBody = document.getElementById('network-modal-body');
    modalBody.innerHTML = '';
    modalBody.appendChild(content);
    
    // Show modal
    $(modalContainer).modal('show');
}

/**
 * Close modal
 */
function closeModal() {
    const modalContainer = document.getElementById('network-modal-container');
    if (modalContainer) {
        $(modalContainer).modal('hide');
    }
}

/**
 * Save network configuration to server
 */
function saveNetworkConfig() {
    console.log("Saving network configuration:", networkConfig);
    
    fetch('/api/network/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(networkConfig)
    })
    .then(response => response.json())
    .then(result => {
        console.log("Save network config result:", result);
        
        if (result.success) {
            showNotification('Network configuration saved successfully', 'success');
            
            // Check if restart is needed
            if (result.restartRequired) {
                if (confirm('Network configuration updated. A restart is required for changes to take effect. Restart now?')) {
                    restartNetworkServices();
                }
            }
        } else {
            showNotification(`Failed to save network configuration: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error saving network configuration:", error);
        showNotification('Error saving network configuration', 'error');
    });
}

/**
 * Restart network services
 */
function restartNetworkServices() {
    console.log("Restarting network services...");
    
    fetch('/api/network/restart', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        console.log("Restart network result:", result);
        
        if (result.success) {
            showNotification('Network services are restarting...', 'info');
            
            // Wait for services to restart, then refresh network status
            setTimeout(() => {
                fetchNetworkStatus();
            }, 5000);
        } else {
            showNotification(`Failed to restart network services: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error restarting network services:", error);
        showNotification('Error restarting network services', 'error');
    });
}

/**
 * Fetch current network status
 */
function fetchNetworkStatus() {
    fetch('/api/network/status')
        .then(response => response.json())
        .then(status => {
            console.log("Network status:", status);
            
            // Update status UI
            updateNetworkStatusUI(status);
        })
        .catch(error => {
            console.error("Error fetching network status:", error);
            showNotification('Error fetching network status', 'error');
        });
}

/**
 * Update network status UI
 * @param {Object} status - Network status information
 */
function updateNetworkStatusUI(status) {
    // Update WiFi status if element exists
    const wifiStatus = document.getElementById('wifi-status');
    if (wifiStatus) {
        if (status.connected) {
            wifiStatus.innerHTML = `
                <div class="alert alert-success">
                    <strong>Connected:</strong> ${status.ssid} (${status.rssi} dBm)
                    <br><strong>IP:</strong> ${status.ip}
                    <br><strong>MAC:</strong> ${status.mac}
                </div>
            `;
        } else {
            wifiStatus.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Disconnected</strong>
                </div>
            `;
        }
    }
    
    // Update MQTT status if element exists
    const mqttStatus = document.getElementById('mqtt-status');
    if (mqttStatus) {
        if (status.mqtt && status.mqtt.enabled) {
            if (status.mqtt.connected) {
                mqttStatus.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Connected:</strong> ${status.mqtt.broker}
                        <br><strong>Topic:</strong> ${status.mqtt.topic}
                    </div>
                `;
            } else {
                mqttStatus.innerHTML = `
                    <div class="alert alert-warning">
                        <strong>Disconnected from MQTT broker</strong>
                    </div>
                `;
            }
        } else {
            mqttStatus.innerHTML = `
                <div class="alert alert-secondary">
                    <strong>MQTT Disabled</strong>
                </div>
            `;
        }
    }
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
    // Check if we're on a page with the network modal
    if (document.getElementById('network-save-btn')) {
        initNetworkConfig();
        
        // Fetch initial network status
        fetchNetworkStatus();
        
        // Set up periodic network status updates
        setInterval(fetchNetworkStatus, 30000); // Update every 30 seconds
    }
});

// Expose functions for use in other scripts
window.network = {
    getNetworkConfig: () => networkConfig,
    saveNetworkConfig,
    restartNetworkServices,
    fetchNetworkStatus,
    closeModal
};