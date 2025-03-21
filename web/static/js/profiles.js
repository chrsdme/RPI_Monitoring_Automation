/**
 * profiles.js
 * Handles profile management for the Mushroom Tent Controller
 */

// Global variables
let profiles = {
    active: 'Test',
    list: ['Test', 'Colonisation', 'Fruiting'],
    data: {
        'Test': {
            graph: {
                updateInterval: 10,  // seconds
                maxPoints: 100
            },
            sensors: {
                dhtInterval: 30,     // seconds
                scdInterval: 60      // seconds
            },
            relays: {
                humidity: {
                    lowThreshold: 50,
                    highThreshold: 85,
                    startTime: "00:00",
                    endTime: "23:59"
                },
                temperature: {
                    lowThreshold: 20,
                    highThreshold: 24
                },
                fans: {
                    co2LowThreshold: 1100,
                    co2HighThreshold: 1600,
                    onDuration: 10,      // minutes
                    cycleInterval: 60,   // minutes
                    startTime: "00:00",
                    endTime: "23:59"
                },
                lights: {
                    cycleTime: 12,       // hours
                    uvStartTime: "08:00",
                    uvEndTime: "20:00",
                    growStartTime: "08:00",
                    growEndTime: "20:00"
                }
            }
        },
        'Colonisation': {
            // Default colonisation profile
            graph: {
                updateInterval: 10,
                maxPoints: 100
            },
            sensors: {
                dhtInterval: 30,
                scdInterval: 60
            },
            relays: {
                humidity: {
                    lowThreshold: 65,
                    highThreshold: 90,
                    startTime: "00:00",
                    endTime: "23:59"
                },
                temperature: {
                    lowThreshold: 23,
                    highThreshold: 26
                },
                fans: {
                    co2LowThreshold: 1300,
                    co2HighThreshold: 1800,
                    onDuration: 5,
                    cycleInterval: 120,
                    startTime: "00:00",
                    endTime: "23:59"
                },
                lights: {
                    cycleTime: 0,
                    uvStartTime: "00:00",
                    uvEndTime: "00:00",
                    growStartTime: "00:00",
                    growEndTime: "00:00"
                }
            }
        },
        'Fruiting': {
            // Default fruiting profile
            graph: {
                updateInterval: 10,
                maxPoints: 100
            },
            sensors: {
                dhtInterval: 30,
                scdInterval: 60
            },
            relays: {
                humidity: {
                    lowThreshold: 80,
                    highThreshold: 95,
                    startTime: "00:00",
                    endTime: "23:59"
                },
                temperature: {
                    lowThreshold: 18,
                    highThreshold: 22
                },
                fans: {
                    co2LowThreshold: 800,
                    co2HighThreshold: 1200,
                    onDuration: 15,
                    cycleInterval: 60,
                    startTime: "00:00",
                    endTime: "23:59"
                },
                lights: {
                    cycleTime: 12,
                    uvStartTime: "08:00",
                    uvEndTime: "20:00",
                    growStartTime: "08:00",
                    growEndTime: "20:00"
                }
            }
        }
    }
};

/**
 * Initialize profiles
 */
function initProfiles() {
    console.log("Initializing profiles system...");
    
    // Fetch profiles from server
    fetchProfiles();
    
    // Set up UI elements
    setupProfilesUI();
}

/**
 * Fetch profiles from server
 */
function fetchProfiles() {
    fetch('/api/profiles')
        .then(response => response.json())
        .then(data => {
            console.log("Profiles loaded:", data);
            
            // Update profiles
            profiles = data;
            
            // Update the UI to reflect loaded profiles
            updateProfilesUI();
        })
        .catch(error => {
            console.error("Error loading profiles:", error);
        });
}

/**
 * Set up profiles UI elements
 */
function setupProfilesUI() {
    // Get DOM elements
    const profileSelector = document.getElementById('profile-selector');
    const loadButton = document.getElementById('profile-load-btn');
    const saveButton = document.getElementById('profile-save-btn');
    const renameButton = document.getElementById('profile-rename-btn');
    const exportButton = document.getElementById('profile-export-btn');
    const importButton = document.getElementById('profile-import-btn');
    
    // Set up profile selector
    if (profileSelector) {
        profileSelector.addEventListener('change', function() {
            // Nothing happens until load is clicked
        });
    }
    
    // Set up load button
    if (loadButton) {
        loadButton.addEventListener('click', function() {
            const selectedProfile = profileSelector.value;
            loadProfile(selectedProfile);
        });
    }
    
    // Set up save button
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const selectedProfile = profileSelector.value;
            saveProfile(selectedProfile);
        });
    }
    
    // Set up rename button
    if (renameButton) {
        renameButton.addEventListener('click', function() {
            const selectedProfile = profileSelector.value;
            const newName = prompt('Enter new profile name:', selectedProfile);
            
            if (newName && newName !== selectedProfile) {
                renameProfile(selectedProfile, newName);
            }
        });
    }
    
    // Set up export button
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            exportProfiles();
        });
    }
    
    // Set up import button
    if (importButton) {
        importButton.addEventListener('click', function() {
            // Create file input element
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.json';
            
            fileInput.addEventListener('change', function(event) {
                const file = event.target.files[0];
                if (file) {
                    importProfiles(file);
                }
            });
            
            // Trigger click to open file dialog
            fileInput.click();
        });
    }
}

