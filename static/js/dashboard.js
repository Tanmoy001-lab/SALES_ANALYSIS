document.addEventListener("DOMContentLoaded", () => {
    console.log("Dashboard JS Loaded successfully!");
    loadKPIs();
    loadSalesTrend();
    loadCategoryPerformance();
    loadTopProducts();
    loadRegionSales();
    loadCustomerSegments();
    loadCorrelation();
    loadSalesOutliers();
    loadProductPerformance();
    loadTopReturnProducts();
});

// Store chart instances globally to prevent duplicate canvas errors
const chartInstances = {};

const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94a3b8' } } },
    scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
    }
};

function renderChart(canvasId, config) {
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, config);
}

function loadKPIs() {
    fetch('/api/v1/kpis')
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            document.getElementById('kpi-sales').innerText = `$${data.total_sales.toLocaleString()}`;
            document.getElementById('kpi-profit').innerText = `$${data.total_profit.toLocaleString()}`;
            document.getElementById('kpi-orders').innerText = data.total_orders.toLocaleString();
            document.getElementById('kpi-returns').innerText = `${data.return_rate}%`;
        })
        .catch(err => console.error("Error loading KPIs:", err));
}

function loadSalesTrend() {
    fetch('/api/v1/sales-trend')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.labels) return;
            renderChart('salesTrendChart', {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        { label: 'Sales ($)', data: data.sales, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.3 },
                        { label: 'Profit ($)', data: data.profit, borderColor: '#60a5fa', backgroundColor: 'rgba(96, 165, 250, 0.1)', fill: true, tension: 0.3 }
                    ]
                },
                options: defaultChartOptions
            });
        })
        .catch(err => console.error("Error loading Sales Trend:", err));
}

function loadCategoryPerformance() {
    fetch('/api/v1/category-performance')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.categories) return;
            renderChart('categoryChart', {
                type: 'bar',
                data: {
                    labels: data.categories,
                    datasets: [
                        { label: 'Sales ($)', data: data.sales, backgroundColor: '#34d399' },
                        { label: 'Profit ($)', data: data.profit, backgroundColor: '#818cf8' }
                    ]
                },
                options: defaultChartOptions
            });
        })
        .catch(err => console.error("Error loading Category Performance:", err));
}

function loadTopProducts() {
    fetch('/api/v1/top-products')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.products) return;
            renderChart('topProductsChart', {
                type: 'bar',
                data: {
                    labels: data.products,
                    datasets: [{ label: 'Sales ($)', data: data.sales, backgroundColor: '#38bdf8' }]
                },
                options: defaultChartOptions
            });
        })
        .catch(err => console.error("Error loading Top Products:", err));
}

function loadRegionSales() {
    fetch('/api/v1/region-sales')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.regions) return;
            renderChart('regionChart', {
                type: 'bar',
                data: {
                    labels: data.regions,
                    datasets: [{ label: 'Sales ($)', data: data.sales, backgroundColor: '#fbbf24' }]
                },
                options: defaultChartOptions
            });
        })
        .catch(err => console.error("Error loading Region Sales:", err));
}

function loadCustomerSegments() {
    fetch('/api/v1/customer-segments')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.segments) return;
            renderChart('segmentChart', {
                type: 'doughnut',
                data: {
                    labels: data.segments,
                    datasets: [{ data: data.counts, backgroundColor: ['#38bdf8', '#818cf8', '#f43f5e', '#fbbf24'] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } }
                }
            });
        })
        .catch(err => console.error("Error loading Customer Segments:", err));
}

