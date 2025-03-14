/**
 * Mushroom Tent Controller - Main JavaScript
 * 
 * This file contains the core functionality for the frontend web interface.
 */

// Global variables
let temperatureChart;
let humidityChart;
let darkModeEnabled = false;
let graphUpdateInterval;
let graphMaxPoints;

// Initialize when document is ready
$(document).ready(function() {
    // Initialize dark/light mode
    initializeTheme();
    
    // Initialize charts
    initializeCharts();
    
    // Start fetching sensor data
    fetchSensorData();
    
    // Start fetching relay states
    fetchRelayStates();
    
    // Setup UI event handlers
    setupEventHandlers();
    
    // Load settings and apply them
    loadSettings();
});

// Initialize theme based on user preference
function initializeTheme() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        enableDarkMode();
    }
    
    // Theme toggle button handler
    $('#theme-toggle').click(function() {
        if (darkModeEnabled) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });
}

// Enable dark mode
function enableDarkMode() {
    $('body').attr('data-bs-theme', 'dark');
    $('#dark-mode-styles').removeAttr('disabled');
    darkModeEnabled = true;
    localStorage.setItem('theme', 'dark');
    
    // Update chart themes
    updateChartTheme();
}

// Disable dark mode
function disableDarkMode() {
    $('body').attr('data-bs-theme', 'light');
    $('#dark-mode-styles').attr('disabled', 'disabled');
    darkModeEnabled = false;
    localStorage.setItem('theme', 'light');
    
    // Update chart themes
    updateChartTheme();
}

// Initialize temperature and humidity charts
function initializeCharts() {
    const temperatureCtx = document.getElementById('temperatureChart').getContext('2d');
    const humidityCtx = document.getElementById('humidityChart').getContext('2d');
    
    // Common chart options
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 500
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                beginAtZero: false
            }
        },
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    // Create temperature chart
    temperatureChart = new Chart(temperatureCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upper DHT Temp',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Lower DHT Temp',
                    data: [],
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'SCD40 Temp',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.4
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                }
            }
        }
    });
    
    // Create humidity chart
    humidityChart = new Chart(humidityCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upper DHT Humidity',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Lower DHT Humidity',
                    data: [],
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'SCD40 Humidity',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.4
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Humidity (%)'
                    }
                }
            }
        }
    });
    
    // Update chart theme to match current mode
    updateChartTheme();
}

// Update chart theme based on current mode
function updateChartTheme() {
    const textColor = darkModeEnabled ? '#fff' : '#666';
    const gridColor = darkModeEnabled ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    const chartOptions = {
        scales: {
            x: {
                grid: {
                    color: gridColor
                },
                ticks: {
                    color: textColor
                }
            },
            y: {
                grid: {
                    color: gridColor
                },
                ticks: {
                    color: textColor
                },
                title: {
                    color: textColor
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: textColor
                }
            }
        }
    };
    
    // Apply to both charts
    temperatureChart.options.scales.x.grid.color = gridColor;
    temperatureChart.options.scales.x.ticks.color = textColor;
    temperatureChart.options.scales.y.grid.color = gridColor;
    temperatureChart.options.scales.y.ticks.color = textColor;
    temperatureChart.options.scales.y.title.color = textColor;
    temperatureChart.options.plugins.legend.labels.color = textColor;
    
    humidityChart.options.scales.x.grid.color = gridColor;
    humidityChart.options.scales.x.ticks.color = textColor;
    humidityChart.options.scales.y.grid.color = gridColor;
    humidityChart.options.scales.y.ticks.color = textColor;
    humidityChart.options.scales.y.title.color = textColor;
    humidityChart.options.plugins.legend.labels.color = textColor;
    
    // Update the charts
    temperatureChart.update();
    humidityChart.update();
}

// Fetch sensor data from API
function fetchSensorData() {
    $.ajax({
        url: '/api/sensors',
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Update dashboard displays
            updateSensorDisplays(data);
            
            // Add data to charts
            updateCharts(data);
            
            // Flash update indicators
            flashUpdateIndicators();
        },
        error: function(error) {
            console.error('Error fetching sensor data:', error);
        },
        complete: function() {
            // Schedule next update
            setTimeout(fetchSensorData, graphUpdateInterval || 60000);
        }
    });
}

