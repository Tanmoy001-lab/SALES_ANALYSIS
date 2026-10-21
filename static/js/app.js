/**
 * RetailPulse AI - Master Application Controller
 * Handles Authentication, Navigation, Live Analytics, Machine Learning Studio, EDA, and Data CRUD
 */

// Application State
const AppState = {
    user: null, // { id, username, email, name, role }
    filters: {
        region: 'All',
        category: 'All'
    },
    transactions: {
        items: [],
        total: 0,
        limit: 12,
        offset: 0,
        search: '',
        region: 'All',
        category: 'All',
        sort_by: 'Order_Date',
        sort_order: 'DESC'
    },
    activeTab: 'overview'
};

const chartInstances = {};

// Helper: Safely destroy and re-render Chart.js
function renderChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }
    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, config);
    return chartInstances[canvasId];
}

// Chart.js Dark Mode Defaults
const darkChartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 12 } }
        },
        tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#f8fafc',
            bodyColor: '#e2e8f0',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
        }
    },
    scales: {
        x: {
            ticks: { color: '#64748b', font: { size: 11 } },
            grid: { color: 'rgba(255, 255, 255, 0.04)' }
        },
        y: {
            ticks: { color: '#64748b', font: { size: 11 } },
            grid: { color: 'rgba(255, 255, 255, 0.04)' }
        }
    }
};

// ==========================================
// TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", async () => {
    console.log("RetailPulse AI frontend initialized");
    
    setupNavigation();
    setupModals();
    setupRoleMenu();
    setupFilterEvents();
    setupPredictionSliders();

    await checkAuth();
    await loadFilterDropdowns();
    await loadDashboardData();
    await loadMLStudioData();
    await loadEDAData();
    await loadTransactions();

    // Check URL parameters for tab navigation and screenshot capture
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab');
    if (initialTab) {
        switchTab(initialTab);
        if (initialTab === 'ml-studio') {
            setTimeout(() => makePrediction(), 300);
        }
    }
    if (urlParams.get('auth') === 'success') {
        showToast('Signed in with Google successfully!', 'success');
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('auth') === 'error') {
        const msg = urlParams.get('msg') || 'Google authentication failed';
        showToast(msg, 'error');
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    if (urlParams.get('modal') === 'auth') {
        openModal('auth-modal');
    }
    if (urlParams.get('modal') === 'add') {
        switchTab('transactions');
        openModal('add-transaction-modal');
    }
    if (urlParams.get('scroll')) {
        setTimeout(() => window.scrollTo(0, parseInt(urlParams.get('scroll'))), 400);
    }
});

// Setup Global Filters in Navigation
function setupFilterEvents() {
    const regionSelect = document.getElementById('global-region-select');
    const categorySelect = document.getElementById('global-category-select');

    if (regionSelect) {
        regionSelect.addEventListener('change', (e) => {
            AppState.filters.region = e.target.value;
            AppState.transactions.region = e.target.value;
            AppState.transactions.offset = 0;
            refreshAllData();
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            AppState.filters.category = e.target.value;
            AppState.transactions.category = e.target.value;
            AppState.transactions.offset = 0;
            refreshAllData();
        });
    }
}

async function refreshAllData() {
    await loadDashboardData();
    await loadProductPerformance();
    await loadTopReturnProducts();
    await loadTransactions();
}

async function loadFilterDropdowns() {
    try {
        const res = await fetch('/api/v1/filter-options');
        const data = await res.json();
        if (data.regions) {
            const regSelect = document.getElementById('global-region-select');
            const transRegSelect = document.getElementById('trans-filter-region');
            const addRegSelect = document.getElementById('add-region');
            
            [regSelect, transRegSelect, addRegSelect].forEach(sel => {
                if (!sel) return;
                const isForm = sel === addRegSelect;
                sel.innerHTML = isForm ? '' : '<option value="All">All Regions</option>';
                data.regions.forEach(r => {
                    const opt = document.createElement('option');
                    opt.value = r;
                    opt.textContent = r;
                    sel.appendChild(opt);
                });
            });
        }

        if (data.categories) {
            const catSelect = document.getElementById('global-category-select');
            const transCatSelect = document.getElementById('trans-filter-category');
            const addCatSelect = document.getElementById('add-category');
            const predCatSelect = document.getElementById('predCategory');

            [catSelect, transCatSelect, addCatSelect, predCatSelect].forEach(sel => {
                if (!sel) return;
                const isForm = (sel === addCatSelect || sel === predCatSelect);
                sel.innerHTML = isForm ? '' : '<option value="All">All Categories</option>';
                data.categories.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c;
                    opt.textContent = c;
                    sel.appendChild(opt);
                });
            });
        }
    } catch (err) {
        console.error("Filter options load error:", err);
    }
}