/**
 * Update profiles UI elements to reflect current data
 */
function updateProfilesUI() {
    // Get DOM elements
    const profileSelector = document.getElementById('profile-selector');
    
    // Update profile selector
    if (profileSelector) {
        // Clear existing options
        profileSelector.innerHTML = '';
        
        // Add options for each profile
        profiles.list.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile;
            option.textContent = profile;
            
            // Select active profile
            if (profile === profiles.active) {
                option.selected = true;
            }
            
            profileSelector.appendChild(option);
        });
    }
    
    // Update form fields with active profile data
    updateFormFields();
}

/**
 * Update form fields with data from the active profile
 */
function updateFormFields() {
    const activeProfile = profiles.active;
    const profileData = profiles.data[activeProfile];
    
    if (!profileData) {
        console.error(`Profile data for ${activeProfile} not found`);
        return;
    }
    
    // Update Graph section
    if (profileData.graph) {
        const updateIntervalField = document.getElementById('graph-update-interval');
        const maxPointsField = document.getElementById('graph-max-points');
        
        if (updateIntervalField) {
            updateIntervalField.value = profileData.graph.updateInterval;
        }
        
        if (maxPointsField) {
            maxPointsField.value = profileData.graph.maxPoints;
        }
    }
    
    // Update Sensors section
    if (profileData.sensors) {
        const dhtIntervalField = document.getElementById('dht-sensor-interval');
        const scdIntervalField = document.getElementById('scd-sensor-interval');
        
        if (dhtIntervalField) {
            dhtIntervalField.value = profileData.sensors.dhtInterval;
        }
        
        if (scdIntervalField) {
            scdIntervalField.value = profileData.sensors.scdInterval;
        }
    }
    
    // Update Humidity section
    if (profileData.relays && profileData.relays.humidity) {
        const humidityLowField = document.getElementById('humidity-low-threshold');
        const humidityHighField = document.getElementById('humidity-high-threshold');
        const humidityStartField = document.getElementById('humidity-start-time');
        const humidityEndField = document.getElementById('humidity-end-time');
        
        if (humidityLowField) {
            humidityLowField.value = profileData.relays.humidity.lowThreshold;
        }
        
        if (humidityHighField) {
            humidityHighField.value = profileData.relays.humidity.highThreshold;
        }
        
        if (humidityStartField) {
            humidityStartField.value = profileData.relays.humidity.startTime;
        }
        
        if (humidityEndField) {
            humidityEndField.value = profileData.relays.humidity.endTime;
        }
    }
    
    // Update Temperature section
    if (profileData.relays && profileData.relays.temperature) {
        const tempLowField = document.getElementById('temperature-low-threshold');
        const tempHighField = document.getElementById('temperature-high-threshold');
        
        if (tempLowField) {
            tempLowField.value = profileData.relays.temperature.lowThreshold;
        }
        
        if (tempHighField) {
            tempHighField.value = profileData.relays.temperature.highThreshold;
        }
    }
    
    // Update Fans section
    if (profileData.relays && profileData.relays.fans) {
        const co2LowField = document.getElementById('co2-low-threshold');
        const co2HighField = document.getElementById('co2-high-threshold');
        const onDurationField = document.getElementById('fans-on-duration');
        const cycleIntervalField = document.getElementById('fans-cycle-interval');
        const fansStartField = document.getElementById('fans-start-time');
        const fansEndField = document.getElementById('fans-end-time');
        
        if (co2LowField) {
            co2LowField.value = profileData.relays.fans.co2LowThreshold;
        }
        
        if (co2HighField) {
            co2HighField.value = profileData.relays.fans.co2HighThreshold;
        }
        
        if (onDurationField) {
            onDurationField.value = profileData.relays.fans.onDuration;
        }
        
        if (cycleIntervalField) {
            cycleIntervalField.value = profileData.relays.fans.cycleInterval;
        }
        
        if (fansStartField) {
            fansStartField.value = profileData.relays.fans.startTime;
        }
        
        if (fansEndField) {
            fansEndField.value = profileData.relays.fans.endTime;
        }
    }
    
    // Update Lights section if needed
    if (profileData.relays && profileData.relays.lights) {
        // Add fields for lights configuration if present in UI
    }
}

