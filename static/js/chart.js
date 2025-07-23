/* Chart Rendering and Export Functionality */

let myChartInstance = null;
let lastQueryData = null;
let chatChartInstances = new Map(); // Store multiple chat chart instances

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

/**
 * Renders a chart within a chat message bubble.
 * @param {HTMLCanvasElement} canvas - The canvas element within the chat message.
 * @param {Array<Object>} data - The raw data from the database.
 * @param {string} question - The original user question.
 */
function renderChatChart(canvas, data, question) {
    const ctx = canvas.getContext('2d');
    let chartConfig;

    // Simple heuristics to determine chart type based on data structure and question
    const keys = Object.keys(data[0]);
    const isAggregation = keys.includes('result') && keys.length === 2; // e.g., user, result or app, result

    if (isAggregation) {
        // Bar chart for aggregates like counts or sums per category
        const labels = data.map(item => {
            const label = Object.values(item)[0];
            // Truncate long labels for better display
            return String(label).length > 12 ? String(label).substring(0, 12) + '...' : String(label);
        });
        const values = data.map(item => item.result);

        chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Hours',
                    data: values,
                    backgroundColor: 'rgba(74, 144, 226, 0.8)',
                    borderColor: 'rgba(74, 144, 226, 1)',
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 12,
                                weight: 'bold'
                            },
                            padding: 20
                        }
                    },
                    title: {
                        display: true,
                        text: 'Usage Analysis',
                        color: 'rgba(255, 255, 255, 0.9)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 30
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(74, 144, 226, 1)',
                        borderWidth: 1,
                        cornerRadius: 6,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                // Show full label in tooltip
                                const originalLabel = Object.values(data[context[0].dataIndex])[0];
                                return String(originalLabel);
                            },
                            label: function(context) {
                                const value = context.parsed.y;
                                const hours = Math.floor(value / 3600);
                                const minutes = Math.floor((value % 3600) / 60);
                                return `${hours}h ${minutes}m (${value.toLocaleString()} seconds)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            lineWidth: 1
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                // Convert seconds to hours for display
                                const hours = Math.floor(value / 3600);
                                return hours + 'h';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Hours',
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            lineWidth: 1
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 0
                        },
                        title: {
                            display: true,
                            text: 'Users',
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                },
                layout: {
                    padding: {
                        top: 20,
                        bottom: 20,
                        left: 20,
                        right: 20
                    }
                }
            }
        };
    } else if (keys.includes('date') || keys.includes('timestamp') || keys.includes('time')) {
        // Line chart for time series data
        const timeKey = keys.find(k => k.includes('date') || k.includes('timestamp') || k.includes('time'));
        const valueKey = keys.find(k => k !== timeKey);
        
        chartConfig = {
            type: 'line',
            data: {
                labels: data.map(item => item[timeKey]),
                datasets: [{
                    label: valueKey,
                    data: data.map(item => item[valueKey]),
                    borderColor: 'rgba(74, 144, 226, 1)',
                    backgroundColor: 'rgba(74, 144, 226, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointBackgroundColor: 'rgba(74, 144, 226, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Trend Analysis',
                        color: 'rgba(255, 255, 255, 0.9)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 11
                            },
                            maxRotation: 45
                        }
                    }
                },
                layout: {
                    padding: 20
                }
            }
        };
    } else {
        // Default to a simple bar chart
        const labels = data.map((item, index) => `Item ${index + 1}`);
        const values = data.map(item => Object.values(item)[0]);

        chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Values',
                    data: values,
                    backgroundColor: 'rgba(74, 144, 226, 0.8)',
                    borderColor: 'rgba(74, 144, 226, 1)',
                    borderWidth: 2,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: 'rgba(255, 255, 255, 0.9)',
                            font: {
                                size: 12
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Data Visualization',
                        color: 'rgba(255, 255, 255, 0.9)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                layout: {
                    padding: 20
                }
            }
        };
    }

    // Create and store chart instance
    const chartInstance = new Chart(ctx, chartConfig);
    chatChartInstances.set(canvas.id, chartInstance);
}
