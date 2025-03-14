/**
 * Mushroom Tent Controller - System Page JavaScript
 */

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
    
    // Show progress and status
    $('#update-progress').removeClass('d-none');
    $('#update-progress .progress-bar').css('width', '0%').text('0%').removeClass('bg-success bg-danger');
    $('#update-status').removeClass('d-none alert-success alert-danger').addClass('alert-info').text('Uploading update package...');
    
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
            $('#update-status').removeClass('alert-info').addClass('alert-danger');
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
                    $('#update-status').removeClass('alert-info alert-danger').addClass('alert-success');
                    $('#update-status').text('Update completed successfully. System will reboot shortly.');
                    
                    // Reset file input
                    $('#update-file').val('');
                } else {
                    $('#update-progress .progress-bar').removeClass('bg-success').addClass('bg-danger');
                    $('#update-status').removeClass('alert-info alert-success').addClass('alert-danger');
                    $('#update-status').text('Update failed: ' + data.error);
                }
            }
        },
        error: function(error) {
            console.error('Error polling update status:', error);
            $('#update-status').removeClass('alert-info alert-success').addClass('alert-danger');
            $('#update-status').text('Error checking update status');
            $('#update-progress .progress-bar').addClass('bg-danger');
        }
    });
}

// Refresh logs
function refreshLogs() {
    // Get filter parameters
    const level = $('#log-level-filter').val();
    const component = $('#log-component-filter').val();
    const limit = $('#log-limit').val();
    
    let url = `/api/logs?limit=${limit}`;
    if (level) url += `&level=${level}`;
    if (component) url += `&component=${component}`;
    
    $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Clear existing logs
            $('#log-entries').empty();
            
            // Add new logs
            if (data.length === 0) {
                $('#log-entries').html('<tr><td colspan="4" class="text-center">No logs found</td></tr>');
            } else {
                // Populate component filter if needed
                populateComponentFilter(data);
                
                // Add log entries
                data.forEach(log => {
                    const rowClass = log.level === 'ERROR' ? 'table-danger' : 
                                     (log.level === 'WARNING' ? 'table-warning' : '');
                    
                    $('#log-entries').append(`
                        <tr class="${rowClass}">
                            <td>${log.datetime}</td>
                            <td>${log.level}</td>
                            <td>${log.component}</td>
                            <td>${log.message}</td>
                        </tr>
                    `);
                });
                
                // Scroll to bottom
                const container = document.getElementById('log-container');
                container.scrollTop = container.scrollHeight;
            }
        },
        error: function(error) {
            console.error('Error fetching logs:', error);
            $('#log-entries').html('<tr><td colspan="4" class="text-center text-danger">Error fetching logs</td></tr>');
        }
    });
}

// Populate component filter
function populateComponentFilter(logs) {
    // Only populate if empty
    if ($('#log-component-filter option').length <= 1) {
        const components = new Set();
        
        logs.forEach(log => {
            components.add(log.component);
        });
        
        // Sort components
        const sortedComponents = Array.from(components).sort();
        
        // Add options
        sortedComponents.forEach(component => {
            $('#log-component-filter').append(`<option value="${component}">${component}</option>`);
        });
    }
}

// Clear logs
function clearLogs() {
    if (!confirm('Are you sure you want to clear all logs?')) {
        return;
    }
    
    $.ajax({
        url: '/api/logs/clear',
        method: 'POST',
        success: function() {
            // Refresh logs
            refreshLogs();
            
            // Show success message
            showAlert('Logs cleared successfully', 'success');
        },
        error: function(error) {
            console.error('Error clearing logs:', error);
            showAlert('Error clearing logs', 'danger');
        }
    });
}

// Document ready
$(document).ready(function() {
    // Set up event handlers
    $('#upload-pkg').click(uploadUpdatePackage);
    $('#refresh-logs').click(refreshLogs);
    $('#clear-logs').click(clearLogs);
    $('#apply-log-filter').click(refreshLogs);
    
    // Initial log load
    refreshLogs();
    
    // Poll system info every 5 seconds
    setInterval(function() {
        $.ajax({
            url: '/api/system/status',
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                updateSystemInfo(data);
            },
            error: function(error) {
                console.error('Error fetching system info:', error);
            }
        });
    }, 5000);
    
    // Poll OTA status if in progress
    setInterval(function() {
        if ($('#update-progress').hasClass('d-none')) {
            return;
        }
        
        $.ajax({
            url: '/api/ota/status',
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                // Only update if in progress
                if (data.in_progress) {
                    $('#update-progress .progress-bar').css('width', data.progress + '%').text(data.progress + '%');
                    $('#update-status').text(data.message);
                }
            }
        });
    }, 2000);
});

// Update system information
function updateSystemInfo(data) {
    // Update network info
    if (data.network) {
        $('#system-ip').text(data.network.ip || '--');
        $('#system-ssid').text(data.network.ssid || '--');
        $('#system-mac').text(data.network.mac || '--');
        $('#system-rssi').text(data.network.rssi ? data.network.rssi + ' dBm' : '--');
    }
    
    // Update uptime
    $('#system-uptime').text(data.uptime || '--');
    
    // Update RAM usage
    if (data.memory) {
        const ramPercent = data.memory.percent;
        $('#ram-usage').css('width', ramPercent + '%').text(ramPercent + '%');
        $('#ram-details').text(
            `${data.memory.used.toFixed(1)} MB used / ` +
            `${data.memory.free.toFixed(1)} MB free / ` +
            `${data.memory.total.toFixed(1)} MB total`
        );
        
        // Set color based on usage
        $('#ram-usage').removeClass('bg-success bg-warning bg-danger');
        if (ramPercent < 60) {
            $('#ram-usage').addClass('bg-success');
        } else if (ramPercent < 85) {
            $('#ram-usage').addClass('bg-warning');
        } else {
            $('#ram-usage').addClass('bg-danger');
        }
    }
    
    // Update disk usage
    if (data.disk) {
        const diskPercent = data.disk.percent;
        $('#disk-usage').css('width', diskPercent + '%').text(diskPercent + '%');
        $('#disk-details').text(
            `${data.disk.used.toFixed(1)} MB used / ` +
            `${data.disk.free.toFixed(1)} MB free / ` +
            `${data.disk.total.toFixed(1)} MB total`
        );
        
        // Set color based on usage
        $('#disk-usage').removeClass('bg-success bg-warning bg-danger');
        if (diskPercent < 60) {
            $('#disk-usage').addClass('bg-success');
        } else if (diskPercent < 85) {
            $('#disk-usage').addClass('bg-warning');
        } else {
            $('#disk-usage').addClass('bg-danger');
        }
    }
    
    // Update CPU info
    if (data.cpu) {
        const cpuPercent = data.cpu.percent;
        $('#cpu-usage').css('width', cpuPercent + '%').text(cpuPercent + '%');
        $('#cpu-frequency').text(data.cpu.frequency ? data.cpu.frequency.toFixed(1) + ' MHz' : '--');
        $('#cpu-temperature').text(data.cpu.temperature ? data.cpu.temperature.toFixed(1) + '°C' : '--');
        
        // Set color based on usage
        $('#cpu-usage').removeClass('bg-success bg-warning bg-danger');
        if (cpuPercent < 60) {
            $('#cpu-usage').addClass('bg-success');
        } else if (cpuPercent < 85) {
            $('#cpu-usage').addClass('bg-warning');
        } else {
            $('#cpu-usage').addClass('bg-danger');
        }
    }
}