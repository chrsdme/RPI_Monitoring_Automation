/**
 * relays.js
 * Handles relay control and status for the Mushroom Tent Controller
 */

// Global variables
let relays = {
    // Key is relay ID, value is relay info
    1: { name: "Main PSU", pin: 18, status: false, dependency: [], visible: false, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    2: { name: "UV Light", pin: 24, status: false, dependency: [1], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    3: { name: "Grow Light", pin: 25, status: false, dependency: [1], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    4: { name: "Tub Fans", pin: 6, status: false, dependency: [1], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    5: { name: "Humidifiers", pin: 0, status: false, dependency: [1], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    6: { name: "Heater", pin: 0, status: false, dependency: [], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    7: { name: "IN/OUT Fans", pin: 0, status: false, dependency: [1], visible: true, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 },
    8: { name: "Reserved", pin: 0, status: false, dependency: [], visible: false, schedule: { start: "00:00", end: "23:59" }, overrideTimeout: 300 }
};

// Track override timers
let overrideTimers = {};

// Automation parameters
let automationConfig = {
    humidifier: {
        lowThreshold: 50,
        highThreshold: 85
    },
    heater: {
        lowThreshold: 20,
        highThreshold: 24
    },
    co2: {
        lowThreshold: 1100,
        highThreshold: 1600
    },
    fans: {
        onDuration: 10, // minutes
        cycleInterval: 60 // minutes
    }
};

/**
 * Initialize relay system
 */
function initRelays() {
    console.log("Initializing relay system...");
    
    // Fetch relay configuration
    fetchRelayConfig();
    
    // Set up UI elements
    setupRelayUI();
    
    // Initial status update
    updateRelayStatus();
}

/**
 * Fetch relay configuration from the server
 */
function fetchRelayConfig() {
    fetch('/api/config/relays')
        .then(response => response.json())
        .then(config => {
            console.log("Relay configuration loaded:", config);
            
            // Update relay configuration
            if (config.relays) {
                relays = config.relays;
            }
            
            // Update automation config
            if (config.automation) {
                automationConfig = config.automation;
            }
            
            // Update UI with new configuration
            updateRelayUI();
        })
        .catch(error => {
            console.error("Error loading relay configuration:", error);
        });
}

/**
 * Setup relay UI elements
 */
function setupRelayUI() {
    // Set up relay toggle buttons
    document.querySelectorAll('.relay-toggle').forEach(toggle => {
        const relayId = toggle.dataset.relay;
        
        toggle.addEventListener('change', function() {
            toggleRelay(relayId, this.checked);
        });
    });
}

/**
 * Update relay UI elements to reflect current configuration
 */
function updateRelayUI() {
    // Update all relay toggle elements
    for (const [id, relay] of Object.entries(relays)) {
        // Only update visible relays
        if (!relay.visible) continue;
        
        const toggleContainer = document.getElementById(`relay-${id}-container`);
        if (toggleContainer) {
            // Show or hide based on visibility
            toggleContainer.style.display = relay.visible ? 'block' : 'none';
            
            // Update label
            const label = toggleContainer.querySelector('label');
            if (label) {
                label.textContent = relay.name;
            }
            
            // Update toggle state
            const toggle = toggleContainer.querySelector('.relay-toggle');
            if (toggle) {
                toggle.checked = relay.status;
                
                // Update toggle colors
                updateToggleColors(id, relay.status);
            }
        }
    }
}

/**
 * Update toggle button colors based on status
 * @param {string} relayId - Relay ID
 * @param {boolean} status - Relay status (on/off)
 */
function updateToggleColors(relayId, status) {
    const toggle = document.querySelector(`.relay-toggle[data-relay="${relayId}"]`);
    if (!toggle) return;
    
    // Get the toggle background element
    const toggleBg = toggle.closest('.toggle-container');
    if (!toggleBg) return;
    
    // Update colors
    if (status) {
        toggleBg.classList.remove('bg-red-500');
        toggleBg.classList.add('bg-green-500');
    } else {
        toggleBg.classList.remove('bg-green-500');
        toggleBg.classList.add('bg-red-500');
    }
}

/**
 * Toggle relay state
 * @param {string} relayId - Relay ID to toggle
 * @param {boolean} state - Desired state (true = on, false = off)
 * @param {boolean} [override=true] - Whether this is a manual override
 */
function toggleRelay(relayId, state, override = true) {
    console.log(`Toggling relay ${relayId} to ${state ? 'ON' : 'OFF'}`);
    
    // Send command to server
    fetch(`/api/relays/${relayId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            state: state,
            override: override
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log("Relay toggle result:", result);
        
        if (result.success) {
            // Update local state
            relays[relayId].status = state;
            
            // Update UI
            updateToggleColors(relayId, state);
            
            // Set override timeout if this is a manual override
            if (override) {
                setOverrideTimeout(relayId);
            }
            
            // Check dependencies
            handleDependencies(relayId, state);
        } else {
            console.error("Failed to toggle relay:", result.message);
            
            // Revert toggle in UI
            const toggle = document.querySelector(`.relay-toggle[data-relay="${relayId}"]`);
            if (toggle) {
                toggle.checked = !state;
                updateToggleColors(relayId, !state);
            }
        }
    })
    .catch(error => {
        console.error("Error toggling relay:", error);
        
        // Revert toggle in UI
        const toggle = document.querySelector(`.relay-toggle[data-relay="${relayId}"]`);
        if (toggle) {
            toggle.checked = !state;
            updateToggleColors(relayId, !state);
        }
    });
}

/**
 * Set override timeout for relay
 * @param {string} relayId - Relay ID
 */
function setOverrideTimeout(relayId) {
    // Clear existing timer
    if (overrideTimers[relayId]) {
        clearTimeout(overrideTimers[relayId]);
    }
    
    // Set new timer
    const timeoutSecs = relays[relayId].overrideTimeout || 300; // Default 5 minutes
    
    console.log(`Setting override timeout for relay ${relayId} to ${timeoutSecs} seconds`);
    
    overrideTimers[relayId] = setTimeout(() => {
        console.log(`Override timeout for relay ${relayId} expired`);
        
        // Reset to automatic control
        fetch(`/api/relays/${relayId}/reset-override`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            console.log("Reset override result:", result);
            
            if (result.success) {
                // Update local state if the relay state changed
                if (relays[relayId].status !== result.state) {
                    relays[relayId].status = result.state;
                    
                    // Update UI
                    const toggle = document.querySelector(`.relay-toggle[data-relay="${relayId}"]`);
                    if (toggle) {
                        toggle.checked = result.state;
                        updateToggleColors(relayId, result.state);
                    }
                }
            }
        })
        .catch(error => {
            console.error("Error resetting relay override:", error);
        });
        
    }, timeoutSecs * 1000);
}

/**
 * Handle relay dependencies
 * @param {string} relayId - Relay ID that changed
 * @param {boolean} state - New state
 */
function handleDependencies(relayId, state) {
    // If turning on relay 1 (main PSU), nothing to do
    if (relayId === '1' && state === true) {
        return;
    }
    
    // If turning off relay 1 (main PSU), need to turn off dependent relays
    if (relayId === '1' && state === false) {
        for (const [id, relay] of Object.entries(relays)) {
            if (relay.dependency.includes(1)) {
                // Turn off dependent relay
                toggleRelay(id, false, false);
            }
        }
        return;
    }
    
    // If turning on a relay that depends on relay 1, make sure relay 1 is on
    if (state === true && relays[relayId].dependency.includes(1)) {
        if (!relays['1'].status) {
            // Turn on relay 1 first
            toggleRelay('1', true, false);
        }
    }
}

/**
 * Update relay status from server
 */
function updateRelayStatus() {
    fetch('/api/relays')
        .then(response => response.json())
        .then(status => {
            console.log("Relay status updated:", status);
            
            // Update local state
            for (const [id, state] of Object.entries(status)) {
                if (relays[id]) {
                    relays[id].status = state.status;
                }
            }
            
            // Update UI
            updateRelayUI();
        })
        .catch(error => {
            console.error("Error updating relay status:", error);
        });
}

        })
        .catch(error => {
            console.error("Error updating relay status:", error);
        });
}

/**
 * Save relay configuration to server
 */
function saveRelayConfig() {
    fetch('/api/config/relays', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            relays: relays,
            automation: automationConfig
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log("Relay configuration saved:", result);
        
        if (result.success) {
            // Show success notification
            showNotification('Relay configuration saved successfully', 'success');
        } else {
            // Show error notification
            showNotification('Failed to save relay configuration: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error("Error saving relay configuration:", error);
        showNotification('Error saving relay configuration', 'error');
    });
}

/**
 * Update relay name
 * @param {string} relayId - Relay ID
 * @param {string} name - New name
 */
function updateRelayName(relayId, name) {
    relays[relayId].name = name;
    updateRelayUI();
}

/**
 * Update relay pin assignment
 * @param {string} relayId - Relay ID
 * @param {number} pin - GPIO pin number
 */
function updateRelayPin(relayId, pin) {
    relays[relayId].pin = parseInt(pin);
}

/**
 * Update relay schedule
 * @param {string} relayId - Relay ID
 * @param {string} start - Start time (HH:MM)
 * @param {string} end - End time (HH:MM)
 */
function updateRelaySchedule(relayId, start, end) {
    relays[relayId].schedule.start = start;
    relays[relayId].schedule.end = end;
}

/**
 * Update relay dependencies
 * @param {string} relayId - Relay ID
 * @param {Array<number>} dependencies - Array of relay IDs this relay depends on
 */
function updateRelayDependencies(relayId, dependencies) {
    relays[relayId].dependency = dependencies;
}

/**
 * Update relay visibility
 * @param {string} relayId - Relay ID
 * @param {boolean} visible - Whether the relay should be visible in UI
 */
function updateRelayVisibility(relayId, visible) {
    relays[relayId].visible = visible;
    updateRelayUI();
}

/**
 * Update relay override timeout
 * @param {string} relayId - Relay ID
 * @param {number} timeout - Timeout in seconds
 */
function updateRelayOverrideTimeout(relayId, timeout) {
    relays[relayId].overrideTimeout = parseInt(timeout);
}

/**
 * Update automation parameters
 * @param {Object} config - New automation configuration
 */
function updateAutomationConfig(config) {
    automationConfig = { ...automationConfig, ...config };
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
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
    // Check if we're on a page with relay controls
    if (document.querySelector('.relay-toggle')) {
        initRelays();
        
        // Set periodic status updates
        setInterval(updateRelayStatus, 5000);
    }
});

// Expose functions for use in other scripts
window.relays = {
    getRelays: () => relays,
    getAutomationConfig: () => automationConfig,
    toggleRelay,
    updateRelayName,
    updateRelayPin,
    updateRelaySchedule,
    updateRelayDependencies,
    updateRelayVisibility,
    updateRelayOverrideTimeout,
    updateAutomationConfig,
    saveRelayConfig
};