// ==========================================
// AUTHENTICATION & ROLE MANAGEMENT
// ==========================================
async function checkAuth() {
    try {
        const res = await fetch('/api/v1/auth/me');
        const data = await res.json();
        if (data.authenticated && data.user) {
            AppState.user = data.user;
        } else {
            // Default to analyst user for initial preview if none logged in
            const localUser = localStorage.getItem('retailpulse_user');
            if (localUser) {
                AppState.user = JSON.parse(localUser);
            } else {
                // Auto login as default user for frictionless initial view
                await quickLogin('admin', false);
            }
        }
        updateAuthUI();
    } catch (err) {
        console.error("Auth check failed:", err);
    }
}

function updateAuthUI() {
    const user = AppState.user;
    const userNameEl = document.getElementById('topbar-user-name');
    const userRoleEl = document.getElementById('topbar-user-role');
    const userAvatarEl = document.getElementById('topbar-user-avatar');
    const adminTab = document.getElementById('tab-btn-admin');
    const adminRetrainBtn = document.getElementById('btn-retrain-ml');
    const adminAddTransBtn = document.getElementById('btn-add-transaction');
    const adminUploadBtn = document.getElementById('btn-upload-dataset');

    if (user) {
        if (userNameEl) userNameEl.textContent = user.name || user.username;
        if (userRoleEl) {
            userRoleEl.textContent = user.role.toUpperCase();
            userRoleEl.className = `user-role-pill ${user.role === 'admin' ? 'role-admin' : 'role-user'}`;
        }
        if (userAvatarEl) {
            if (user.picture) {
                userAvatarEl.innerHTML = `<img src="${user.picture}" alt="${user.name || 'User'}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" referrerpolicy="no-referrer">`;
            } else {
                userAvatarEl.textContent = (user.name || user.username).substring(0, 2).toUpperCase();
            }
        }

        // Toggle Admin Restricted Controls
        const isAdmin = user.role === 'admin';
        if (adminTab) adminTab.style.display = isAdmin ? 'inline-flex' : 'none';
        if (adminRetrainBtn) {
            adminRetrainBtn.disabled = !isAdmin;
            adminRetrainBtn.title = isAdmin ? "Retrain models on latest data" : "Admin privileges required";
        }
        if (adminAddTransBtn) {
            adminAddTransBtn.style.display = isAdmin ? 'inline-flex' : 'none';
        }
        if (adminUploadBtn) {
            adminUploadBtn.style.display = isAdmin ? 'inline-flex' : 'none';
        }

        // Update action column visibility in table
        const tableActionHeader = document.getElementById('th-actions');
        if (tableActionHeader) tableActionHeader.style.display = isAdmin ? 'table-cell' : 'none';

        localStorage.setItem('retailpulse_user', JSON.stringify(user));
    } else {
        if (userNameEl) userNameEl.textContent = "Guest";
        if (userRoleEl) {
            userRoleEl.textContent = "VISITOR";
            userRoleEl.className = "user-role-pill role-user";
        }
        if (adminTab) adminTab.style.display = 'none';
    }
}

async function quickLogin(role, notify = true) {
    try {
        const res = await fetch('/api/v1/auth/quick-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        });
        const data = await res.json();
        if (data.success) {
            AppState.user = data.user;
            updateAuthUI();
            closeModal('auth-modal');
            if (notify) showToast(`Switched account to ${data.user.name} (${role.toUpperCase()})`, 'success');
            loadTransactions();
            if (role === 'admin') loadAdminStats();
        } else {
            showToast(data.error || "Login failed", 'error');
        }
    } catch (err) {
        showToast("Quick login network error", 'error');
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.success) {
            AppState.user = data.user;
            updateAuthUI();
            closeModal('auth-modal');
            showToast(`Welcome back, ${data.user.name}!`, 'success');
            loadTransactions();
        } else {
            showToast(data.error || "Invalid credentials", 'error');
        }
    } catch (err) {
        showToast("Login connection error", 'error');
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const role = document.getElementById('reg-role').value;

    try {
        const res = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, username, email, password, role })
        });
        const data = await res.json();
        if (data.success) {
            AppState.user = data.user;
            updateAuthUI();
            closeModal('auth-modal');
            showToast("Registration successful!", 'success');
        } else {
            showToast(data.error || "Registration failed", 'error');
        }
    } catch (err) {
        showToast("Registration connection error", 'error');
    }
}