function loadCorrelation() {
    fetch('/api/v1/correlation')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.features) return;

            const container = document.getElementById('heatmap-container');
            const cols = data.features;
            const matrix = data.matrix;

            let tableHtml = `<div class="overflow-x-auto"><table class="w-full text-xs text-center border-collapse">`;
            tableHtml += `<thead><tr><th class="p-2 text-slate-400 font-semibold border-b border-slate-800 text-left min-w-[100px]">Feature</th>`;
            cols.forEach(col => {
                tableHtml += `<th class="p-2 text-slate-400 font-semibold border-b border-slate-800">${col}</th>`;
            });
            tableHtml += `</tr></thead><tbody>`;

            matrix.forEach((row, rowIndex) => {
                tableHtml += `<tr class="hover:bg-slate-800/30"><td class="p-2 font-semibold text-slate-300 border-r border-slate-800 text-left min-w-[100px]">${cols[rowIndex]}</td>`;
                row.forEach((value) => {
                    let bgClass = "bg-slate-800/40 text-slate-300";
                    let val = parseFloat(value);

                    if (val === 1.0) {
                        bgClass = "bg-rose-600 text-white font-bold";
                    } else if (val >= 0.6) {
                        bgClass = "bg-orange-500/80 text-white font-semibold";
                    } else if (val >= 0.3) {
                        bgClass = "bg-amber-500/50 text-amber-100";
                    } else if (val > 0) {
                        bgClass = "bg-slate-800 text-slate-300";
                    } else if (val < 0) {
                        bgClass = "bg-indigo-600/50 text-indigo-200";
                    }

                    tableHtml += `<td class="p-2.5 ${bgClass} border border-slate-950 font-mono">${val.toFixed(3)}</td>`;
                });
                tableHtml += `</tr>`;
            });

            tableHtml += `</tbody></table></div>`;
            container.innerHTML = tableHtml;
        })
        .catch(err => console.error("Error loading Correlation Heatmap:", err));
}

function loadSalesOutliers() {
    fetch('/api/v1/sales-outliers')
        .then(res => res.json())
        .then(data => {
            if (data.error) return;

            // Update stats
            document.getElementById('outlier-q1').innerText = `$${data.q1.toLocaleString()}`;
            document.getElementById('outlier-median').innerText = `$${data.median.toLocaleString()}`;
            document.getElementById('outlier-q3').innerText = `$${data.q3.toLocaleString()}`;
            document.getElementById('outlier-threshold').innerText = `$${data.upper_bound.toLocaleString()}`;
            document.getElementById('outlier-max').innerText = `$${data.max.toLocaleString()}`;
            document.getElementById('outlier-badge').innerText = `${data.outlier_count.toLocaleString()} Outliers Detected`;

            // Prepare Scatter Plot data representing the distribution & outliers
            const outlierPoints = data.outliers_sample.map(val => ({ x: val, y: 0 }));

            renderChart('outliersChart', {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Sales Outliers',
                        data: outlierPoints,
                        backgroundColor: '#f43f5e',
                        borderColor: '#fb7185',
                        borderWidth: 1,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#94a3b8' } },
                        tooltip: {
                            callbacks: {
                                label: (context) => `Outlier Value: $${context.raw.x.toLocaleString()}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            title: { display: true, text: 'Sales Amount ($)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: '#334155' }
                        },
                        y: {
                            display: false,
                            min: -1,
                            max: 1
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading Sales Outliers:", err));
}

function loadProductPerformance() {
    fetch('/api/v1/product-performance')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.products) return;

            renderChart('productPerformanceChart', {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Products',
                        data: data.products,
                        backgroundColor: '#3b82f6', // Tailwind blue-500
                        borderColor: '#60a5fa',
                        borderWidth: 1,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const point = context.raw;
                                    return `${point.name}: Sales = $${point.x.toLocaleString()}, Profit = $${point.y.toLocaleString()}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Total Sales ($)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: '#334155' }
                        },
                        y: {
                            title: { display: true, text: 'Total Profit ($)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: '#334155' }
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading Product Performance:", err));
}

function loadTopReturnProducts() {
    fetch('/api/v1/top-return-products')
        .then(res => res.json())
        .then(data => {
            if (data.error || !data.products) return;

            renderChart('topReturnProductsChart', {
                type: 'bar',
                data: {
                    labels: data.products,
                    datasets: [{
                        label: 'Return Rate (%)',
                        data: data.return_rates,
                        backgroundColor: '#0284c7', // Slate Blue / Sky Blue
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const index = context.dataIndex;
                                    const returned = data.returned_orders[index];
                                    const total = data.total_orders[index];
                                    return `Return Rate: ${context.raw}% (${returned}/${total} orders)`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Product', color: '#94a3b8' },
                            ticks: { color: '#94a3b8', maxRotation: 45, minRotation: 35 },
                            grid: { color: 'transparent' }
                        },
                        y: {
                            title: { display: true, text: 'Return Rate (%)', color: '#94a3b8' },
                            ticks: { color: '#94a3b8' },
                            grid: { color: '#334155' },
                            suggestedMax: 65
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading Top Return Products:", err));
}