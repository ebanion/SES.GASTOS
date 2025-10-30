/**
 * Analytics Advanced Dashboard
 * Power BI-inspired interface with advanced visualizations
 */

const API_BASE = '/analytics';
let authToken = null;
let charts = {};
let dashboardData = null;

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    initAuth();
    initNavigation();
    loadAllData();
    
    // Event listeners
    document.getElementById('fiscal-simulate-btn')?.addEventListener('click', runFiscalSimulation);
    
    // Auto-refresh every 5 minutes
    setInterval(loadAllData, 5 * 60 * 1000);
}

/**
 * Authentication
 */
function initAuth() {
    authToken = localStorage.getItem('access_token') || getCookie('access_token');
    
    if (!authToken) {
        console.warn('No authentication token found');
        // Fallback: try to get from URL params or redirect to login
    }
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

/**
 * Navigation
 */
function initNavigation() {
    document.querySelectorAll('.sidebar-menu-item').forEach(item => {
        item.addEventListener('click', function() {
            const pageName = this.dataset.page;
            switchPage(pageName);
        });
    });
}

function switchPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    // Show selected page
    const selectedPage = document.getElementById(`page-${pageName}`);
    if (selectedPage) {
        selectedPage.style.display = 'block';
    }
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-menu-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    
    // Load page-specific data if needed
    if (pageName === 'fiscal') {
        loadFiscalData();
    } else if (pageName === 'expenses') {
        loadExpenseAnalysis();
    } else if (pageName === 'performance') {
        loadPerformanceData();
    }
}