/**
 * Gather form data into profile
 * @returns {Object} Profile data from form
 */
function gatherFormData() {
    const formData = {
        graph: {
            updateInterval: parseInt(document.getElementById('graph-update-interval').value),
            maxPoints: parseInt(document.getElementById('graph-max-points').value)
        },
        sensors: {
            dhtInterval: parseInt(document.getElementById('dht-sensor-interval').value),
            scdInterval: parseInt(document.getElementById('scd-sensor-interval').value)
        },
        relays: {
            humidity: {
                lowThreshold: parseInt(document.getElementById('humidity-low-threshold').value),
                highThreshold: parseInt(document.getElementById('humidity-high-threshold').value),
                startTime: document.getElementById('humidity-start-time').value,
                endTime: document.getElementById('humidity-end-time').value
            },
            temperature: {
                lowThreshold: parseInt(document.getElementById('temperature-low-threshold').value),
                highThreshold: parseInt(document.getElementById('temperature-high-threshold').value)
            },
            fans: {
                co2LowThreshold: parseInt(document.getElementById('co2-low-threshold').value),
                co2HighThreshold: parseInt(document.getElementById('co2-high-threshold').value),
                onDuration: parseInt(document.getElementById('fans-on-duration').value),
                cycleInterval: parseInt(document.getElementById('fans-cycle-interval').value),
                startTime: document.getElementById('fans-start-time').value,
                endTime: document.getElementById('fans-end-time').value
            }
        }
    };
    
    // Add lights section if needed
    
    return formData;
}

/**
 * Load profile data into form
 * @param {string} profileName - Name of profile to load
 */
function loadProfile(profileName) {
    console.log(`Loading profile: ${profileName}`);
    
    if (!profiles.data[profileName]) {
        console.error(`Profile ${profileName} not found`);
        showNotification(`Profile ${profileName} not found`, 'error');
        return;
    }
    
    // Set active profile
    profiles.active = profileName;
    
    // Update the form with profile data
    updateFormFields();
    
    // Apply the profile to the system
    applyProfile(profileName);
}

/**
 * Apply profile to the system
 * @param {string} profileName - Name of profile to apply
 */
