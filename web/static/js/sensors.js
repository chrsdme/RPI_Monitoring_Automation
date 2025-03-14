/**
 * sensors.js
 * Handles all sensor data acquisition, processing, and visualization
 * For the Mushroom Tent Controller
 */

// Global variables
let tempChart, humidityChart;
let tempUpdateIndicator, humidityUpdateIndicator;
let sensorData = {
    upperDHT: { temperature: 0, humidity: 0 },
    lowerDHT: { temperature: 0, humidity: 0 },
    scd40: { temperature: 0, humidity: 0, co2: 0 }
};
let sensorUpdateTimers = {
    upperDHT: null,
    lowerDHT: null,
    scd40: null
};
let chartUpdateTimer = null;
let sensorReadings = [];
let maxDataPoints = 100; // Default, can be changed in settings

// Temperature & Humidity thresholds for display coloring
let thresholds = {
    temperature: {
        low: 18,
        high: 26
    },
    humidity: {
        low: 50,
        high: 85
    },
    co2: {
        low: 1000,
        high: 1600
    }
};

/**
 * Initialize sensor systems
 */
function initSensors() {
    console.log("Initializing sensor systems...");
    
    // Get configuration
    fetchSensorConfig();
    
    // Initialize sensor update indicators
    initSensorIndicators();
    
    // Initialize charts
    initCharts();
    
    // Start data collection
    startSensorDataCollection();
}

/**
 * Fetch sensor configuration from the server
 */
function fetchSensorConfig() {
    fetch('/api/config/sensors')
        .then(response => response.json())
        .then(config => {
            console.log("Sensor configuration loaded:", config);
            
            // Update thresholds
            thresholds = config.thresholds;
            
            // Update chart configuration
            maxDataPoints = config.graphMaxPoints;
            
            // Update sensor reading intervals
            updateSensorIntervals(config.dhtInterval, config.scdInterval);
            
            // Update chart refresh interval
            updateChartInterval(config.graphUpdateInterval);
        })
        .catch(error => {
            console.error("Error loading sensor configuration:", error);
        });
}

/**
 * Initialize the blinking indicators for sensor updates
 */
function initSensorIndicators() {
    // Get DOM elements for indicators
    tempUpdateIndicator = document.getElementById('temp-update-indicator');
    humidityUpdateIndicator = document.getElementById('humidity-update-indicator');
    
    // Get sensor reading indicators
    document.querySelectorAll('.sensor-indicator').forEach(indicator => {
        // Store references if needed
    });
}

/**
 * Initialize temperature and humidity charts
 */
function initCharts() {
    const tempCtx = document.getElementById('temperature-chart').getContext('2d');
    const humidityCtx = document.getElementById('humidity-chart').getContext('2d');
    
    // Create temperature chart
    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upper DHT',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Lower DHT',
                    data: [],
                    borderColor: 'rgba(153, 102, 255, 1)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'SCD40',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    tension: 0.1,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Temperature (°C)'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    },
                    suggestedMin: 15,
                    suggestedMax: 30
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
                    label: 'Upper DHT',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Lower DHT',
                    data: [],
                    borderColor: 'rgba(153, 102, 255, 1)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'SCD40',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    tension: 0.1,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Humidity (%)'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Humidity (%)'
                    },
                    suggestedMin: 40,
                    suggestedMax: 100
                }
            }
        }
    });
}

/**
 * Start sensor data collection at configured intervals
 */
function startSensorDataCollection() {
    // Initial data fetch
    fetchSensorData();
    
    // Set up recurring update for chart data
    chartUpdateTimer = setInterval(updateCharts, 5000); // Default 5s, will be updated from config
}

/**
 * Update sensor reading intervals
 * @param {number} dhtInterval - Interval in seconds for DHT sensors
 * @param {number} scdInterval - Interval in seconds for SCD40 sensor
 */
function updateSensorIntervals(dhtInterval, scdInterval) {
    // Clear existing timers
    if (sensorUpdateTimers.upperDHT) clearInterval(sensorUpdateTimers.upperDHT);
    if (sensorUpdateTimers.lowerDHT) clearInterval(sensorUpdateTimers.lowerDHT);
    if (sensorUpdateTimers.scd40) clearInterval(sensorUpdateTimers.scd40);
    
    // Set new timers
    const dhtMs = dhtInterval * 1000;
    const scdMs = scdInterval * 1000;
    
    sensorUpdateTimers.upperDHT = setInterval(() => fetchSensorData('upperDHT'), dhtMs);
    sensorUpdateTimers.lowerDHT = setInterval(() => fetchSensorData('lowerDHT'), dhtMs);
    sensorUpdateTimers.scd40 = setInterval(() => fetchSensorData('scd40'), scdMs);
}

