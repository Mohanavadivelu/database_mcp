/* Chart Rendering and Export Functionality */

let myChartInstance = null;
let lastQueryData = null;

// Export functionality
function exportChart(format) {
    if (!myChartInstance) {
        addLog('❌ No chart available to export', 'error');
        return;
    }
    
    try {
        const canvas = myChartInstance.canvas;
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `chart-${Date.now()}.png`;
        link.href = url;
        link.click();
        
        addLog('✅ Chart exported successfully', 'response');
    } catch (error) {
        addLog(`❌ Export failed: ${error.message}`, 'error');
    }
}

function exportData(format) {
    if (!lastQueryData || !lastQueryData.data) {
        addLog('❌ No data available to export', 'error');
        return;
    }
    
    try {
        let content, filename, mimeType;
        
        if (format === 'csv') {
            content = convertToCSV(lastQueryData.data);
            filename = `query-results-${Date.now()}.csv`;
            mimeType = 'text/csv';
        } else if (format === 'json') {
            content = JSON.stringify({
                query: lastQueryData.question,
                timestamp: lastQueryData.timestamp,
                results: lastQueryData.data
            }, null, 2);
            filename = `query-results-${Date.now()}.json`;
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

/**
 * Renders a chart based on the provided data and inferred chart type.
 * @param {Array<Object>} data - The raw data from the database.
 * @param {string} question - The original user question.
 */
function renderChart(data, question) {
    // Destroy existing chart if it exists
    if (myChartInstance) {
        myChartInstance.destroy();
    }

    const ctx = document.getElementById('myChart').getContext('2d');
    let chartConfig;

    // Simple heuristics to determine chart type based on data structure and question
    const keys = Object.keys(data[0]);
    const isAggregation = keys.includes('result') && keys.length === 2; // e.g., user, result or app, result

    if (isAggregation) {
        // Bar chart for aggregates like counts or sums per category
        const labels = data.map(item => Object.values(item)[0]); // First key is category (user, app, etc.)
        const values = data.map(item => item.result);

        chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Result',
                    data: values,
                    backgroundColor: '#569cd6',
                    borderColor: '#333',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: question || 'Query Result',
                        color: '#d4d4d4'
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#d4d4d4' },
                        grid: { color: '#333' }
                    },
                    y: {
                        ticks: { color: '#d4d4d4' },
                        grid: { color: '#333' }
                    }
                }
            }
        };
    } else if (keys.includes('log_date') && keys.includes('duration_seconds')) {
        // Line chart for time-series data
        // This would require more sophisticated grouping/aggregation in JS if not already done by SQL
        // For simplicity, let's just show a basic bar for now, or adapt if the SQL gives daily aggregation
         const labels = data.map(item => new Date(item.log_date).toLocaleDateString());
         const values = data.map(item => item.duration_seconds);

         chartConfig = {
             type: 'line', // Line chart for time series
             data: {
                 labels: labels,
                 datasets: [{
                     label: 'Duration (seconds)',
                     data: values,
                     borderColor: '#6a9955',
                     backgroundColor: 'rgba(106, 153, 85, 0.2)',
                     borderWidth: 2,
                     fill: true,
                     tension: 0.1
                 }]
             },
             options: {
                 responsive: true,
                 maintainAspectRatio: false,
                 plugins: {
                     legend: {
                         display: true,
                         labels: { color: '#d4d4d4' }
                     },
                     title: {
                         display: true,
                         text: question || 'Query Result',
                         color: '#d4d4d4'
                     }
                 },
                 scales: {
                     x: {
                         ticks: { color: '#d4d4d4' },
                         grid: { color: '#333' }
                     },
                     y: {
                         ticks: { color: '#d4d4d4' },
                         grid: { color: '#333' }
                     }
                 }
             }
         };

    } else {
        // Default to a table or general bar chart if no specific pattern
        console.warn("Could not infer specific chart type. Displaying raw data as text.");
        // Optionally display the raw data in a more readable format if no chart
        document.getElementById('chart-container').style.display = 'none';
        addLog('Raw Data (click to inspect in console):', 'response');
        addLog(JSON.stringify(data, null, 2), 'response');
        return; // Do not create a chart instance
    }

    myChartInstance = new Chart(ctx, chartConfig);
}