// Update sensor displays on dashboard
function updateSensorDisplays(data) {
    // Update Upper DHT
    $('#upper-dht-temp').text(data.upper_dht.temperature.toFixed(1) + '°C');
    $('#upper-dht-humidity').text(data.upper_dht.humidity.toFixed(1) + '%');
    
    // Update Lower DHT
    $('#lower-dht-temp').text(data.lower_dht.temperature.toFixed(1) + '°C');
    $('#lower-dht-humidity').text(data.lower_dht.humidity.toFixed(1) + '%');
    
    // Update SCD40
    $('#scd40-temp').text(data.scd40.temperature.toFixed(1) + '°C');
    $('#scd40-humidity').text(data.scd40.humidity.toFixed(1) + '%');
    $('#scd40-co2').text(data.scd40.co2.toFixed(0) + ' ppm');
    
    // Apply color coding based on thresholds
    applyColorCoding(data);
}

// Apply color coding to sensor values
function applyColorCoding(data) {
    // Load thresholds from settings
    const tempLow = parseFloat($('#temperature-low-threshold').val() || 20);
    const tempHigh = parseFloat($('#temperature-high-threshold').val() || 24);
    const humLow = parseFloat($('#humidity-low-threshold').val() || 50);
    const humHigh = parseFloat($('#humidity-high-threshold').val() || 85);
    const co2Low = parseFloat($('#co2-low-threshold').val() || 1000);
    const co2High = parseFloat($('#co2-high-threshold').val() || 1600);
    
    // Helper function to apply color class based on value and thresholds
    function applyColorClass(element, value, low, high) {
        element.removeClass('text-danger text-success text-warning');
        
        if (value < low) {
            element.addClass('text-danger');  // Below minimum (red)
        } else if (value > high) {
            element.addClass('text-danger');  // Above maximum (red)
        } else if (value < low * 1.1 || value > high * 0.9) {
            element.addClass('text-warning'); // Near threshold (orange)
        } else {
            element.addClass('text-success'); // Ideal range (green)
        }
    }
    
    // Apply to temperature values
    applyColorClass($('#upper-dht-temp'), data.upper_dht.temperature, tempLow, tempHigh);
    applyColorClass($('#lower-dht-temp'), data.lower_dht.temperature, tempLow, tempHigh);
    applyColorClass($('#scd40-temp'), data.scd40.temperature, tempLow, tempHigh);
    
    // Apply to humidity values
    applyColorClass($('#upper-dht-humidity'), data.upper_dht.humidity, humLow, humHigh);
    applyColorClass($('#lower-dht-humidity'), data.lower_dht.humidity, humLow, humHigh);
    applyColorClass($('#scd40-humidity'), data.scd40.humidity, humLow, humHigh);
    
    // Apply to CO2 value
    applyColorClass($('#scd40-co2'), data.scd40.co2, co2Low, co2High);
}

