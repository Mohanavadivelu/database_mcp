/* Query History Management */

let queryHistory = JSON.parse(localStorage.getItem('queryHistory') || '[]');

// History management
function addToHistory(query) {
    const historyItem = {
        id: Date.now(),
        query: query,
        timestamp: new Date().toISOString()
    };
    
    queryHistory.unshift(historyItem);
    if (queryHistory.length > 100) {
        queryHistory = queryHistory.slice(0, 100);
    }
    
    localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
    renderHistory();
}

function renderHistory() {
    historyList.innerHTML = '';
    
    if (queryHistory.length === 0) {
        historyList.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No queries yet</div>';
        return;
    }

    queryHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-content">
                <div class="query-text-full">${item.query}</div>
                <div class="history-timestamp">
                    ${new Date(item.timestamp).toLocaleString()}
                </div>
            </div>
            <div class="history-actions-top">
                <button onclick="rerunQuery('${item.query.replace(/'/g, "\\'")}'))" title="Load/Run Query" class="action-play">
                    <i class="fas fa-play"></i>
                </button>
                <button onclick="removeFromHistory(${item.id})" title="Delete Query" class="action-delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        historyItem.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                input.value = item.query;
                input.focus();
                if (window.innerWidth <= 768) {
                    sidebar.classList.add('closed');
                    updateSidebarButtonState();
                }
            }
        });
        
        historyList.appendChild(historyItem);
    });
}

function rerunQuery(query) {
    input.value = query;
    form.dispatchEvent(new Event('submit'));
    if (window.innerWidth <= 768) {
        sidebar.classList.add('closed');
        updateSidebarButtonState();
    }
}

function removeFromHistory(id) {
    queryHistory = queryHistory.filter(q => q.id !== id);
    localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
    renderHistory();
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all query history?')) {
        queryHistory = [];
        localStorage.removeItem('queryHistory');
        renderHistory();
    }
}