/**
 * API Helpers
 */
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function apiPost(endpoint, params = {}) {
    try {
        const url = new URL(`${window.location.origin}${API_BASE}${endpoint}`);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error posting to ${endpoint}:`, error);
        return null;
    }
}

/**
 * Load All Data
 */
async function loadAllData() {
    try {
        const data = await apiGet('/dashboard');
        
        if (data) {
            dashboardData = data;
            updateLastUpdate();
            
            // Update Overview page
            updateHealthStatus(data.financial_health);
            updateHeroKPIs(data.kpis, data.financial_health);
            updateAlerts(data.alerts);
            createRevenueTrendChart(data);
            
            // Cache for other pages
            window.analyticsData = data;
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

/**
 * Update Last Update Time
 */
function updateLastUpdate() {
    const now = new Date();
    const formatted = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('last-update').textContent = formatted;
}

/**
 * Update Hero Health Status
 */
function updateHealthStatus(health) {
    const heroHealth = document.getElementById('hero-health');
    const heroScore = document.getElementById('hero-score');
    const heroMessage = document.getElementById('health-hero-message');
    const heroMargin = document.getElementById('hero-margin');
    const heroOccupancy = document.getElementById('hero-occupancy');
    const heroProfit = document.getElementById('hero-profit');
    
    // Update circle color
    heroHealth.className = `health-circle ${health.status}`;
    
    // Update score
    heroScore.textContent = health.score;
    
    // Update message
    heroMessage.textContent = health.message;
    
    // Update metrics
    heroMargin.textContent = `${health.margin_percent.toFixed(1)}%`;
    heroOccupancy.textContent = `${health.occupancy_rate.toFixed(1)}%`;
    heroProfit.textContent = `€${health.net_profit.toLocaleString('es-ES', {minimumFractionDigits: 2})}`;
}

/**
 * Update Hero KPIs
 */
function updateHeroKPIs(kpis, health) {
    // ADR
    document.getElementById('kpi-adr').textContent = `€${kpis.adr.toFixed(2)}`;
    
    // Occupancy
    document.getElementById('kpi-occupancy').textContent = `${kpis.occupancy_rate.toFixed(1)}%`;
    
    // RevPAR
    document.getElementById('kpi-revpar').textContent = `€${kpis.revpar.toFixed(2)}`;
    
    // Profit
    document.getElementById('kpi-profit').textContent = `€${health.net_profit.toLocaleString('es-ES', {minimumFractionDigits: 2})}`;
    
    // Update badges (placeholder - would need historical data for real trends)
    updateBadge('kpi-adr-badge', 5.2);
    updateBadge('kpi-occupancy-badge', 8.7);
    updateBadge('kpi-revpar-badge', 12.3);
    updateBadge('kpi-profit-badge', 15.8);
}

function updateBadge(elementId, changePercent) {
    const badge = document.getElementById(elementId);
    if (!badge) return;
    
    const isPositive = changePercent >= 0;
    const icon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
    const className = isPositive ? 'metric-badge positive' : 'metric-badge negative';
    
    badge.className = className;
    badge.innerHTML = `<i class="fas ${icon} mr-1"></i> ${Math.abs(changePercent).toFixed(1)}%`;
}

/**
 * Create Revenue Trend Chart
 */
function createRevenueTrendChart(data) {
    const ctx = document.getElementById('revenue-trend-chart');
    if (!ctx) return;
    
    if (charts.revenueTrend) {
        charts.revenueTrend.destroy();
    }
    
    // Mock data for last 6 months (would come from backend in production)
    const labels = ['Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    const incomeData = [4200, 5800, 4500, 5100, data.income_comparison?.current_month || 5400, 0];
    const expenseData = [2300, 3100, 2600, 2800, data.financial_health?.total_expenses || 2970, 0];
    
    charts.revenueTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ingresos',
                    data: incomeData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: 'Gastos',
                    data: expenseData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 13,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': €' + context.parsed.y.toLocaleString('es-ES', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '€' + value.toLocaleString('es-ES');
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Update Alerts
 */
function updateAlerts(alerts) {
    const alertsGrid = document.getElementById('alerts-grid');
    const alertsCount = document.getElementById('alerts-count');
    
    if (!alerts || alerts.length === 0) {
        alertsGrid.innerHTML = '<p class="text-gray-500 text-center py-8 col-span-2">No hay alertas activas 🎉</p>';
        alertsCount.textContent = '0 activas';
        return;
    }
    
    alertsCount.textContent = `${alerts.length} activa${alerts.length !== 1 ? 's' : ''}`;
    
    alertsGrid.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <div class="flex items-start">
                <span class="text-3xl mr-4">${alert.icon}</span>
                <div class="flex-1">
                    <h4 class="font-bold text-gray-900 mb-1">${alert.title}</h4>
                    <p class="text-sm text-gray-600 mb-2">${alert.message}</p>
                    ${alert.due_date ? `
                        <span class="inline-block px-3 py-1 rounded-full bg-white text-xs font-semibold text-gray-700">
                            <i class="far fa-calendar mr-1"></i>
                            ${formatDate(alert.due_date)}
                        </span>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Load Expense Analysis
 */
async function loadExpenseAnalysis() {
    const data = await apiGet('/expense-analysis');
    
    if (!data || data.length === 0) return;
    
    createExpenseDonutChart(data);
    createExpenseComparisonChart(data);
    displayExpenseRecommendations(data);
}

/**
 * Create Expense Donut Chart
 */
function createExpenseDonutChart(expenses) {
    const ctx = document.getElementById('expense-donut-chart');
    if (!ctx) return;
    
    if (charts.expenseDonut) {
        charts.expenseDonut.destroy();
    }
    
    const colors = [
        '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', 
        '#ef4444', '#ec4899', '#14b8a6', '#f97316'
    ];
    
    charts.expenseDonut = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: expenses.map(e => e.category),
            datasets: [{
                data: expenses.map(e => e.total_amount),
                backgroundColor: colors,
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 16,
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                            
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                const percent = ((value / total) * 100).toFixed(1);
                                
                                return {
                                    text: `${label} (${percent}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percent = ((value / total) * 100).toFixed(1);
                            return `€${value.toLocaleString('es-ES', {minimumFractionDigits: 2})} (${percent}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create Expense Comparison Chart
 */
function createExpenseComparisonChart(expenses) {
    const ctx = document.getElementById('expense-comparison-chart');
    if (!ctx) return;
    
    if (charts.expenseComparison) {
        charts.expenseComparison.destroy();
    }
    
    charts.expenseComparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: expenses.map(e => e.category),
            datasets: [
                {
                    label: 'Tu %',
                    data: expenses.map(e => e.percent_of_income),
                    backgroundColor: expenses.map(e => 
                        e.status === 'optimal' ? '#10b981' : 
                        e.status === 'high' ? '#f59e0b' : '#ef4444'
                    ),
                    borderRadius: 6,
                    borderSkipped: false
                },
                {
                    label: 'Benchmark',
                    data: expenses.map(e => e.benchmark_percent),
                    backgroundColor: '#cbd5e1',
                    borderRadius: 6,
                    borderSkipped: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 16,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.x.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Display Expense Recommendations
 */
function displayExpenseRecommendations(expenses) {
    const container = document.getElementById('expense-recommendations');
    if (!container) return;
    
    const statusConfig = {
        'optimal': { icon: '✅', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
        'high': { icon: '⚠️', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
        'very_high': { icon: '🚨', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
    };
    
    container.innerHTML = `
        <div class="space-y-4">
            ${expenses.map(expense => {
                const config = statusConfig[expense.status];
                return `
                    <div class="p-5 rounded-xl border-2 ${config.border} ${config.bg}">
                        <div class="flex items-start justify-between">
                            <div class="flex items-start flex-1">
                                <span class="text-3xl mr-4">${config.icon}</span>
                                <div class="flex-1">
                                    <h4 class="font-bold text-gray-900 mb-1">${expense.category}</h4>
                                    <p class="text-sm text-gray-700 mb-3">${expense.recommendation}</p>
                                    
                                    <div class="flex flex-wrap gap-3 text-xs">
                                        <span class="px-3 py-1 rounded-full bg-white border border-gray-200">
                                            <strong>Tu gasto:</strong> ${expense.percent_of_income.toFixed(1)}%
                                        </span>
                                        <span class="px-3 py-1 rounded-full bg-white border border-gray-200">
                                            <strong>Benchmark:</strong> ${expense.benchmark_percent.toFixed(1)}%
                                        </span>
                                        <span class="px-3 py-1 rounded-full bg-white border border-gray-200">
                                            <strong>Total:</strong> €${expense.total_amount.toLocaleString('es-ES', {minimumFractionDigits: 2})}
                                        </span>
                                        <span class="px-3 py-1 rounded-full bg-white border border-gray-200">
                                            <strong>Transacciones:</strong> ${expense.transaction_count}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="ml-4">
                                <div class="text-right">
                                    <p class="text-2xl font-bold ${config.color}">
                                        ${expense.percent_of_income.toFixed(1)}%
                                    </p>
                                    <p class="text-xs text-gray-500">sobre ingresos</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Load Fiscal Data
 */
async function loadFiscalData() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentQuarter = Math.floor(now.getMonth() / 3) + 1;
    
    const [ivaData, irpfData] = await Promise.all([
        apiGet(`/fiscal/iva/${currentYear}/${currentQuarter}`),
        apiGet(`/fiscal/irpf/${currentYear}/${currentQuarter}`)
    ]);
    
    if (ivaData) displayFiscalIVA(ivaData);
    if (irpfData) displayFiscalIRPF(irpfData);
}

/**
 * Display Fiscal IVA
 */
function displayFiscalIVA(data) {
    const container = document.getElementById('fiscal-iva-detail');
    if (!container) return;
    
    const daysUntilDue = data.days_until_due;
    const urgencyColor = daysUntilDue < 0 ? 'red' : daysUntilDue < 15 ? 'orange' : 'green';
    const urgencyText = daysUntilDue < 0 ? 'Vencido' : `${daysUntilDue} días`;
    
    container.innerHTML = `
        <div class="space-y-5">
            <!-- Period -->
            <div class="p-4 rounded-xl bg-gray-50">
                <p class="text-sm text-gray-600 mb-1">Periodo</p>
                <p class="text-lg font-bold text-gray-900">${data.quarter_label}</p>
                <p class="text-sm text-gray-500">${formatDate(data.start_date)} - ${formatDate(data.end_date)}</p>
            </div>
            
            <!-- Calculations -->
            <div>
                <div class="flex justify-between items-center mb-3">
                    <span class="text-gray-600">IVA Repercutido (10%)</span>
                    <span class="font-bold text-gray-900">€${data.iva_repercutido.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="flex justify-between items-center mb-3">
                    <span class="text-gray-600">IVA Soportado</span>
                    <span class="font-bold text-red-600">-€${data.iva_soportado.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                </div>
                
                <hr class="my-4">
                
                <div class="flex justify-between items-center">
                    <span class="text-lg font-bold text-gray-900">A Pagar</span>
                    <span class="text-3xl font-black ${data.iva_to_pay > 0 ? 'text-blue-600' : 'text-green-600'}">
                        €${Math.abs(data.iva_to_pay).toLocaleString('es-ES', {minimumFractionDigits: 2})}
                    </span>
                </div>
            </div>
            
            <!-- Due Date -->
            <div class="p-4 rounded-xl border-2 border-${urgencyColor}-200 bg-${urgencyColor}-50">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600 mb-1">Vencimiento Modelo 303</p>
                        <p class="font-bold text-gray-900">${formatDate(data.due_date)}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-${urgencyColor}-600">${urgencyText}</p>
                        <p class="text-xs text-gray-600">restantes</p>
                    </div>
                </div>
            </div>
            
            <button class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-all">
                <i class="fas fa-download mr-2"></i>
                Generar Borrador Modelo 303
            </button>
        </div>
    `;
}

/**
 * Display Fiscal IRPF
 */
function displayFiscalIRPF(data) {
    const container = document.getElementById('fiscal-irpf-detail');
    if (!container) return;
    
    const daysUntilDue = data.days_until_due;
    const urgencyColor = daysUntilDue < 0 ? 'red' : daysUntilDue < 15 ? 'orange' : 'green';
    const urgencyText = daysUntilDue < 0 ? 'Vencido' : `${daysUntilDue} días`;
    
    container.innerHTML = `
        <div class="space-y-5">
            <!-- Period -->
            <div class="p-4 rounded-xl bg-gray-50">
                <p class="text-sm text-gray-600 mb-1">Periodo</p>
                <p class="text-lg font-bold text-gray-900">${data.quarter_label}</p>
                <p class="text-xs text-gray-500 mt-1">Régimen: ${data.regime === 'general' ? 'General' : 'Módulos'}</p>
            </div>
            
            <!-- Calculations -->
            <div>
                <div class="flex justify-between items-center mb-3">
                    <span class="text-gray-600">Ingresos totales</span>
                    <span class="font-bold text-gray-900">€${data.total_income.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="flex justify-between items-center mb-3">
                    <span class="text-gray-600">Gastos deducibles</span>
                    <span class="font-bold text-red-600">-€${data.total_expenses.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="flex justify-between items-center mb-3 pb-3 border-b-2 border-gray-200">
                    <span class="text-gray-600">Beneficio neto</span>
                    <span class="font-bold text-green-600">€${data.net_income.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                </div>
                
                <div class="flex justify-between items-center">
                    <span class="text-lg font-bold text-gray-900">Pago Fraccionado</span>
                    <span class="text-3xl font-black text-green-600">
                        €${data.quarterly_payment.toLocaleString('es-ES', {minimumFractionDigits: 2})}
                    </span>
                </div>
                <p class="text-xs text-gray-500 mt-1 text-right">
                    IRPF ${data.irpf_rate_percent}% del beneficio neto
                </p>
            </div>
            
            <!-- Due Date -->
            <div class="p-4 rounded-xl border-2 border-${urgencyColor}-200 bg-${urgencyColor}-50">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600 mb-1">Vencimiento Modelo 130</p>
                        <p class="font-bold text-gray-900">${formatDate(data.due_date)}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-${urgencyColor}-600">${urgencyText}</p>
                        <p class="text-xs text-gray-600">restantes</p>
                    </div>
                </div>
            </div>
            
            <button class="w-full py-3 rounded-xl bg-green-600 hover:bg-green-700 text-white font-semibold transition-all">
                <i class="fas fa-download mr-2"></i>
                Generar Borrador Modelo 130
            </button>
        </div>
    `;
}

/**
 * Run Fiscal Simulation
 */
async function runFiscalSimulation() {
    const income = parseFloat(document.getElementById('fiscal-sim-income').value);
    const expenses = parseFloat(document.getElementById('fiscal-sim-expenses').value);
    
    if (isNaN(income) || isNaN(expenses) || income <= 0 || expenses < 0) {
        alert('Por favor, introduce valores válidos');
        return;
    }
    
    const data = await apiPost('/fiscal/simulate', {
        projected_annual_income: income,
        projected_annual_expenses: expenses
    });
    
    if (data) {
        displayFiscalSimulation(data);
    }
}

/**
 * Display Fiscal Simulation Results
 */
function displayFiscalSimulation(data) {
    const container = document.getElementById('fiscal-simulation-results');
    if (!container) return;
    
    const scenarios = data.scenarios;
    
    container.innerHTML = `
        <!-- Summary -->
        <div class="p-6 rounded-xl bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 mb-8">
            <div class="grid grid-cols-3 gap-6 text-center">
                <div>
                    <p class="text-sm text-gray-600 mb-1">Ingresos Proyectados</p>
                    <p class="text-2xl font-bold text-gray-900">€${data.projected_annual_income.toLocaleString('es-ES')}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600 mb-1">Gastos Proyectados</p>
                    <p class="text-2xl font-bold text-gray-900">€${data.projected_annual_expenses.toLocaleString('es-ES')}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600 mb-1">Beneficio Proyectado</p>
                    <p class="text-2xl font-bold text-green-600">€${data.projected_net_income.toLocaleString('es-ES')}</p>
                </div>
            </div>
        </div>
        
        <!-- Scenarios Comparison -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            ${Object.entries(scenarios).map(([key, scenario]) => {
                const isRecommended = scenario.recommended;
                return `
                    <div class="power-card ${isRecommended ? 'ring-4 ring-purple-600' : ''}">
                        ${isRecommended ? `
                            <div class="mb-3 px-3 py-1 rounded-full bg-purple-600 text-white text-sm font-bold inline-block">
                                ✨ RECOMENDADO
                            </div>
                        ` : ''}
                        
                        <h4 class="text-lg font-bold text-gray-900 mb-5">${scenario.name}</h4>
                        
                        <div class="space-y-3 mb-5">
                            ${Object.entries(scenario).filter(([k]) => !['name', 'recommended', 'note', 'net_after_tax', 'total_tax', 'effective_rate'].includes(k)).map(([k, v]) => `
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-600 capitalize">${k.replace(/_/g, ' ')}</span>
                                    <span class="font-semibold text-gray-900">€${typeof v === 'number' ? v.toLocaleString('es-ES', {minimumFractionDigits: 2}) : v}</span>
                                </div>
                            `).join('')}
                            
                            <hr class="my-3">
                            
                            <div class="flex justify-between">
                                <span class="font-bold text-gray-900">Total Impuestos</span>
                                <span class="font-bold text-red-600 text-lg">€${scenario.total_tax.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                            </div>
                            
                            <div class="flex justify-between">
                                <span class="font-bold text-gray-900">Neto Final</span>
                                <span class="font-bold text-green-600 text-xl">€${scenario.net_after_tax.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                            </div>
                            
                            <div class="mt-4 pt-3 border-t-2 border-gray-200">
                                <div class="flex justify-between">
                                    <span class="text-sm text-gray-600">Tipo Efectivo</span>
                                    <span class="font-bold text-purple-600">${scenario.effective_rate.toFixed(2)}%</span>
                                </div>
                            </div>
                        </div>
                        
                        ${scenario.note ? `
                            <p class="text-xs text-gray-500 italic p-3 bg-gray-50 rounded-lg">
                                💡 ${scenario.note}
                            </p>
                        ` : ''}
                    </div>
                `;
            }).join('')}
        </div>
        
        <!-- Recommendation -->
        <div class="p-6 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white">
            <div class="flex items-start">
                <i class="fas fa-lightbulb text-3xl mr-4 mt-1"></i>
                <div>
                    <h4 class="font-bold text-xl mb-2">Recomendación Personalizada</h4>
                    <p class="text-lg opacity-95">${data.recommendation}</p>
                </div>
            </div>
        </div>
    `;
}

/**
 * Load Performance Data
 */
async function loadPerformanceData() {
    // Get current month dates
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    const data = await apiGet(`/year-over-year?start_date=${formatDateAPI(start)}&end_date=${formatDateAPI(end)}`);
    
    if (data) {
        displayYearOverYear(data);
    }
}

/**
 * Display Year over Year
 */
function displayYearOverYear(data) {
    const container = document.getElementById('yoy-comparison');
    if (!container) return;
    
    const current = data.current_period;
    const previous = data.previous_period;
    const variations = data.variations;
    
    const metrics = [
        { key: 'income', label: 'Ingresos', icon: 'fa-money-bill-wave', color: 'blue' },
        { key: 'expenses', label: 'Gastos', icon: 'fa-wallet', color: 'red' },
        { key: 'profit', label: 'Beneficio', icon: 'fa-coins', color: 'green' },
        { key: 'occupancy_rate', label: 'Ocupación', icon: 'fa-bed', color: 'purple', suffix: '%' },
        { key: 'adr', label: 'ADR', icon: 'fa-euro-sign', color: 'orange', prefix: '€' }
    ];
    
    container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            ${metrics.map(metric => {
                const currentValue = current[metric.key];
                const previousValue = previous[metric.key];
                const change = variations[`${metric.key}_change_percent`];
                const isPositive = change >= 0;
                
                return `
                    <div class="stat-item">
                        <div class="flex items-center justify-between mb-3">
                            <i class="fas ${metric.icon} text-${metric.color}-600 text-xl"></i>
                            <span class="${isPositive ? 'metric-badge positive' : 'metric-badge negative'}">
                                ${isPositive ? '+' : ''}${change.toFixed(1)}%
                            </span>
                        </div>
                        <p class="text-xs text-gray-500 mb-1">${metric.label}</p>
                        <p class="text-2xl font-bold text-gray-900">
                            ${metric.prefix || ''}${typeof currentValue === 'number' ? currentValue.toLocaleString('es-ES', {minimumFractionDigits: metric.suffix ? 1 : 2}) : currentValue}${metric.suffix || ''}
                        </p>
                        <p class="text-xs text-gray-500 mt-1">
                            vs. ${metric.prefix || ''}${typeof previousValue === 'number' ? previousValue.toLocaleString('es-ES', {minimumFractionDigits: metric.suffix ? 1 : 2}) : previousValue}${metric.suffix || ''}
                        </p>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Utilities
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateAPI(date) {
    return date.toISOString().split('T')[0];
}
