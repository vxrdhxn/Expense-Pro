// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
});

function initializeCharts() {
    const categoryChart = document.getElementById('categoryChart');
    const dailyChart = document.getElementById('dailyChart');
    const currencySymbol = window.CURRENCY_SYMBOL || '$';

    console.log('Initializing charts with currency symbol:', currencySymbol);
    console.log('Category chart element:', categoryChart);
    console.log('Daily chart element:', dailyChart);

    if (categoryChart) {
        console.log('Category chart data:', {
            labels: categoryChart.dataset.labels,
            values: categoryChart.dataset.values
        });
    }

    if (dailyChart) {
        console.log('Daily chart data:', dailyChart.dataset.expenses);
    }

    initializeCategoryChart(categoryChart, currencySymbol);
    initializeDailyExpensesChart(dailyChart, currencySymbol);
}

function initializeCategoryChart(chartElement, currencySymbol) {
    if (!chartElement) return;

    const categoryLabels = JSON.parse(chartElement.dataset.labels || '[]');
    const categoryValues = JSON.parse(chartElement.dataset.values || '[]');

    if (categoryLabels.length === 0 || categoryValues.length === 0) return;

    new Chart(chartElement, {
        type: 'doughnut',
        data: {
            labels: categoryLabels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: categoryValues,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',   // Blue
                    'rgba(16, 185, 129, 0.8)',   // Green
                    'rgba(139, 92, 246, 0.8)',   // Purple
                    'rgba(245, 158, 11, 0.8)',   // Yellow
                    'rgba(239, 68, 68, 0.8)'     // Red
                ],
                borderWidth: 2,
                borderColor: '#1F2937'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#E5E7EB',
                        font: { size: 12 },
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${currencySymbol}${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1000
            }
        }
    });
}

function initializeDailyExpensesChart(chartElement, currencySymbol) {
    if (!chartElement) return;

    const dailyData = JSON.parse(chartElement.dataset.expenses || '{}');
    const dailyLabels = Object.keys(dailyData);
    const dailyValues = Object.values(dailyData);

    if (dailyLabels.length === 0) return;

    new Chart(chartElement, {
        type: 'line',
        data: {
            labels: dailyLabels,
            datasets: [{
                label: 'Daily Expenses',
                data: dailyValues,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#3B82F6',
                pointBorderColor: '#1F2937',
                pointHoverBackgroundColor: '#60A5FA',
                pointHoverBorderColor: '#1F2937'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${currencySymbol}${context.raw.toFixed(2)}`;
                        }
                    },
                    backgroundColor: '#1F2937',
                    titleColor: '#E5E7EB',
                    bodyColor: '#E5E7EB',
                    padding: 12,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(75, 85, 99, 0.2)' },
                    ticks: { color: '#E5E7EB' }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(75, 85, 99, 0.2)' },
                    ticks: {
                        color: '#E5E7EB',
                        callback: function(value) {
                            return currencySymbol + value.toFixed(2);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
} 