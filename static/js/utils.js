/* Utility Functions and Helpers */

/**
 * Automatically scrolls the console to the bottom.
 */
function scrollToBottom() {
    setTimeout(() => { // Use a timeout to ensure DOM update is complete
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }, 100);
}

/**
 * Copy text to clipboard functionality.
 */
function copyToClipboard(button) {
    const logEntry = button.closest('.log-entry');
    const text = logEntry.textContent.replace(/CopyShare$/, '').trim();
    navigator.clipboard.writeText(text).then(() => {
        const originalIcon = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            button.innerHTML = originalIcon;
        }, 1000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

/**
 * Share response functionality.
 */
function shareResponse(button) {
    const logEntry = button.closest('.log-entry');
    const text = logEntry.textContent.replace(/CopyShare$/, '').trim();
    if (navigator.share) {
        navigator.share({
            title: 'MCP Query Result',
            text: text
        });
    } else {
        copyToClipboard(button);
    }
}

/**
 * Adds a new message to the console log with enhanced features.
 * @param {string} message - The text to display.
 * @param {string} type - The class name for styling ('prompt', 'response', or 'error').
 * @param {boolean} withActions - Whether to add action buttons.
 * @returns {HTMLElement} The new log element created.
 */
function addLog(message, type, withActions = false) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type} fade-in ${withActions ? 'with-actions' : ''}`;
    logEntry.textContent = message;
    
    if (withActions && type === 'response') {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'log-actions';
        actionsDiv.innerHTML = `
            <button onclick="copyToClipboard(this)" title="Copy to clipboard">
                <i class="fas fa-copy"></i>
            </button>
            <button onclick="shareResponse(this)" title="Share">
                <i class="fas fa-share"></i>
            </button>
        `;
        logEntry.appendChild(actionsDiv);
    }
    
    consoleDiv.appendChild(logEntry);
    scrollToBottom();
    return logEntry;
}

/**
 * Adds a response with an embedded chart to the chat.
 * @param {string} message - The text response.
 * @param {Array} data - The data for chart rendering.
 * @param {string} question - The original question for chart context.
 * @returns {HTMLElement} The new log element created.
 */
function addLogWithChart(message, data, question) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry response fade-in with-actions';
    
    // Create message content
    const messageDiv = document.createElement('div');
    messageDiv.textContent = message;
    logEntry.appendChild(messageDiv);
    
    // Create chart container if data is available
    if (data && data.length > 0) {
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chat-chart-container';
        
        // Create chart actions
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'chat-chart-actions';
        actionsDiv.innerHTML = `
            <button onclick="exportChatChart(this)" title="Export Chart as PNG">
                <i class="fas fa-download"></i> PNG
            </button>
            <button onclick="exportChatData(this, 'csv')" title="Export Data as CSV">
                <i class="fas fa-file-csv"></i> CSV
            </button>
            <button onclick="exportChatData(this, 'json')" title="Export Data as JSON">
                <i class="fas fa-file-code"></i> JSON
            </button>
        `;
        chartContainer.appendChild(actionsDiv);
        
        // Create canvas for chart
        const canvas = document.createElement('canvas');
        canvas.id = `chat-chart-${Date.now()}`;
        canvas.width = 800;
        canvas.height = 400;
        canvas.style.width = '100%';
        canvas.style.height = '350px';
        chartContainer.appendChild(canvas);
        
        logEntry.appendChild(chartContainer);
        
        // Store data for export functionality
        logEntry.dataset.chartData = JSON.stringify(data);
        logEntry.dataset.question = question;
        
        // Render chart after DOM insertion
        consoleDiv.appendChild(logEntry);
        renderChatChart(canvas, data, question);
    } else {
        consoleDiv.appendChild(logEntry);
    }
    
    // Add response actions
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'log-actions';
    actionsDiv.innerHTML = `
        <button onclick="copyToClipboard(this)" title="Copy to clipboard">
            <i class="fas fa-copy"></i>
        </button>
        <button onclick="shareResponse(this)" title="Share">
            <i class="fas fa-share"></i>
        </button>
    `;
    logEntry.appendChild(actionsDiv);
    
    scrollToBottom();
    return logEntry;
}

/**
 * Creates and shows a loading indicator.
 */
function showLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator fade-in';
    loadingDiv.innerHTML = `
        <div class="spinner"></div>
        <span>Processing your query...</span>
    `;
    loadingDiv.id = 'loading-indicator';
    consoleDiv.appendChild(loadingDiv);
    scrollToBottom();
    return loadingDiv;
}

/**
 * Removes the loading indicator.
 */
function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function clearConsole() {
    consoleDiv.innerHTML = '';
    document.getElementById('chart-container').classList.add('hidden');
    // Clear all chat chart instances
    if (typeof chatChartInstances !== 'undefined') {
        chatChartInstances.forEach(chart => chart.destroy());
        chatChartInstances.clear();
    }
}

/**
 * Export chart from chat message as PNG.
 */
function exportChatChart(button) {
    const logEntry = button.closest('.log-entry');
    const canvas = logEntry.querySelector('canvas');
    if (!canvas) {
        addLog('❌ No chart available to export', 'error');
        return;
    }
    
    try {
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `chat-chart-${Date.now()}.png`;
        link.href = url;
        link.click();
        
        addLog('✅ Chart exported successfully', 'response');
    } catch (error) {
        addLog(`❌ Export failed: ${error.message}`, 'error');
    }
}

/**
 * Export data from chat message.
 */
function exportChatData(button, format) {
    const logEntry = button.closest('.log-entry');
    const data = JSON.parse(logEntry.dataset.chartData || '[]');
    const question = logEntry.dataset.question || '';
    
    if (!data || data.length === 0) {
        addLog('❌ No data available to export', 'error');
        return;
    }
    
    try {
        let content, filename, mimeType;
        
        if (format === 'csv') {
            content = convertToCSV(data);
            filename = `chat-data-${Date.now()}.csv`;
            mimeType = 'text/csv';
        } else if (format === 'json') {
            content = JSON.stringify({
                query: question,
                timestamp: new Date().toISOString(),
                results: data
            }, null, 2);
            filename = `chat-data-${Date.now()}.json`;
            mimeType = 'application/json';
        }
        
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
        
        addLog(`✅ Data exported as ${format.toUpperCase()} successfully`, 'response');
    } catch (error) {
        addLog(`❌ Export failed: ${error.message}`, 'error');
    }
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                // Escape quotes and wrap in quotes if contains comma or quote
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',')
        )
    ].join('\n');
    
    return csvContent;
}