/**
 * Update chart refresh interval
 * @param {number} interval - Interval in seconds
 */
function updateChartInterval(interval) {
    if (chartUpdateTimer) clearInterval(chartUpdateTimer);
    chartUpdateTimer = setInterval(updateCharts, interval * 1000);
}

/**
 * Fetch sensor data from the API
 * @param {string} [sensorType] - Optional sensor type to fetch specific data
 */
function fetchSensorData(sensorType = null) {
    let endpoint = '/api/sensors';
    if (sensorType) {
        endpoint += `/${sensorType}`;
    }
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            console.log("Sensor data received:", data);
            
            // Store the data
            if (data.upperDHT) sensorData.upperDHT = data.upperDHT;
            if (data.lowerDHT) sensorData.lowerDHT = data.lowerDHT;
            if (data.scd40) sensorData.scd40 = data.scd40;
            
            // Flash indicators
            if (sensorType === 'upperDHT' || sensorType === null) {
                flashSensorIndicator('upper-dht-indicator');
            }
            if (sensorType === 'lowerDHT' || sensorType === null) {
                flashSensorIndicator('lower-dht-indicator');
            }
            if (sensorType === 'scd40' || sensorType === null) {
                flashSensorIndicator('scd40-indicator');
            }
            
            // Update display values
            updateSensorDisplays();
            
            // Add to historical data for charts
            addDataPoint(data);
        })
        .catch(error => {
            console.error("Error fetching sensor data:", error);
        });
}

/**
 * Flash sensor indicator to show data update
 * @param {string} indicatorId - DOM ID of the indicator element
 */
function flashSensorIndicator(indicatorId) {
    const indicator = document.getElementById(indicatorId);
    if (!indicator) return;
    
    // Add active class
    indicator.classList.add('active');
    
    // Remove after 500ms
    setTimeout(() => {
        indicator.classList.remove('active');
    }, 500);
}

/**
 * Update sensor displays with latest values
 */
function updateSensorDisplays() {
    // Update Upper DHT display
    updateSensorDisplay(
        'upper-dht-temp', 
        sensorData.upperDHT.temperature, 
        '°C',
        getColorForValue(sensorData.upperDHT.temperature, thresholds.temperature)
    );
    updateSensorDisplay(
        'upper-dht-humidity', 
        sensorData.upperDHT.humidity, 
        '%',
        getColorForValue(sensorData.upperDHT.humidity, thresholds.humidity)
    );
    
    // Update Lower DHT display
    updateSensorDisplay(
        'lower-dht-temp', 
        sensorData.lowerDHT.temperature, 
        '°C',
        getColorForValue(sensorData.lowerDHT.temperature, thresholds.temperature)
    );
    updateSensorDisplay(
        'lower-dht-humidity', 
        sensorData.lowerDHT.humidity, 
        '%',
        getColorForValue(sensorData.lowerDHT.humidity, thresholds.humidity)
    );
    
    // Update SCD40 display
    updateSensorDisplay(
        'scd40-temp', 
        sensorData.scd40.temperature, 
        '°C',
        getColorForValue(sensorData.scd40.temperature, thresholds.temperature)
    );
    updateSensorDisplay(
        'scd40-humidity', 
        sensorData.scd40.humidity, 
        '%',
        getColorForValue(sensorData.scd40.humidity, thresholds.humidity)
    );
    updateSensorDisplay(
        'scd40-co2', 
        sensorData.scd40.co2, 
        'ppm',
        getColorForValue(sensorData.scd40.co2, thresholds.co2)
    );
}

/**
 * Update a specific sensor display element
 * @param {string} elementId - DOM ID of the display element
 * @param {number} value - The value to display
 * @param {string} unit - The unit of measurement
 * @param {string} color - Text color based on thresholds
 */
function updateSensorDisplay(elementId, value, unit, color) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Format the value to 1 decimal place if it's a float
    let displayValue = value;
    if (typeof value === 'number' && !Number.isInteger(value)) {
        displayValue = value.toFixed(1);
    }
    
    // Update the text and color
    element.textContent = `${displayValue} ${unit}`;
    element.style.color = color;
}

/**
 * Determine color based on value and thresholds
 * @param {number} value - The sensor value
 * @param {Object} threshold - Threshold object with low and high properties
 * @returns {string} - CSS color string
 */
