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
    
    // Add other event handlers for modals and buttons here
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
        url: '/api/relays/' + relayId,
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
    $('#humidity-start-time').val(data.humidity_schedule.start);
    $('#humidity-end-time').val(data.humidity_schedule.end);
    $('#fan-start-time').val(data.fan_schedule.start);
    $('#fan-end-time').val(data.fan_schedule.end);
    $('#light-start-time').val(data.light_schedule.start);
    $('#light-end-time').val(data.light_schedule.end);
    
    // Cycle timers
    $('#fan-on-duration').val(data.fan_cycle.duration);
    $('#fan-cycle-interval').val(data.fan_cycle.interval);
    $('#light-on-duration').val(data.light_cycle.duration);
    $('#light-cycle-interval').val(data.light_cycle.interval);
    
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