async function handleLogout() {
    try {
        await fetch('/api/v1/auth/logout', { method: 'POST' });
        AppState.user = null;
        localStorage.removeItem('retailpulse_user');
        updateAuthUI();
        showToast("Logged out successfully", 'info');
        openModal('auth-modal');
    } catch (err) {
        console.error(err);
    }
}

// Setup Role dropdown menu
function setupRoleMenu() {
    const profileBadge = document.getElementById('topbar-profile-badge');
    const menu = document.getElementById('role-switch-menu');

    if (profileBadge && menu) {
        profileBadge.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('show');
        });

        document.addEventListener('click', () => {
            menu.classList.remove('show');
        });
    }
}

// ==========================================
// NAVIGATION TABS
// ==========================================
function setupNavigation() {
    const tabBtns = document.querySelectorAll('.nav-tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    AppState.activeTab = tabId;

    // Update buttons
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update tab content panels
    document.querySelectorAll('.tab-content').forEach(panel => {
        if (panel.id === `tab-content-${tabId}`) {
            panel.classList.add('active');
        } else {
            panel.classList.remove('active');
        }
    });

    // Lazy load or resize charts on tab activation
    if (tabId === 'admin') {
        loadAdminStats();
    }
}

// ==========================================
// DASHBOARD & EXECUTIVE OVERVIEW
// ==========================================
async function loadDashboardData() {
    const params = new URLSearchParams();
    if (AppState.filters.region !== 'All') params.append('region', AppState.filters.region);
    if (AppState.filters.category !== 'All') params.append('category', AppState.filters.category);

    const queryStr = params.toString() ? `?${params.toString()}` : '';

    try {
        // 1. KPIs
        const kpiRes = await fetch(`/api/v1/kpis${queryStr}`);
        const kpiData = await kpiRes.json();
        if (!kpiData.error) {
            document.getElementById('kpi-sales').innerText = `$${kpiData.total_sales.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('kpi-profit').innerText = `$${kpiData.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('kpi-margin').innerText = `${kpiData.profit_margin}%`;
            document.getElementById('kpi-orders').innerText = kpiData.total_orders.toLocaleString();
            document.getElementById('kpi-returns').innerText = `${kpiData.return_rate}%`;
        }

        // 2. Sales Trend
        const trendRes = await fetch(`/api/v1/sales-trend${queryStr}`);
        const trendData = await trendRes.json();
        if (!trendData.error && trendData.labels) {
            renderChart('salesTrendChart', {
                type: 'line',
                data: {
                    labels: trendData.labels,
                    datasets: [
                        {
                            label: 'Revenue ($)',
                            data: trendData.sales,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.12)',
                            fill: true,
                            tension: 0.35,
                            borderWidth: 2.5,
                            pointRadius: 3,
                            pointHoverRadius: 6
                        },
                        {
                            label: 'Profit ($)',
                            data: trendData.profit,
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            fill: true,
                            tension: 0.35,
                            borderWidth: 2,
                            pointRadius: 3
                        }
                    ]
                },
                options: darkChartDefaults
            });
        }

        // 3. Category Performance
        const catRes = await fetch(`/api/v1/category-performance${queryStr}`);
        const catData = await catRes.json();
        if (!catData.error && catData.categories) {
            renderChart('categoryChart', {
                type: 'bar',
                data: {
                    labels: catData.categories,
                    datasets: [
                        {
                            label: 'Sales ($)',
                            data: catData.sales,
                            backgroundColor: '#34d399',
                            borderRadius: 6
                        },
                        {
                            label: 'Profit ($)',
                            data: catData.profit,
                            backgroundColor: '#818cf8',
                            borderRadius: 6
                        }
                    ]
                },
                options: darkChartDefaults
            });
        }

        // 4. Top Products
        const prodRes = await fetch(`/api/v1/top-products${queryStr}`);
        const prodData = await prodRes.json();
        if (!prodData.error && prodData.products) {
            renderChart('topProductsChart', {
                type: 'bar',
                data: {
                    labels: prodData.products.map(p => p.length > 25 ? p.substring(0, 23) + '...' : p),
                    datasets: [{
                        label: 'Sales ($)',
                        data: prodData.sales,
                        backgroundColor: '#38bdf8',
                        borderRadius: 6
                    }]
                },
                options: {
                    ...darkChartDefaults,
                    indexAxis: 'y'
                }
            });
        }

        // 5. Region Distribution
        const regRes = await fetch(`/api/v1/region-sales${queryStr}`);
        const regData = await regRes.json();
        if (!regData.error && regData.regions) {
            renderChart('regionChart', {
                type: 'doughnut',
                data: {
                    labels: regData.regions,
                    datasets: [{
                        data: regData.sales,
                        backgroundColor: ['#10b981', '#06b6d4', '#6366f1', '#f59e0b', '#ec4899'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#94a3b8' } }
                    },
                    cutout: '65%'
                }
            });
        }

    } catch (err) {
        console.error("Dashboard data load error:", err);
    }
}

// ==========================================
// MACHINE LEARNING STUDIO
// ==========================================
function setupPredictionSliders() {
    const qtySlider = document.getElementById('predQuantity');
    const discSlider = document.getElementById('predDiscount');

    if (qtySlider) {
        qtySlider.addEventListener('input', (e) => {
            const val = document.getElementById('val-predQuantity');
            if (val) val.textContent = e.target.value;
        });
    }

    if (discSlider) {
        discSlider.addEventListener('input', (e) => {
            const val = document.getElementById('val-predDiscount');
            if (val) val.textContent = `${e.target.value}%`;
        });
    }
}

async function makePrediction() {
    const btn = document.getElementById('btn-run-prediction');
    if (btn) btn.innerHTML = '<span>⚡</span> Calculating AI Inference...';

    const payload = {
        quantity: parseFloat(document.getElementById('predQuantity').value || 1),
        unit_price: parseFloat(document.getElementById('predUnitPrice').value || 100),
        discount: parseFloat(document.getElementById('predDiscount').value || 0),
        category: document.getElementById('predCategory').value || 'Electronics',
        region: document.getElementById('predRegion').value || 'North',
        customer_segment: document.getElementById('predSegment').value || 'Regular',
        order_priority: document.getElementById('predPriority').value || 'Medium',
        delivery_days: parseFloat(document.getElementById('predDeliveryDays').value || 3),
        customer_rating: parseFloat(document.getElementById('predRating').value || 4.0)
    };

    try {
        const res = await fetch('/api/v1/ml/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.predicted_sales !== undefined) {
            document.getElementById('res-sales').innerText = `$${data.predicted_sales.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            document.getElementById('res-gross').innerText = `$${data.gross_sales.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            document.getElementById('res-discount').innerText = `-$${data.discount_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            document.getElementById('res-profit').innerText = `$${data.estimated_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            document.getElementById('res-margin').innerText = `${data.profit_margin_pct}%`;
            document.getElementById('res-confidence').innerText = `${data.confidence_score}%`;
            showToast("AI Sales prediction calculated!", 'success');
        } else {
            showToast(data.error || "Prediction computation failed", 'error');
        }
    } catch (err) {
        showToast("Error communicating with ML predictor", 'error');
    } finally {
        if (btn) btn.innerHTML = '<span>✨</span> Run AI Sales Prediction';
    }
}

async function loadMLStudioData() {
    try {
        // 1. Model Benchmark & Metrics
        const metricsRes = await fetch('/api/v1/ml/metrics');
        const metrics = await metricsRes.json();
        if (metrics.models) {
            const rf = metrics.models.random_forest;
            const lr = metrics.models.linear_regression;

            document.getElementById('rf-r2').innerText = `${(rf.r2_score * 100).toFixed(1)}%`;
            document.getElementById('rf-rmse').innerText = `$${rf.rmse.toLocaleString()}`;
            document.getElementById('rf-mae').innerText = `$${rf.mae.toLocaleString()}`;

            document.getElementById('lr-r2').innerText = `${(lr.r2_score * 100).toFixed(1)}%`;
            document.getElementById('lr-rmse').innerText = `$${lr.rmse.toLocaleString()}`;
            document.getElementById('lr-mae').innerText = `$${lr.mae.toLocaleString()}`;

            if (document.getElementById('ml-last-trained')) {
                document.getElementById('ml-last-trained').innerText = metrics.last_trained || 'Just now';
            }

            // Render Feature Importance Chart
            if (metrics.feature_importances) {
                renderChart('featureImportanceChart', {
                    type: 'bar',
                    data: {
                        labels: metrics.feature_importances.map(f => f.feature),
                        datasets: [{
                            label: 'Impact Score (%)',
                            data: metrics.feature_importances.map(f => f.importance),
                            backgroundColor: 'rgba(16, 185, 129, 0.75)',
                            borderColor: '#10b981',
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        ...darkChartDefaults,
                        indexAxis: 'y'
                    }
                });
            }
        }

        // 2. Customer Segmentation Clusters (RFM K-Means)
        const clusterRes = await fetch('/api/v1/ml/clusters');
        const clusterData = await clusterRes.json();
        if (clusterData.clusters) {
            renderClusterCards(clusterData.clusters);

            if (clusterData.sample_points) {
                renderChart('clusterScatterChart', {
                    type: 'scatter',
                    data: {
                        datasets: clusterData.clusters.map(c => {
                            const points = clusterData.sample_points.filter(p => p.cluster === c.cluster_id);
                            return {
                                label: c.name,
                                data: points.map(p => ({ x: p.x, y: p.y })),
                                backgroundColor: c.color,
                                pointRadius: 4,
                                pointHoverRadius: 7
                            };
                        })
                    },
                    options: {
                        ...darkChartDefaults,
                        scales: {
                            x: {
                                title: { display: true, text: 'Recency (Days Since Last Order)', color: '#94a3b8' },
                                grid: { color: 'rgba(255, 255, 255, 0.04)' },
                                ticks: { color: '#64748b' }
                            },
                            y: {
                                title: { display: true, text: 'Monetary Spend ($)', color: '#94a3b8' },
                                grid: { color: 'rgba(255, 255, 255, 0.04)' },
                                ticks: { color: '#64748b' }
                            }
                        }
                    }
                });
            }
        }

    } catch (err) {
        console.error("Error loading ML Studio data:", err);
    }
}

function renderClusterCards(clusters) {
    const container = document.getElementById('clusters-cards-container');
    if (!container) return;
    container.innerHTML = '';

    clusters.forEach(c => {
        const card = document.createElement('div');
        card.className = 'cluster-card';
        card.innerHTML = `
            <div class="cluster-card-header">
                <h4 style="font-size:0.95rem; font-weight:700;">${c.name}</h4>
                <span class="cluster-pill" style="background:${c.color}25; color:${c.color}; border:1px solid ${c.color}60;">${c.badge}</span>
            </div>
            <div class="cluster-metrics-grid">
                <div class="cluster-metric-box">
                    <span>Avg Recency</span>
                    <strong>${c.avg_recency_days}d</strong>
                </div>
                <div class="cluster-metric-box">
                    <span>Avg Frequency</span>
                    <strong>${c.avg_frequency}</strong>
                </div>
                <div class="cluster-metric-box">
                    <span>Avg Spend</span>
                    <strong>$${Math.round(c.avg_monetary).toLocaleString()}</strong>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94a3b8; margin-bottom:0.6rem;">
                <span>Share: <strong>${c.percentage_customers}%</strong> (${c.customer_count.toLocaleString()} shoppers)</span>
                <span>Revenue Share: <strong>${c.percentage_revenue}%</strong></span>
            </div>
            <div class="cluster-strategy" style="border-left-color: ${c.color};">
                💡 <strong>Strategy:</strong> ${c.strategy}
            </div>
        `;
        container.appendChild(card);
    });
}

async function retrainModels() {
    if (!AppState.user || AppState.user.role !== 'admin') {
        showToast("Admin privileges required to retrain AI models.", 'error');
        return;
    }

    const btn = document.getElementById('btn-retrain-ml');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> Retraining Random Forest & K-Means...';
    }

    try {
        const res = await fetch('/api/v1/ml/train', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("Machine learning models retrained successfully!", 'success');
            await loadMLStudioData();
            if (AppState.activeTab === 'admin') await loadAdminStats();
        } else {
            showToast(data.error || "Model retraining failed", 'error');
        }
    } catch (err) {
        showToast("Retraining error", 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span>⚡</span> Retrain AI Models';
        }
    }
}

// ==========================================
// EXPLORATORY DATA ANALYSIS (EDA)
// ==========================================
async function loadEDAData() {
    await loadCorrelation();
    await loadSalesOutliers();
    await loadProductPerformance();
    await loadTopReturnProducts();
}

async function loadCorrelation() {
    try {
        const res = await fetch('/api/v1/correlation');
        const data = await res.json();
        if (data.error || !data.features) return;

        const container = document.getElementById('heatmap-container');
        if (!container) return;

        const table = document.createElement('table');
        table.className = 'heatmap-table';

        // Header Row
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Feature</th>' + data.features.map(f => `<th>${f}</th>`).join('');
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body Rows
        const tbody = document.createElement('tbody');
        data.matrix.forEach((row, i) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<th style="text-align:left; padding-left:0.75rem;">${data.features[i]}</th>`;
            row.forEach(val => {
                const td = document.createElement('td');
                td.className = 'heatmap-cell';
                td.innerText = val.toFixed(2);

                // Dynamic background shading
                if (val >= 0) {
                    td.style.backgroundColor = `rgba(16, 185, 129, ${Math.min(0.85, val * 0.9)})`;
                    td.style.color = val > 0.4 ? '#ffffff' : '#94a3b8';
                } else {
                    td.style.backgroundColor = `rgba(244, 63, 94, ${Math.min(0.85, Math.abs(val) * 0.9)})`;
                    td.style.color = Math.abs(val) > 0.4 ? '#ffffff' : '#94a3b8';
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        container.innerHTML = '';
        container.appendChild(table);
    } catch (err) {
        console.error("Correlation error:", err);
    }
}

async function loadSalesOutliers() {
    try {
        const res = await fetch('/api/v1/sales-outliers');
        const data = await res.json();
        if (data.error) return;

        document.getElementById('outlier-q1').innerText = `$${data.q1.toLocaleString()}`;
        document.getElementById('outlier-median').innerText = `$${data.median.toLocaleString()}`;
        document.getElementById('outlier-q3').innerText = `$${data.q3.toLocaleString()}`;
        document.getElementById('outlier-threshold').innerText = `$${data.upper_bound.toLocaleString()}`;
        document.getElementById('outlier-max').innerText = `$${data.max.toLocaleString()}`;

        const badge = document.getElementById('outlier-badge');
        if (badge) {
            badge.innerText = `${data.outlier_count} Outliers Detected (${data.outlier_percentage}%)`;
        }

        // Render extreme records list
        const extremeTable = document.getElementById('outliers-extreme-tbody');
        if (extremeTable && data.extreme_records) {
            extremeTable.innerHTML = '';
            data.extreme_records.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:700; color:#38bdf8;">${r.Order_ID}</td>
                    <td>${r.Customer_Name}</td>
                    <td>${r.Product_Name}</td>
                    <td style="font-weight:700; color:#f43f5e;">$${r.Sales.toLocaleString()}</td>
                `;
                extremeTable.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Outliers error:", err);
    }
}

async function loadProductPerformance() {
    const params = new URLSearchParams();
    if (AppState.filters.region !== 'All') params.append('region', AppState.filters.region);
    if (AppState.filters.category !== 'All') params.append('category', AppState.filters.category);

    try {
        const res = await fetch(`/api/v1/product-performance?${params.toString()}`);
        const data = await res.json();
        if (data.products) {
            renderChart('productPerformanceChart', {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Products (Sales vs Profit)',
                        data: data.products,
                        backgroundColor: '#38bdf8',
                        borderColor: '#0284c7',
                        borderWidth: 1,
                        pointRadius: 6,
                        pointHoverRadius: 9
                    }]
                },
                options: {
                    ...darkChartDefaults,
                    plugins: {
                        ...darkChartDefaults.plugins,
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const p = ctx.raw;
                                    return `${p.name} (${p.category}): Sales $${p.x.toLocaleString()}, Profit $${p.y.toLocaleString()}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { title: { display: true, text: 'Total Revenue ($)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } },
                        y: { title: { display: true, text: 'Total Profit ($)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.04)' } }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Product performance error:", err);
    }
}

async function loadTopReturnProducts() {
    const params = new URLSearchParams();
    if (AppState.filters.region !== 'All') params.append('region', AppState.filters.region);
    if (AppState.filters.category !== 'All') params.append('category', AppState.filters.category);

    try {
        const res = await fetch(`/api/v1/top-return-products?${params.toString()}`);
        const data = await res.json();
        if (data.products) {
            renderChart('topReturnProductsChart', {
                type: 'bar',
                data: {
                    labels: data.products.map(p => p.length > 25 ? p.substring(0, 23) + '...' : p),
                    datasets: [{
                        label: 'Return Rate (%)',
                        data: data.return_rates,
                        backgroundColor: 'rgba(244, 63, 94, 0.75)',
                        borderColor: '#f43f5e',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    ...darkChartDefaults,
                    indexAxis: 'y'
                }
            });
        }
    } catch (err) {
        console.error("Top returns error:", err);
    }
}

// ==========================================
// TRANSACTIONS & DATA EXPLORER (CRUD)
// ==========================================
async function loadTransactions() {
    const state = AppState.transactions;
    const params = new URLSearchParams({
        limit: state.limit,
        offset: state.offset,
        sort_by: state.sort_by,
        sort_order: state.sort_order
    });

    if (state.search) params.append('search', state.search);
    if (state.region !== 'All') params.append('region', state.region);
    if (state.category !== 'All') params.append('category', state.category);

    try {
        const res = await fetch(`/api/v1/transactions?${params.toString()}`);
        const data = await res.json();
        if (data.items) {
            state.items = data.items;
            state.total = data.total;
            renderTransactionsTable();
            renderPagination();
        }
    } catch (err) {
        console.error("Transactions load error:", err);
    }
}

function renderTransactionsTable() {
    const tbody = document.getElementById('transactions-tbody');
    if (!tbody) return;

    const isAdmin = AppState.user && AppState.user.role === 'admin';
    tbody.innerHTML = '';

    if (AppState.transactions.items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${isAdmin ? 11 : 10}" style="text-align:center; padding:2rem; color:#64748b;">No transactions match criteria.</td></tr>`;
        return;
    }

    AppState.transactions.items.forEach(t => {
        const tr = document.createElement('tr');
        const isRet = String(t.Returned).toLowerCase() === 'yes';

        let actionCell = '';
        if (isAdmin) {
            actionCell = `
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="openEditTransactionModal('${t.Order_ID}')" title="Edit Record">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTransaction('${t.Order_ID}')" title="Delete Record">🗑️</button>
                </td>
            `;
        }

        tr.innerHTML = `
            <td style="font-weight:700; color:#38bdf8;">${t.Order_ID}</td>
            <td>${t.Order_Date || 'N/A'}</td>
            <td style="font-weight:600;">${t.Customer_Name || 'Unknown'}</td>
            <td>${t.Region || 'N/A'}</td>
            <td><span style="background:rgba(255,255,255,0.06); padding:0.15rem 0.5rem; border-radius:4px; font-size:0.75rem;">${t.Category || 'General'}</span></td>
            <td>${t.Product_Name || 'N/A'}</td>
            <td>${t.Quantity}</td>
            <td style="font-weight:700; color:#34d399;">$${parseFloat(t.Sales).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td style="color:${parseFloat(t.Profit) >= 0 ? '#38bdf8' : '#f43f5e'}; font-weight:600;">$${parseFloat(t.Profit).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td><span class="${isRet ? 'badge-returned-yes' : 'badge-returned-no'}">${isRet ? 'Returned' : 'Kept'}</span></td>
            ${actionCell}
        `;
        tbody.appendChild(tr);
    });
}

function renderPagination() {
    const state = AppState.transactions;
    const start = state.total === 0 ? 0 : state.offset + 1;
    const end = Math.min(state.offset + state.limit, state.total);
    const currentPage = Math.floor(state.offset / state.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(state.total / state.limit));

    const info = document.getElementById('pagination-info');
    if (info) info.innerText = `Showing ${start}–${end} of ${state.total.toLocaleString()} transactions`;

    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');

    if (prevBtn) prevBtn.disabled = state.offset === 0;
    if (nextBtn) nextBtn.disabled = end >= state.total;
}

function handleSearchTransactions(e) {
    AppState.transactions.search = e.target.value;
    AppState.transactions.offset = 0;
    loadTransactions();
}

function nextPage() {
    const state = AppState.transactions;
    if (state.offset + state.limit < state.total) {
        state.offset += state.limit;
        loadTransactions();
    }
}

function prevPage() {
    const state = AppState.transactions;
    if (state.offset - state.limit >= 0) {
        state.offset -= state.limit;
        loadTransactions();
    }
}

function exportCSV() {
    const params = new URLSearchParams();
    if (AppState.filters.region !== 'All') params.append('region', AppState.filters.region);
    if (AppState.filters.category !== 'All') params.append('category', AppState.filters.category);
    window.location.href = `/api/v1/export-csv?${params.toString()}`;
    showToast("Exporting filtered dataset to CSV...", 'info');
}

// Admin: Delete Transaction
async function deleteTransaction(orderId) {
    if (!confirm(`Are you sure you want to delete order ${orderId}? This cannot be undone.`)) return;

    try {
        const res = await fetch(`/api/v1/transactions/${orderId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast(`Order ${orderId} deleted successfully`, 'success');
            await loadTransactions();
            await refreshAllData();
        } else {
            showToast(data.error || "Delete failed", 'error');
        }
    } catch (err) {
        showToast("Error deleting transaction", 'error');
    }
}

// Admin: Add Transaction Modal & Submission
function openAddTransactionModal() {
    openModal('add-transaction-modal');
}

async function handleAddTransactionSubmit(e) {
    e.preventDefault();
    const payload = {
        Customer_Name: document.getElementById('add-customer-name').value,
        Order_Date: document.getElementById('add-order-date').value || new Date().toISOString().split('T')[0],
        Region: document.getElementById('add-region').value,
        Category: document.getElementById('add-category').value,
        Product_Name: document.getElementById('add-product-name').value,
        Quantity: parseFloat(document.getElementById('add-quantity').value || 1),
        Unit_Price: parseFloat(document.getElementById('add-price').value || 100),
        Discount: parseFloat(document.getElementById('add-discount').value || 0),
        Customer_Rating: parseFloat(document.getElementById('add-rating').value || 4.5),
        Returned: document.getElementById('add-returned').value
    };

    try {
        const res = await fetch('/api/v1/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast("New transaction recorded successfully!", 'success');
            closeModal('add-transaction-modal');
            e.target.reset();
            await loadTransactions();
            await refreshAllData();
        } else {
            showToast(data.error || "Failed to create transaction", 'error');
        }
    } catch (err) {
        showToast("Network error creating record", 'error');
    }
}

// Admin: Edit Transaction
function openEditTransactionModal(orderId) {
    const item = AppState.transactions.items.find(i => i.Order_ID === orderId);
    if (!item) return;

    document.getElementById('edit-order-id').value = item.Order_ID;
    document.getElementById('edit-customer-name').value = item.Customer_Name;
    document.getElementById('edit-product-name').value = item.Product_Name;
    document.getElementById('edit-quantity').value = item.Quantity;
    document.getElementById('edit-price').value = item.Unit_Price;
    document.getElementById('edit-discount').value = item.Discount;
    document.getElementById('edit-returned').value = item.Returned;

    openModal('edit-transaction-modal');
}

async function handleEditTransactionSubmit(e) {
    e.preventDefault();
    const orderId = document.getElementById('edit-order-id').value;
    const payload = {
        Customer_Name: document.getElementById('edit-customer-name').value,
        Product_Name: document.getElementById('edit-product-name').value,
        Quantity: parseFloat(document.getElementById('edit-quantity').value),
        Unit_Price: parseFloat(document.getElementById('edit-price').value),
        Discount: parseFloat(document.getElementById('edit-discount').value),
        Returned: document.getElementById('edit-returned').value
    };

    // Recalculate sales and profit
    const gross = payload.Quantity * payload.Unit_Price;
    payload.Sales = roundTo(gross * (1 - (payload.Discount / 100.0)), 2);
    payload.Profit = roundTo(payload.Sales * 0.18, 2);

    try {
        const res = await fetch(`/api/v1/transactions/${orderId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Order ${orderId} updated successfully`, 'success');
            closeModal('edit-transaction-modal');
            await loadTransactions();
            await refreshAllData();
        } else {
            showToast(data.error || "Update failed", 'error');
        }
    } catch (err) {
        showToast("Error updating transaction", 'error');
    }
}

function roundTo(n, digits) {
    const m = Math.pow(10, digits);
    return Math.round(n * m) / m;
}

// ==========================================
// ADMIN CONTROL CENTER
// ==========================================
async function loadAdminStats() {
    try {
        const res = await fetch('/api/v1/admin/stats');
        const data = await res.json();
        if (data.total_records !== undefined) {
            document.getElementById('admin-total-records').innerText = data.total_records.toLocaleString();
            document.getElementById('admin-db-size').innerText = `${data.database_size_mb} MB`;
            document.getElementById('admin-total-users').innerText = data.total_users;
            document.getElementById('admin-last-trained').innerText = data.last_trained || 'Available';
        }
    } catch (err) {
        console.error("Admin stats error:", err);
    }
}

async function handleCSVUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file-input');
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a CSV file first.", 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const btn = document.getElementById('btn-upload-submit');
    if (btn) btn.innerHTML = '<span>⏳</span> Processing CSV & Retraining...';

    try {
        const res = await fetch('/api/v1/upload-csv', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fileInput.value = '';
            await loadAdminStats();
            await refreshAllData();
            await loadMLStudioData();
        } else {
            showToast(data.error || "Upload failed", 'error');
        }
    } catch (err) {
        showToast("Error during file upload", 'error');
    } finally {
        if (btn) btn.innerHTML = '<span>📤</span> Upload Dataset';
    }
}

// ==========================================
// MODAL DIALOGS CONTROLLER
// ==========================================
function setupModals() {
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('open');
            }
        });
    });

    document.querySelectorAll('.modal-close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) modal.classList.remove('open');
        });
    });

    // Auth Switcher tabs inside Auth Modal
    const authTabLogin = document.getElementById('auth-tab-login');
    const authTabRegister = document.getElementById('auth-tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');

    if (authTabLogin && authTabRegister) {
        authTabLogin.addEventListener('click', () => {
            authTabLogin.classList.add('active');
            authTabRegister.classList.remove('active');
            formLogin.style.display = 'block';
            formRegister.style.display = 'none';
        });

        authTabRegister.addEventListener('click', () => {
            authTabRegister.classList.add('active');
            authTabLogin.classList.remove('active');
            formLogin.style.display = 'none';
            formRegister.style.display = 'block';
        });
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('open');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('open');
}
