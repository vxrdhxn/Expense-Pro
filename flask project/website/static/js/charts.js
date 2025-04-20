// Chart configurations
const initializeCharts = (container) => {
    if (!container) return;

    // Get data from container
    const dailyLabels = JSON.parse(container.dataset.dailyLabels || '[]');
    const dailyValues = JSON.parse(container.dataset.dailyValues || '[]');
    const categoryLabels = JSON.parse(container.dataset.categoryLabels || '[]');
    const categoryValues = JSON.parse(container.dataset.categoryValues || '[]');
    const currency = container.dataset.currency;

    // Get theme
    const isDarkMode = document.documentElement.classList.contains('dark');
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDarkMode ? '#fff' : '#000';

    // Daily Expenses Chart
    const dailyCtx = document.getElementById('dailyExpensesChart');
    if (dailyCtx) {
        const existingChart = Chart.getChart(dailyCtx);
        if (existingChart) {
            existingChart.destroy();
        }

        new Chart(dailyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: dailyLabels,
                datasets: [{
                    data: dailyValues, 
                    borderColor: '#007AFF',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#007AFF',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1C1C1E',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {
                            size: 13,
                            family: 'SF Pro Text'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'SF Pro Text'
                        },
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `${currency} ${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'SF Pro Text',
                                size: 12
                            },
                            color: '#98989D'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(152, 152, 157, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                family: 'SF Pro Text',
                                size: 12
                            },
                            color: '#98989D',
                            callback: function(value) {
                                return `${currency} ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Category Distribution Chart
    const categoryCtx = document.getElementById('categoryDistributionChart');
    if (categoryCtx) {
        const existingChart = Chart.getChart(categoryCtx);
        if (existingChart) {
            existingChart.destroy();
        }

        new Chart(categoryCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryValues,
                    backgroundColor: [
                        '#007AFF', '#34C759', '#FF9500', '#FF3B30', '#5856D6',
                        '#FF2D55', '#AF52DE', '#5AC8FA', '#FFCC00', '#64D2FF'
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#FFFFFF',  // Set legend text color to white
                            font: {
                                family: 'SF Pro Text',
                                size: 12
                            },
                            padding: 20,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: `${label}: ${currency} ${data.datasets[0].data[i]}`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i,
                                    textColor: '#FFFFFF'  // Add text color for legend items
                                }));
                            },
                            color: '#FFFFFF'  // Ensure text color is white
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1C1C1E',
                        titleColor: '#FFFFFF',
                        bodyColor: '#FFFFFF',
                        titleFont: {
                            size: 13,
                            family: 'SF Pro Text'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'SF Pro Text'
                        },
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw;
                                return `${label}: ${currency} ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }
};

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chartContainer = document.getElementById('chartContainer');
    if (chartContainer) {
        initializeCharts(chartContainer);
    }
});

// Export the initialization function
window.initializeCharts = initializeCharts;