function getColorForValue(value, threshold) {
    if (value < threshold.low) {
        return 'red';  // Below minimum
    } else if (value > threshold.high) {
        return 'red';  // Above maximum
    } else if (value >= threshold.low && value <= threshold.low + ((threshold.high - threshold.low) * 0.2)) {
        return 'orange';  // Just above minimum
    } else if (value <= threshold.high && value >= threshold.high - ((threshold.high - threshold.low) * 0.2)) {
        return 'orange';  // Just below maximum
    } else {
        return 'green';  // Ideal range
    }
}

/**
 * Add a data point to the historical data for charts
 * @param {Object} data - Sensor data object
 */
function addDataPoint(data) {
    // Create timestamp
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Create data point
    const dataPoint = {
        time: timeString,
        upperDHT: { ...data.upperDHT },
        lowerDHT: { ...data.lowerDHT },
        scd40: { ...data.scd40 }
    };
    
    // Add to array
    sensorReadings.push(dataPoint);
    
    // Limit array size
    if (sensorReadings.length > maxDataPoints) {
        sensorReadings.shift();
    }
}

/**
 * Update charts with latest data
 */
function updateCharts() {
    // Flash chart update indicators
    flashChartIndicators();
    
    // Don't update if we don't have data
    if (sensorReadings.length === 0) return;
    
    // Prepare data for charts
    const labels = sensorReadings.map(reading => reading.time);
    
    // Update temperature chart
    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = sensorReadings.map(reading => reading.upperDHT.temperature);
    tempChart.data.datasets[1].data = sensorReadings.map(reading => reading.lowerDHT.temperature);
    tempChart.data.datasets[2].data = sensorReadings.map(reading => reading.scd40.temperature);
    tempChart.update();
    
    // Update humidity chart
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = sensorReadings.map(reading => reading.upperDHT.humidity);
    humidityChart.data.datasets[1].data = sensorReadings.map(reading => reading.lowerDHT.humidity);
    humidityChart.data.datasets[2].data = sensorReadings.map(reading => reading.scd40.humidity);
    humidityChart.update();
}

/**
 * Flash chart update indicators to show data update
 */
function flashChartIndicators() {
    if (tempUpdateIndicator) {
        tempUpdateIndicator.classList.add('active');
        setTimeout(() => {
            tempUpdateIndicator.classList.remove('active');
        }, 500);
    }
    
    if (humidityUpdateIndicator) {
        humidityUpdateIndicator.classList.add('active');
        setTimeout(() => {
            humidityUpdateIndicator.classList.remove('active');
        }, 500);
    }
}

/**
 * Clear all chart data
 */
function clearChartData() {
    // Clear the data array
    sensorReadings = [];
    
    // Update charts
    tempChart.data.labels = [];
    tempChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    tempChart.update();
    
    humidityChart.data.labels = [];
    humidityChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    humidityChart.update();
    
    console.log("Chart data cleared");
}

/**
 * Export sensor data as CSV
 */
function exportSensorData() {
    // Don't export if we don't have data
    if (sensorReadings.length === 0) {
        alert("No sensor data available to export");
        return;
    }
    
    // Create CSV header
    let csv = 'Time,UpperDHT-Temp,UpperDHT-Humidity,LowerDHT-Temp,LowerDHT-Humidity,SCD40-Temp,SCD40-Humidity,SCD40-CO2\n';
    
    // Add data rows
    sensorReadings.forEach(reading => {
        csv += `${reading.time},` +
               `${reading.upperDHT.temperature},${reading.upperDHT.humidity},` +
               `${reading.lowerDHT.temperature},${reading.lowerDHT.humidity},` +
               `${reading.scd40.temperature},${reading.scd40.humidity},${reading.scd40.co2}\n`;
    });
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', `sensor-data-${new Date().toISOString().slice(0,10)}.csv`);
    a.click();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sensors when on index page
    if (document.getElementById('temperature-chart') && document.getElementById('humidity-chart')) {
        initSensors();
        
        // Add event listener for clear button if it exists
        const clearButton = document.getElementById('clear-graphs-btn');
        if (clearButton) {
            clearButton.addEventListener('click', clearChartData);
        }
    }
});

// Expose functions for use in other scripts
window.sensors = {
    clearChartData,
    exportSensorData,
    updateThresholds: (newThresholds) => {
        thresholds = newThresholds;
        updateSensorDisplays();
    },
    updateChartConfig: (maxPoints, updateInterval) => {
        maxDataPoints = maxPoints;
        updateChartInterval(updateInterval);
    },
    updateSensorIntervals,
    fetchLatestData: fetchSensorData
};