// Update charts with new sensor data
function updateCharts(data) {
    // Format timestamp for x-axis
    const now = new Date();
    const timeLabel = now.getHours().toString().padStart(2, '0') + ':' + 
                      now.getMinutes().toString().padStart(2, '0') + ':' + 
                      now.getSeconds().toString().padStart(2, '0');
    
    // Add new data to temperature chart
    temperatureChart.data.labels.push(timeLabel);
    temperatureChart.data.datasets[0].data.push(data.upper_dht.temperature);
    temperatureChart.data.datasets[1].data.push(data.lower_dht.temperature);
    temperatureChart.data.datasets[2].data.push(data.scd40.temperature);
    
    // Add new data to humidity chart
    humidityChart.data.labels.push(timeLabel);
    humidityChart.data.datasets[0].data.push(data.upper_dht.humidity);
    humidityChart.data.datasets[1].data.push(data.lower_dht.humidity);
    humidityChart.data.datasets[2].data.push(data.scd40.humidity);
    
    // Limit data points
    const maxPoints = graphMaxPoints || 60;
    
    if (temperatureChart.data.labels.length > maxPoints) {
        temperatureChart.data.labels.shift();
        temperatureChart.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    if (humidityChart.data.labels.length > maxPoints) {
        humidityChart.data.labels.shift();
        humidityChart.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    // Update charts
    temperatureChart.update();
    humidityChart.update();
}

// Flash update indicators
function flashUpdateIndicators() {
    // Flash temperature graph indicator
    $('#temp-update-indicator').addClass('blink-orange');
    setTimeout(() => $('#temp-update-indicator').removeClass('blink-orange'), 1000);
    
    // Flash humidity graph indicator
    $('#humid-update-indicator').addClass('blink-cyan');
    setTimeout(() => $('#humid-update-indicator').removeClass('blink-cyan'), 1000);
    
    // Flash sensor indicators
    $('#upper-dht-indicator').addClass('blink');
    $('#lower-dht-indicator').addClass('blink');
    $('#scd40-indicator').addClass('blink');
    
    setTimeout(() => {
        $('#upper-dht-indicator').removeClass('blink');
        $('#lower-dht-indicator').removeClass('blink');
        $('#scd40-indicator').removeClass('blink');
    }, 1000);
}

// Fetch relay states from API
function fetchRelayStates() {
    $.ajax({
        url: '/api/relays',
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Update relay toggle states and indicators
            updateRelayControls(data);
        },
        error: function(error) {
            console.error('Error fetching relay states:', error);
        },
        complete: function() {
            // Schedule next update
            setTimeout(fetchRelayStates, 5000);
        }
    });
}

// Update relay toggle states and indicators
function updateRelayControls(data) {
    // Loop through each relay (2-7, excluding relay1 as it's not visible)
    for (let i = 2; i <= 7; i++) {
        const relayId = `relay${i}`;
        const relayData = data[relayId];
        
        if (relayData) {
            // Update toggle switch state without triggering change event
            $(`#${relayId}-toggle`).prop('checked', relayData.state);
            
            // Update status indicator
            const statusBadge = $(`#${relayId}-status`);
            if (relayData.state) {
                statusBadge.removeClass('bg-danger').addClass('bg-success').text('ON');
            } else {
                statusBadge.removeClass('bg-success').addClass('bg-danger').text('OFF');
            }
        }
    }
}

// Setup UI event handlers
function setupEventHandlers() {
    // Clear graphs button
    $('#clear-graphs').click(function() {
        clearGraphs();
    });
    
    // Relay toggle handlers
    for (let i = 2; i <= 7; i++) {
        $(`#relay${i}-toggle`).change(function() {
            const isChecked = $(this).prop('checked');
            toggleRelay(`relay${i}`, isChecked);
        });
    }
    
    // Profiles modal handlers
    $('#profile-load').click(loadSelectedProfile);
    $('#profile-save').click(saveSelectedProfile);
    $('#profile-rename').click(renameSelectedProfile);
    $('#profile-export').click(exportProfiles);
    $('#profile-import').click(function() {
        $('#profile-import-file').click();
    });
    $('#profile-import-file').change(importProfiles);
    
    // Settings handlers
    $('#save-settings').click(saveSettings);
    $('#test-sensors').click(testSensors);
    $('#test-relays').click(testRelays);
    $('#reboot-now').click(rebootSystem);
    $('#factory-reset').click(factoryReset);
    
    // Network handlers
    $('#wifi1-scan').click(function() { scanWifi(1); });
    $('#wifi2-scan').click(function() { scanWifi(2); });
    $('#wifi3-scan').click(function() { scanWifi(3); });
    $('#ip-static, #ip-dhcp').change(toggleStaticIPFields);
    $('#mqtt-enable').change(toggleMQTTFields);
    $('#save-network').click(saveNetworkSettings);
    
    // Toggle static IP fields visibility
    toggleStaticIPFields();
    
    // Toggle MQTT fields visibility
    toggleMQTTFields();
    
    // WiFi scan handlers
    $('#refresh-wifi-scan').click(refreshWifiScan);
    $('#save-wifi-selection').click(saveWifiSelection);
    
    // System handlers
    $('#upload-pkg').click(uploadUpdatePackage);
}

// Clear both graphs
function clearGraphs() {
    // Clear temperature chart
    temperatureChart.data.labels = [];
    temperatureChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    temperatureChart.update();
    
    // Clear humidity chart
    humidityChart.data.labels = [];
    humidityChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    humidityChart.update();
}

// Toggle relay state
function toggleRelay(relayId, state) {
    $.ajax({
        url: `/api/relays/${relayId}`,
        method: 'POST',
        data: JSON.stringify({ state: state, override: true }),
        contentType: 'application/json',
        success: function(response) {
            console.log(`Relay ${relayId} set to ${state ? 'ON' : 'OFF'}`);
            
            // Update UI based on response
            const statusBadge = $(`#${relayId}-status`);
            if (state) {
                statusBadge.removeClass('bg-danger').addClass('bg-success').text('ON');
            } else {
                statusBadge.removeClass('bg-success').addClass('bg-danger').text('OFF');
            }
        },
        error: function(error) {
            console.error(`Error setting relay ${relayId}:`, error);
            // Revert toggle to previous state
            $(`#${relayId}-toggle`).prop('checked', !state);
        }
    });
}

// Load settings from API
function loadSettings() {
    $.ajax({
        url: '/api/settings',
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Apply graph settings
            graphUpdateInterval = data.graph_update_interval * 1000;
            graphMaxPoints = data.graph_max_points;
            
            // Populate form fields in modals
            populateSettingsForm(data);
        },
        error: function(error) {
            console.error('Error loading settings:', error);
        }
    });
}