function applyProfile(profileName) {
    console.log(`Applying profile: ${profileName}`);
    
    // Send request to server to apply profile
    fetch(`/api/profiles/${profileName}/apply`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification(`Profile "${profileName}" applied successfully`, 'success');
            
            // Update local sensors and relays configurations
            if (window.sensors) {
                const profileData = profiles.data[profileName];
                
                // Update sensor intervals
                window.sensors.updateSensorIntervals(
                    profileData.sensors.dhtInterval,
                    profileData.sensors.scdInterval
                );
                
                // Update chart configuration
                window.sensors.updateChartConfig(
                    profileData.graph.maxPoints,
                    profileData.graph.updateInterval
                );
                
                // Update thresholds
                window.sensors.updateThresholds({
                    temperature: {
                        low: profileData.relays.temperature.lowThreshold,
                        high: profileData.relays.temperature.highThreshold
                    },
                    humidity: {
                        low: profileData.relays.humidity.lowThreshold,
                        high: profileData.relays.humidity.highThreshold
                    },
                    co2: {
                        low: profileData.relays.fans.co2LowThreshold,
                        high: profileData.relays.fans.co2HighThreshold
                    }
                });
            }
            
            // Update relay configuration if that module is available
            if (window.relays) {
                const profileData = profiles.data[profileName];
                
                window.relays.updateAutomationConfig({
                    humidifier: {
                        lowThreshold: profileData.relays.humidity.lowThreshold,
                        highThreshold: profileData.relays.humidity.highThreshold
                    },
                    heater: {
                        lowThreshold: profileData.relays.temperature.lowThreshold,
                        highThreshold: profileData.relays.temperature.highThreshold
                    },
                    co2: {
                        lowThreshold: profileData.relays.fans.co2LowThreshold,
                        highThreshold: profileData.relays.fans.co2HighThreshold
                    },
                    fans: {
                        onDuration: profileData.relays.fans.onDuration,
                        cycleInterval: profileData.relays.fans.cycleInterval
                    }
                });
            }
        } else {
            showNotification(`Failed to apply profile: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error applying profile:", error);
        showNotification('Error applying profile', 'error');
    });
}

/**
 * Save form data to profile
 * @param {string} profileName - Name of profile to save
 */
function saveProfile(profileName) {
    console.log(`Saving profile: ${profileName}`);
    
    // Gather form data
    const formData = gatherFormData();
    
    // Update local profiles data
    profiles.data[profileName] = formData;
    
    // Update server
    fetch(`/api/profiles/${profileName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(result => {
        console.log("Save profile result:", result);
        
        if (result.success) {
            showNotification(`Profile "${profileName}" saved successfully`, 'success');
            
            // Apply the profile
            applyProfile(profileName);
        } else {
            showNotification(`Failed to save profile: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error("Error saving profile:", error);
        showNotification('Error saving profile', 'error');
    });
}

/**
 * Rename a profile
 * @param {string} oldName - Current profile name
 * @param {string} newName - New profile name
 */
function renameProfile(oldName, newName) {
    console.log(`Renaming profile from "${oldName}" to "${newName}"`);
    
    // Check if new name already exists
    if (profiles.list.includes(newName)) {
        showNotification(`Profile "${newName}" already exists`, 'error');
        return;
    }
    
    // Update local data
    // Copy profile data
    profiles.data[newName] = { ...profiles.data[oldName] };
    
    // Remove old profile
    delete profiles.data[oldName];
    
    // Update list
    const index = profiles.list.indexOf(oldName);
    if (index !== -1) {
        profiles.list[index] = newName;
    }
    
    // Update active profile if needed
    if (profiles.active === oldName) {
        profiles.active = newName;
    }
    
    // Update server
    fetch(`/api/profiles/${oldName}/rename`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ newName })
    })
    .then(response => response.json())
    .then(result => {
        console.log("Rename profile result:", result);
        
        if (result.success) {
            showNotification(`Profile renamed to "${newName}" successfully`, 'success');
            
            // Update UI
            updateProfilesUI();
        } else {
            // Revert local changes
            profiles.data[oldName] = profiles.data[newName];
            delete profiles.data[newName];
            
            const index = profiles.list.indexOf(newName);
            if (index !== -1) {
                profiles.list[index] = oldName;
            }
            
            if (profiles.active === newName) {
                profiles.active = oldName;
            }
            
            showNotification(`Failed to rename profile: ${result.message}`, 'error');
            updateProfilesUI();
        }
    })
    .catch(error => {
        console.error("Error renaming profile:", error);
        
        // Revert local changes
        profiles.data[oldName] = profiles.data[newName];
        delete profiles.data[newName];
        
        const index = profiles.list.indexOf(newName);
        if (index !== -1) {
            profiles.list[index] = oldName;
        }
        
        if (profiles.active === newName) {
            profiles.active = oldName;
        }
        
        showNotification('Error renaming profile', 'error');
        updateProfilesUI();
    });
}

/**
 * Export all profiles to JSON file
 */
function exportProfiles() {
    console.log("Exporting all profiles");
    
    // Create JSON string
    const json = JSON.stringify(profiles, null, 2);
    
    // Create blob
    const blob = new Blob([json], { type: 'application/json' });
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', 'mushroom-controller-profiles.json');
    a.click();
}

/**
 * Import profiles from JSON file
 * @param {File} file - File object from input
 */
function importProfiles(file) {
    console.log("Importing profiles from file:", file.name);
    
    // Read file
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            // Parse JSON
            const importedProfiles = JSON.parse(e.target.result);
            
            // Validate data structure
            if (!importedProfiles.list || !importedProfiles.data) {
                throw new Error('Invalid profile data structure');
            }
            
            // Update server with imported profiles
            fetch('/api/profiles/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(importedProfiles)
            })
            .then(response => response.json())
            .then(result => {
                console.log("Import profiles result:", result);
                
                if (result.success) {
                    // Update local data
                    profiles = importedProfiles;
                    
                    showNotification('Profiles imported successfully', 'success');
                    
                    // Update UI
                    updateProfilesUI();
                    
                    // Apply first profile
                    const firstProfile = importedProfiles.list[0];
                    if (firstProfile) {
                        applyProfile(firstProfile);
                    }
                } else {
                    showNotification(`Failed to import profiles: ${result.message}`, 'error');
                }
            })
            .catch(error => {
                console.error("Error importing profiles to server:", error);
                showNotification('Error importing profiles to server', 'error');
            });
            
        } catch (error) {
            console.error("Error parsing profile file:", error);
            showNotification('Invalid profile file format', 'error');
        }
    };
    
    reader.onerror = function() {
        console.error("Error reading profile file");
        showNotification('Error reading profile file', 'error');
    };
    
    reader.readAsText(file);
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
    // Check if we're on a page with the profiles modal
    if (document.getElementById('profile-selector')) {
        initProfiles();
    }
});

// Expose functions for use in other scripts
window.profiles = {
    getProfiles: () => profiles,
    getActiveProfile: () => profiles.data[profiles.active],
    loadProfile,
    saveProfile,
    renameProfile,
    exportProfiles,
    importProfiles
};