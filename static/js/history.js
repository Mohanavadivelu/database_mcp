/* Query History Management */

let queryHistory = JSON.parse(localStorage.getItem('queryHistory') || '[]');
let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');

// History management
function addToHistory(query) {
    const historyItem = {
        id: Date.now(),
        query: query,
        timestamp: new Date().toISOString(),
        favorite: false
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
        historyItem.className = `history-item ${item.favorite ? 'favorite' : ''}`;
        historyItem.innerHTML = `
            <div class="query-text">${item.query}</div>
            <div class="history-actions">
                <button onclick="toggleFavorite(${item.id})" title="${item.favorite ? 'Remove from favorites' : 'Add to favorites'}">
                    <i class="fas fa-star${item.favorite ? '' : '-o'}"></i>
                </button>
                <button onclick="rerunQuery('${item.query.replace(/'/g, "\\'")}'))" title="Run again">
                    <i class="fas fa-play"></i>
                </button>
                <button onclick="removeFromHistory(${item.id})" title="Remove">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div style="font-size: 0.7em; color: var(--text-secondary); margin-top: 3px;">
                ${new Date(item.timestamp).toLocaleString()}
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

function toggleFavorite(id) {
    const item = queryHistory.find(q => q.id === id);
    if (item) {
        item.favorite = !item.favorite;
        localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
        renderHistory();
    }
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