// Populate settings form fields
function populateSettingsForm(data) {
    // Graphs
    $('#graph-update-interval').val(data.graph_update_interval);
    $('#graph-max-points').val(data.graph_max_points);
    
    // Sensors
    $('#dht-sensor-interval').val(data.dht_sensor_interval);
    $('#scd40-sensor-interval').val(data.scd40_sensor_interval);
    
    // Thresholds
    $('#humidity-low-threshold').val(data.humidity_low_threshold);
    $('#humidity-high-threshold').val(data.humidity_high_threshold);
    $('#temperature-low-threshold').val(data.temperature_low_threshold);
    $('#temperature-high-threshold').val(data.temperature_high_threshold);
    $('#co2-low-threshold').val(data.co2_low_threshold);
    $('#co2-high-threshold').val(data.co2_high_threshold);
    
    // Schedules
    if (data.fan_schedule) {
        $('#fan-start-time').val(data.fan_schedule.start);
        $('#fan-end-time').val(data.fan_schedule.end);
    }
    
    if (data.light_schedule) {
        $('#light-start-time').val(data.light_schedule.start);
        $('#light-end-time').val(data.light_schedule.end);
    }
    
    // Cycle timers
    if (data.fan_cycle) {
        $('#fan-on-duration').val(data.fan_cycle.duration);
        $('#fan-cycle-interval').val(data.fan_cycle.interval);
    }
    
    if (data.light_cycle) {
        $('#light-on-duration').val(data.light_cycle.duration);
        $('#light-cycle-interval').val(data.light_cycle.interval);
    }
    
    // Logging
    $('#log-level').val(data.log_level);
    $('#log-max-size').val(data.log_max_size);
    $('#log-flush-interval').val(data.log_flush_interval);
    $('#log-remote-address').val(data.log_remote_address);
    $('#sensor-error-threshold').val(data.sensor_error_threshold);
    
    // Reboot schedule
    $('#reboot-day').val(data.reboot_day);
    $('#reboot-time').val(data.reboot_time);
    
    // Sleep mode
    $('#sleep-mode').val(data.sleep_mode);
    $('#sleep-start-time').val(data.sleep_start_time);
    $('#sleep-end-time').val(data.sleep_end_time);
}

// Save settings
function saveSettings() {
    const settings = {
        // System settings
        log_level: $('#log-level').val(),
        log_max_size: parseInt($('#log-max-size').val()),
        log_flush_interval: parseInt($('#log-flush-interval').val()),
        sensor_error_threshold: parseInt($('#sensor-error-threshold').val()),
        reboot_day: parseInt($('#reboot-day').val()),
        reboot_time: $('#reboot-time').val(),
        sleep_mode: $('#sleep-mode').val(),
        sleep_start_time: $('#sleep-start-time').val(),
        sleep_end_time: $('#sleep-end-time').val(),
        
        // Profile settings
        graph_update_interval: parseInt($('#graph-update-interval').val()),
        graph_max_points: parseInt($('#graph-max-points').val()),
        dht_sensor_interval: parseInt($('#dht-sensor-interval').val()),
        scd40_sensor_interval: parseInt($('#scd40-sensor-interval').val()),
        humidity_low_threshold: parseFloat($('#humidity-low-threshold').val()),
        humidity_high_threshold: parseFloat($('#humidity-high-threshold').val()),
        temperature_low_threshold: parseFloat($('#temperature-low-threshold').val()),
        temperature_high_threshold: parseFloat($('#temperature-high-threshold').val()),
        co2_low_threshold: parseFloat($('#co2-low-threshold').val()),
        co2_high_threshold: parseFloat($('#co2-high-threshold').val()),
        
        // Fan schedule and cycle
        fan_schedule: {
            start: $('#fan-start-time').val(),
            end: $('#fan-end-time').val()
        },
        fan_cycle: {
            duration: parseInt($('#fan-on-duration').val()),
            interval: parseInt($('#fan-cycle-interval').val())
        },
        
        // Light schedule and cycle
        light_schedule: {
            start: $('#light-start-time').val(),
            end: $('#light-end-time').val()
        },
        light_cycle: {
            duration: parseInt($('#light-on-duration').val()),
            interval: parseInt($('#light-cycle-interval').val())
        }
    };
    
    $.ajax({
        url: '/api/settings',
        method: 'POST',
        data: JSON.stringify(settings),
        contentType: 'application/json',
        success: function(response) {
            // Update graph settings
            graphUpdateInterval = settings.graph_update_interval * 1000;
            graphMaxPoints = settings.graph_max_points;
            
            // Show success message
            showAlert('Settings saved successfully', 'success');
            
            // Close modal
            $('#settingsModal').modal('hide');
        },
        error: function(error) {
            console.error('Error saving settings:', error);
            showAlert('Error saving settings', 'danger');
        }
    });
}

