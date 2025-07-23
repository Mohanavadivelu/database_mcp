/* Main Application Logic and Initialization */

let currentTheme = localStorage.getItem('theme') || 'dark';
let isLoading = false;

// Get references to HTML elements
const consoleDiv = document.getElementById('console');
const form = document.getElementById('input-form');
const input = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');
const sidebar = document.getElementById('sidebar');
const historyList = document.getElementById('history-list');
const themeText = document.getElementById('theme-text');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    applyTheme(currentTheme);
    renderHistory();
    updateSidebarButtonState();
    
    // On mobile, start with sidebar closed
    if (window.innerWidth <= 768) {
        sidebar.classList.add('closed');
        updateSidebarButtonState();
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && !sidebar.classList.contains('closed')) {
            if (!sidebar.contains(e.target) && !e.target.closest('.sidebar-toggle')) {
                sidebar.classList.add('closed');
                updateSidebarButtonState();
            }
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            // On desktop, always show sidebar
            sidebar.classList.remove('closed');
        } else {
            // On mobile, start closed if not already set
            if (!sidebar.classList.contains('closed')) {
                sidebar.classList.add('closed');
            }
        }
        updateSidebarButtonState();
    });
});

/**
 * Handles the form submission event.
 */
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question || isLoading) return;

    addLog(question, 'prompt');
    addToHistory(question);
    input.value = '';

    const command = question.toLowerCase();

    // Handle built-in commands
    if (command === 'help') {
        const helpText =
            "🤖 MCP Natural Language Console Help\n\n" +
            "📊 Query Examples:\n" +
            "  • How many hours did alice spend on photoshop?\n" +
            "  • Show me all usage from bob\n" +
            "  • What was the longest session in seconds?\n" +
            "  • List all users on the windows platform\n" +
            "  • What legacy apps were used?\n\n" +
            "🔧 Built-in Commands:\n" +
            "  • help: Show this help message\n" +
            "  • clear: Clear the console screen\n\n" +
            "💡 Features:\n" +
            "  • Click History button to view past queries\n" +
            "  • Toggle between light/dark themes\n" +
            "  • Export chart data as PNG, CSV, or JSON\n" +
            "  • Star queries to save as favorites";
        addLog(helpText, 'response');
    } else if (command === 'clear') {
        clearConsole();
    } else {
        await performLlmQuery(question);
    }
});

// Theme toggle functionality
function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(currentTheme);
    localStorage.setItem('theme', currentTheme);
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    const icon = document.querySelector('.theme-toggle i');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
        themeText.textContent = 'Light';
    } else {
        icon.className = 'fas fa-moon';
        themeText.textContent = 'Dark';
    }
}

// Sidebar functionality
function toggleSidebar() {
    sidebar.classList.toggle('closed');
    updateSidebarButtonState();
    
    // On mobile, close when clicking a history item
    if (window.innerWidth <= 768 && !sidebar.classList.contains('closed')) {
        // Auto-close after a delay if on mobile
        setTimeout(() => {
            if (window.innerWidth <= 768) {
                sidebar.classList.add('closed');
                updateSidebarButtonState();
            }
        }, 5000);
    }
}

function updateSidebarButtonState() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const isOpen = !sidebar.classList.contains('closed');
    
    if (isOpen) {
        sidebarToggle.classList.add('active');
        sidebarToggle.innerHTML = '<i class="fas fa-history"></i> Hide History';
    } else {
        sidebarToggle.classList.remove('active');
        sidebarToggle.innerHTML = '<i class="fas fa-history"></i> Show History';
    }
}

/**
 * Sends the user's question to the backend and displays the answer with enhanced UX.
 * @param {string} question - The user's natural language question.
 */
async function performLlmQuery(question) {
    if (isLoading) return;
    
    isLoading = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    const loadingIndicator = showLoadingIndicator();
    const chartContainer = document.getElementById('chart-container');
    
    try {
        const response = await fetch('/api/llm_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        });

        const data = await response.json();
        hideLoadingIndicator();

        if (response.ok) {
            // Store the data for export functionality
            lastQueryData = {
                question: question,
                answer: data.answer,
                data: data.data,
                timestamp: new Date().toISOString()
            };
            
            // Display the answer with action buttons
            addLog(data.answer, 'response', true);

            // Render chart if data is available
            if (data.data && data.data.length > 0) {
                try {
                    renderChart(data.data, data.question);
                    chartContainer.classList.remove('hidden');
                } catch (chartError) {
                    console.error("Error rendering chart:", chartError);
                    addLog(`⚠️ Chart rendering failed: ${chartError.message}`, 'error');
                    chartContainer.classList.add('hidden');
                }
            } else {
                chartContainer.classList.add('hidden');
            }

        } else {
            // Handle API errors
            const errorMessage = data.answer || data.error || 'Unknown server error';
            addLog(`🚨 Server Error: ${errorMessage}`, 'error');
            chartContainer.classList.add('hidden');
        }

    } catch (error) {
        hideLoadingIndicator();
        // Handle network errors
        addLog(`🔌 Connection Error: ${error.message}\n\nPlease check your internet connection and try again.`, 'error');
        chartContainer.classList.add('hidden');
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
        scrollToBottom();
    }
}
