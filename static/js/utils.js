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