// Load selected profile
function loadSelectedProfile() {
    const profileName = $('#profile-select').val();
    
    $.ajax({
        url: `/api/profiles/active/${profileName}`,
        method: 'POST',
        success: function(response) {
            // Load profile settings
            $.ajax({
                url: `/api/profiles/${profileName}`,
                method: 'GET',
                dataType: 'json',
                success: function(data) {
                    // Apply settings to form
                    populateSettingsForm(data);
                    
                    // Show success message
                    showAlert(`Profile '${profileName}' loaded successfully`, 'success');
                },
                error: function(error) {
                    console.error(`Error loading profile '${profileName}':`, error);
                    showAlert(`Error loading profile '${profileName}'`, 'danger');
                }
            });
        },
        error: function(error) {
            console.error(`Error setting active profile '${profileName}':`, error);
            showAlert(`Error setting active profile '${profileName}'`, 'danger');
        }
    });
}

// Save selected profile
function saveSelectedProfile() {
    const profileName = $('#profile-select').val();
    
    // Collect profile data
    const profileData = {
        graph_update_interval: parseInt($('#graph-update-interval').val()),
        graph_max_points: parseInt($('#graph-max-points').val()),
        dht_sensor_interval: parseInt($('#dht-sensor-interval').val()),
        scd40_sensor_interval: parseInt($('#scd40-sensor-interval').val()),
        humidity_low_threshold: parseFloat($('#humidity-low-threshold').val()),
        humidity_high_threshold: parseFloat($('#humidity-high-threshold').val()),
        temperature_low_threshold: parseFloat($('#temperature-low-threshold').val()),
        temperature_high_threshold: parseFloat($('#temperature-high-threshold').val()),
        co2_low_threshold: parseFloat($('#co2-low-threshold').val()),
        co2_high_threshold: parseFloat($('#co2-high-threshold').val()),
        
        // Fan schedule and cycle
        fan_schedule: {
            start: $('#fan-start-time').val(),
            end: $('#fan-end-time').val()
        },
        fan_cycle: {
            duration: parseInt($('#fan-on-duration').val()),
            interval: parseInt($('#fan-cycle-interval').val())
        },
        
        // Light schedule and cycle
        light_schedule: {
            start: $('#light-start-time').val(),
            end: $('#light-end-time').val()
        },
        light_cycle: {
            duration: parseInt($('#light-on-duration').val()),
            interval: parseInt($('#light-cycle-interval').val())
        }
    };
    
    $.ajax({
        url: `/api/profiles/${profileName}`,
        method: 'POST',
        data: JSON.stringify(profileData),
        contentType: 'application/json',
        success: function(response) {
            // Set as active profile
            $.ajax({
                url: `/api/profiles/active/${profileName}`,
                method: 'POST',
                success: function() {
                    // Show success message
                    showAlert(`Profile '${profileName}' saved and activated`, 'success');
                },
                error: function(error) {
                    console.error(`Error activating profile '${profileName}':`, error);
                    showAlert(`Profile saved but could not be activated`, 'warning');
                }
            });
        },
        error: function(error) {
            console.error(`Error saving profile '${profileName}':`, error);
            showAlert(`Error saving profile '${profileName}'`, 'danger');
        }
    });
}

// Rename selected profile
function renameSelectedProfile() {
    const oldName = $('#profile-select').val();
    const newName = prompt(`Enter new name for profile '${oldName}':`);
    
    if (!newName) {
        return;
    }
    
    $.ajax({
        url: '/api/profiles/rename',
        method: 'POST',
        data: JSON.stringify({ old_name: oldName, new_name: newName }),
        contentType: 'application/json',
        success: function(response) {
            // Update profile dropdown
            const $profileSelect = $('#profile-select');
            $profileSelect.find(`option[value="${oldName}"]`).val(newName).text(newName);
            $profileSelect.val(newName);
            
            // Show success message
            showAlert(`Profile renamed from '${oldName}' to '${newName}'`, 'success');
        },
        error: function(error) {
            console.error(`Error renaming profile '${oldName}':`, error);
            showAlert(`Error renaming profile '${oldName}'`, 'danger');
        }
    });
}

// Export profiles
function exportProfiles() {
    window.location.href = '/api/profiles/export';
}

// Import profiles
function importProfiles(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    $.ajax({
        url: '/api/profiles/import',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // Refresh profile list
            $.ajax({
                url: '/api/profiles',
                method: 'GET',
                dataType: 'json',
                success: function(data) {
                    const $profileSelect = $('#profile-select');
                    $profileSelect.empty();
                    
                    data.profiles.forEach(profile => {
                        $profileSelect.append($('<option>', {
                            value: profile,
                            text: profile,
                            selected: profile === data.active
                        }));
                    });
                    
                    // Show success message
                    showAlert('Profiles imported successfully', 'success');
                },
                error: function(error) {
                    console.error('Error refreshing profiles:', error);
                }
            });
        },
        error: function(error) {
            console.error('Error importing profiles:', error);
            showAlert('Error importing profiles', 'danger');
        }
    });
    
    // Reset file input
    event.target.value = '';
}

// Test sensors
function testSensors() {
    $('#test-results').removeClass('d-none alert-success alert-danger').addClass('alert-info').html('Testing sensors...');
    
    $.ajax({
        url: '/api/sensors/test',
        method: 'POST',
        success: function(data) {
            let html = '<h5>Sensor Test Results:</h5><ul>';
            
            for (const [sensor, result] of Object.entries(data)) {
                const statusClass = result.status === 'passed' ? 'text-success' : 
                                   (result.status === 'warning' ? 'text-warning' : 'text-danger');
                
                html += `<li><strong>${sensor}:</strong> <span class="${statusClass}">${result.status}</span> - ${result.message}</li>`;
            }
            
            html += '</ul>';
            
            $('#test-results').removeClass('alert-info').addClass('alert-success').html(html);
        },
        error: function(error) {
            console.error('Error testing sensors:', error);
            $('#test-results').removeClass('alert-info').addClass('alert-danger')
                .html('Error testing sensors: ' + (error.responseJSON?.error || error.statusText));
        }
    });
}

// Test relays
function testRelays() {
    $('#test-results').removeClass('d-none alert-success alert-danger').addClass('alert-info').html('Testing relays...');
    
    $.ajax({
        url: '/api/relays/test',
        method: 'POST',
        success: function(data) {
            let html = '<h5>Relay Test Results:</h5><ul>';
            
            for (const [relay, result] of Object.entries(data)) {
                const statusClass = result.status === 'passed' ? 'text-success' : 'text-danger';
                
                html += `<li><strong>${relay}:</strong> <span class="${statusClass}">${result.status}</span> - ${result.message}</li>`;
            }
            
            html += '</ul>';
            
            $('#test-results').removeClass('alert-info').addClass('alert-success').html(html);
        },
        error: function(error) {
            console.error('Error testing relays:', error);
            $('#test-results').removeClass('alert-info').addClass('alert-danger')
                .html('Error testing relays: ' + (error.responseJSON?.error || error.statusText));
        }
    });
}

// Reboot system
function rebootSystem() {
    if (!confirm('Are you sure you want to reboot the system?')) {
        return;
    }
    
    $.ajax({
        url: '/api/system/reboot',
        method: 'POST',
        success: function(response) {
            showAlert('System is rebooting...', 'info');
            
            // Redirect to home page after a delay
            setTimeout(() => {
                window.location.href = '/';
            }, 5000);
        },
        error: function(error) {
            console.error('Error rebooting system:', error);
            showAlert('Error rebooting system', 'danger');
        }
    });
}

// Factory reset
function factoryReset() {
    if (!confirm('Are you sure you want to perform a factory reset? All settings will be lost!')) {
        return;
    }
    
    if (!confirm('This will erase ALL data and reset to factory defaults. This cannot be undone. Are you really sure?')) {
        return;
    }
    
    $.ajax({
        url: '/api/system/reset',
        method: 'POST',
        success: function(response) {
            showAlert('Factory reset in progress. System will reboot...', 'info');
            
            // Redirect to home page after a delay
            setTimeout(() => {
                window.location.href = '/';
            }, 5000);
        },
        error: function(error) {
            console.error('Error performing factory reset:', error);
            showAlert('Error performing factory reset', 'danger');
        }
    });
}

// Toggle static IP fields visibility
function toggleStaticIPFields() {
    if ($('#ip-static').prop('checked')) {
        $('#static-ip-fields').removeClass('d-none');
    } else {
        $('#static-ip-fields').addClass('d-none');
    }
}

// Toggle MQTT fields visibility
function toggleMQTTFields() {
    if ($('#mqtt-enable').prop('checked')) {
        $('#mqtt-fields').removeClass('d-none');
    } else {
        $('#mqtt-fields').addClass('d-none');
    }
}

// Scan WiFi networks
function scanWifi(index) {
    // Store target index
    $('#wifi-scan-target').text(`wifi${index}`);
    
    // Show WiFi scan modal
    $('#wifiScanModal').modal('show');
    
    // Refresh scan
    refreshWifiScan();
}

// Refresh WiFi scan
function refreshWifiScan() {
    $('#wifi-networks-list').html('<tr><td colspan="4" class="text-center">Scanning...</td></tr>');
    $('#save-wifi-selection').prop('disabled', true);
    
    $.ajax({
        url: '/api/network/scan',
        method: 'GET',
        dataType: 'json',
        success: function(networks) {
            const $list = $('#wifi-networks-list');
            $list.empty();
            
            if (networks.length === 0) {
                $list.html('<tr><td colspan="4" class="text-center">No networks found</td></tr>');
                return;
            }
            
            networks.forEach(network => {
                const signalStrength = network.rssi > -60 ? 'Strong' : (network.rssi > -75 ? 'Medium' : 'Weak');
                
                const $row = $('<tr>');
                $row.append($('<td>').text(network.ssid));
                $row.append($('<td>').text(signalStrength + ` (${network.rssi} dBm)`));
                $row.append($('<td>').text(network.security));
                $row.append($('<td>').text(network.mac));
                
                $row.data('network', network);
                $row.css('cursor', 'pointer');
                
                $row.click(function() {
                    // Highlight selected row
                    $list.find('tr').removeClass('table-primary');
                    $(this).addClass('table-primary');
                    
                    // Show password field if network has security
                    const network = $(this).data('network');
                    
                    $('#selected-ssid').text(network.ssid);
                    
                    if (network.security === 'Yes') {
                        $('#wifi-password-form').removeClass('d-none');
                    } else {
                        $('#wifi-password-form').addClass('d-none');
                    }
                    
                    // Enable save button
                    $('#save-wifi-selection').prop('disabled', false);
                });
                
                $list.append($row);
            });
        },
        error: function(error) {
            console.error('Error scanning WiFi networks:', error);
            $('#wifi-networks-list').html('<tr><td colspan="4" class="text-center text-danger">Error scanning networks</td></tr>');
        }
    });
}

// Save WiFi selection
function saveWifiSelection() {
    const targetIndex = $('#wifi-scan-target').text().slice(-1);
    const selectedRow = $('#wifi-networks-list tr.table-primary');
    
    if (selectedRow.length === 0) {
        return;
    }
    
    const network = selectedRow.data('network');
    const password = $('#wifi-password').val();
    
    $.ajax({
        url: '/api/network/wifi',
        method: 'POST',
        data: JSON.stringify({
            index: parseInt(targetIndex),
            ssid: network.ssid,
            password: password
        }),
        contentType: 'application/json',
        success: function(response) {
            // Update SSID field
            $(`#wifi${targetIndex}-ssid`).val(network.ssid);
            
            // Close modal
            $('#wifiScanModal').modal('hide');
            
            // Reset password field
            $('#wifi-password').val('');
            
            // Show success message
            showAlert(`WiFi network '${network.ssid}' saved to slot ${targetIndex}`, 'success');
        },
        error: function(error) {
            console.error('Error saving WiFi selection:', error);
            showAlert('Error saving WiFi selection', 'danger');
        }
    });
}

// Save network settings
function saveNetworkSettings() {
    // Collect network settings
    const networkSettings = {
        // Hostname
        hostname: $('#mdns-hostname').val(),
        
        // Static IP
        static_ip: {
            use_static: $('#ip-static').prop('checked'),
            ip: $('#static-ip').val(),
            netmask: $('#static-netmask').val(),
            gateway: $('#static-gateway').val(),
            dns1: $('#static-dns1').val(),
            dns2: $('#static-dns2').val()
        },
        
        // WiFi watchdog
        wifi_watchdog: {
            min_rssi: parseInt($('#wifi-min-rssi').val()),
            check_interval: parseInt($('#wifi-check-interval').val())
        },
        
        // MQTT
        mqtt: {
            enabled: $('#mqtt-enable').prop('checked'),
            broker: $('#mqtt-broker').val(),
            port: parseInt($('#mqtt-port').val()),
            username: $('#mqtt-username').val(),
            password: $('#mqtt-password').val(),
            topic: $('#mqtt-topic').val()
        }
    };
    
    // Save hostname
    $.ajax({
        url: '/api/network/hostname',
        method: 'POST',
        data: JSON.stringify({ hostname: networkSettings.hostname }),
        contentType: 'application/json',
        success: function() {
            // Save static IP
            $.ajax({
                url: '/api/network/static_ip',
                method: 'POST',
                data: JSON.stringify({
                    use_static: networkSettings.static_ip.use_static,
                    ip: networkSettings.static_ip.ip,
                    netmask: networkSettings.static_ip.netmask,
                    gateway: networkSettings.static_ip.gateway,
                    dns1: networkSettings.static_ip.dns1,
                    dns2: networkSettings.static_ip.dns2
                }),
                contentType: 'application/json',
                success: function() {
                    // Save WiFi watchdog
                    $.ajax({
                        url: '/api/network/watchdog',
                        method: 'POST',
                        data: JSON.stringify({
                            min_rssi: networkSettings.wifi_watchdog.min_rssi,
                            check_interval: networkSettings.wifi_watchdog.check_interval
                        }),
                        contentType: 'application/json',
                        success: function() {
                            // Save MQTT
                            $.ajax({
                                url: '/api/network/mqtt',
                                method: 'POST',
                                data: JSON.stringify({
                                    enabled: networkSettings.mqtt.enabled,
                                    broker: networkSettings.mqtt.broker,
                                    port: networkSettings.mqtt.port,
                                    username: networkSettings.mqtt.username,
                                    password: networkSettings.mqtt.password,
                                    topic: networkSettings.mqtt.topic
                                }),
                                contentType: 'application/json',
                                success: function() {
                                    // Show success message
                                    showAlert('Network settings saved successfully', 'success');
                                    
                                    // Close modal
                                    $('#networkModal').modal('hide');
                                },
                                error: function(error) {
                                    console.error('Error saving MQTT settings:', error);
                                    showAlert('Error saving MQTT settings', 'danger');
                                }
                            });
                        },
                        error: function(error) {
                            console.error('Error saving WiFi watchdog settings:', error);
                            showAlert('Error saving WiFi watchdog settings', 'danger');
                        }
                    });
                },
                error: function(error) {
                    console.error('Error saving static IP settings:', error);
                    showAlert('Error saving static IP settings', 'danger');
                }
            });
        },
        error: function(error) {
            console.error('Error saving hostname:', error);
            showAlert('Error saving hostname', 'danger');
        }
    });
}

// Upload update package
function uploadUpdatePackage() {
    const fileInput = document.getElementById('update-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select an update package file', 'warning');
        return;
    }
    
    if (!file.name.endsWith('.zip')) {
        showAlert('Update package must be a ZIP file', 'warning');
        return;
    }
    
    // Show progress
    $('#update-progress').removeClass('d-none');
    $('#update-status').text('Uploading update package...');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('restart', $('#update-restart').prop('checked'));
    
    // Upload file
    $.ajax({
        url: '/api/ota/upload',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    $('#update-progress .progress-bar').css('width', percent + '%').text(percent + '%');
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            $('#update-status').text('Update package uploaded. Installing...');
            
            // Start polling for update status
            pollUpdateStatus();
        },
        error: function(error) {
            console.error('Error uploading update package:', error);
            $('#update-status').text('Error uploading update package: ' + (error.responseJSON?.error || error.statusText));
            $('#update-progress .progress-bar').addClass('bg-danger');
        }
    });
}

// Poll update status
function pollUpdateStatus() {
    $.ajax({
        url: '/api/ota/status',
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Update progress
            $('#update-progress .progress-bar').css('width', data.progress + '%').text(data.progress + '%');
            
            // Update status message
            $('#update-status').text(data.message);
            
            // Check if update is complete
            if (data.in_progress) {
                // Continue polling
                setTimeout(pollUpdateStatus, 1000);
            } else {
                // Update complete
                if (data.success) {
                    $('#update-progress .progress-bar').removeClass('bg-danger').addClass('bg-success');
                    $('#update-status').text('Update completed successfully. System will reboot shortly.');
                    
                    // Reset file input
                    $('#update-file').val('');
                } else {
                    $('#update-progress .progress-bar').removeClass('bg-success').addClass('bg-danger');
                    $('#update-status').text('Update failed: ' + data.error);
                }
            }
        },
        error: function(error) {
            console.error('Error polling update status:', error);
            $('#update-status').text('Error checking update status');
            $('#update-progress .progress-bar').addClass('bg-danger');
        }
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    // Create alert element if it doesn't exist
    if ($('#alert-container').length === 0) {
        $('body').append('<div id="alert-container" style="position: fixed; top: 20px; right: 20px; z-index: 9999;"></div>');
    }
    
    // Create alert
    const alertId = 'alert-' + Date.now();
    const $alert = $(`
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    
    // Add to container
    $('#alert-container').append($alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $alert.alert('close');
    }, 5000);
}