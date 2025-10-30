/**
 * Analytics Dashboard JavaScript
 * Maneja la carga de datos, gráficos y navegación
 */

// Configuration
const IS_DEMO = window.location.pathname.includes('/demo');
const API_BASE = IS_DEMO ? '/analytics/demo' : '/analytics';
let authToken = null;
let charts = {};

// Show demo banner if in demo mode
if (IS_DEMO) {
    document.addEventListener('DOMContentLoaded', function() {
        const banner = document.createElement('div');
        banner.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; background: linear-gradient(90deg, #8b5cf6, #6d28d9); color: white; padding: 12px; text-align: center; z-index: 9999; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2);';
        banner.innerHTML = '🎨 MODO DEMO - Datos de ejemplo | <a href="/" style="color: white; text-decoration: underline; margin-left: 12px;">Volver al inicio</a>';
        document.body.prepend(banner);
        document.body.style.paddingTop = '48px';
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initAuth();
    initTabNavigation();
    loadDashboard();
    
    // Simulator button
    document.getElementById('simulate-btn')?.addEventListener('click', runSimulation);
});

/**
 * Authentication
 */
function initAuth() {
    // Get token from localStorage or cookie
    authToken = localStorage.getItem('access_token') || getCookie('access_token');
    
    if (!authToken) {
        // If no token, redirect to login
        console.warn('No authentication token found');
        // window.location.href = '/login';
    }
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

/**
 * API Calls
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
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function apiPost(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error posting to ${endpoint}:`, error);
        return null;
    }
}

/**
 * Main Dashboard Load
 */
async function loadDashboard() {
    showLoading();
    
    try {
        const data = await apiGet('/dashboard');
        
        if (data) {
            updatePeriod(data.period);
            updateFinancialHealth(data.financial_health);
            updateKPIs(data.kpis);
            updateIncomeComparison(data.income_comparison);
            updateAlerts(data.alerts);
            
            // Load detailed data for other tabs
            loadExpenseAnalysis();
            loadFiscalData();
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Error cargando el dashboard');
    }
    
    hideLoading();
}

/**
 * Update Period Info
 */
function updatePeriod(period) {
    document.getElementById('current-period').textContent = period.label;
}

/**
 * Update Financial Health
 */
function updateFinancialHealth(health) {
    const badge = document.getElementById('health-badge');
    const score = document.getElementById('health-score');
    const statusText = document.getElementById('health-status-text');
    const message = document.getElementById('health-message');
    
    // Update score
    score.textContent = health.score;
    
    // Update status color
    badge.className = `health-badge ${health.status}`;
    
    // Update status text
    const statusLabels = {
        'green': 'Excelente',
        'yellow': 'Moderado',
        'red': 'Crítico'
    };
    statusText.textContent = statusLabels[health.status] || 'Analizando...';
    
    // Update message
    message.textContent = health.message;
    
    // Update metrics
    document.getElementById('health-margin').textContent = `${health.margin_percent.toFixed(1)}%`;
    document.getElementById('health-occupancy').textContent = `${health.occupancy_rate.toFixed(1)}%`;
    document.getElementById('health-expenses').textContent = `${health.expense_ratio.toFixed(1)}%`;
}

/**
 * Update KPIs
 */
function updateKPIs(kpis) {
    // ADR
    document.getElementById('adr-value').textContent = `€${kpis.adr.toFixed(2)}`;
    
    // Occupancy
    document.getElementById('occupancy-value').textContent = `${kpis.occupancy_rate.toFixed(1)}%`;
    
    // RevPAR
    document.getElementById('revpar-value').textContent = `€${kpis.revpar.toFixed(2)}`;
    
    // TODO: Calculate trends (would need historical data)
    // For now, set placeholder trends
}

/**
 * Update Income Comparison
 */
function updateIncomeComparison(comparison) {
    const currentIncome = document.getElementById('current-income');
    const previousIncome = document.getElementById('previous-income');
    const incomeChange = document.getElementById('income-change');
    
    currentIncome.textContent = `€${comparison.current_month.toLocaleString('es-ES', {minimumFractionDigits: 2})}`;
    previousIncome.textContent = `€${comparison.previous_month.toLocaleString('es-ES', {minimumFractionDigits: 2})}`;
    
    const changePercent = comparison.change_percent;
    const isPositive = changePercent >= 0;
    const icon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
    const colorClass = isPositive ? 'trend-up' : 'trend-down';
    
    incomeChange.innerHTML = `
        <span class="${colorClass}">
            <i class="fas ${icon}"></i> ${Math.abs(changePercent).toFixed(1)}%
        </span>
    `;
    
    // Create income chart
    createIncomeChart(comparison);
}

/**
 * Create Income Chart
 */
function createIncomeChart(data) {
    const ctx = document.getElementById('income-chart');
    if (!ctx) return;
    
    if (charts.income) {
        charts.income.destroy();
    }
    
    charts.income = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mes Anterior', 'Mes Actual'],
            datasets: [{
                label: 'Ingresos',
                data: [data.previous_month, data.current_month],
                backgroundColor: [
                    'rgba(156, 163, 175, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ],
                borderColor: [
                    'rgba(156, 163, 175, 1)',
                    'rgba(139, 92, 246, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8
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
                    callbacks: {
                        label: function(context) {
                            return '€' + context.parsed.y.toLocaleString('es-ES', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '€' + value.toLocaleString('es-ES');
                        }
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
    const alertsList = document.getElementById('alerts-list');
    const alertDot = document.getElementById('alert-dot');
    
    if (!alerts || alerts.length === 0) {
        alertsList.innerHTML = '<p class="text-gray-500 text-center py-4">No hay alertas activas</p>';
        alertDot.style.display = 'none';
        return;
    }
    
    alertDot.style.display = 'block';
    
    const severityClasses = {
        'error': 'border-red-500 bg-red-50',
        'warning': 'border-orange-500 bg-orange-50',
        'info': 'border-blue-500 bg-blue-50',
        'success': 'border-green-500 bg-green-50'
    };
    
    alertsList.innerHTML = alerts.map(alert => `
        <div class="p-4 rounded-xl border-l-4 ${severityClasses[alert.severity] || 'border-gray-500 bg-gray-50'}">
            <div class="flex items-start">
                <span class="text-2xl mr-3">${alert.icon}</span>
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-800 mb-1">${alert.title}</h4>
                    <p class="text-sm text-gray-600">${alert.message}</p>
                    ${alert.due_date ? `<p class="text-xs text-gray-500 mt-2">Vence: ${formatDate(alert.due_date)}</p>` : ''}
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
    
    if (!data) return;
    
    // Create pie chart
    createExpensesPieChart(data);
    
    // Create benchmark chart
    createExpensesBenchmarkChart(data);
    
    // Display recommendations
    displayRecommendations(data);
}

/**
 * Create Expenses Pie Chart
 */
function createExpensesPieChart(expenses) {
    const ctx = document.getElementById('expenses-pie-chart');
    if (!ctx) return;
    
    if (charts.expensesPie) {
        charts.expensesPie.destroy();
    }
    
    const colors = [
        'rgba(139, 92, 246, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(236, 72, 153, 0.8)'
    ];
    
    charts.expensesPie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: expenses.map(e => e.category),
            datasets: [{
                data: expenses.map(e => e.total_amount),
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: €${value.toLocaleString('es-ES', {minimumFractionDigits: 2})}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create Expenses Benchmark Chart
 */
function createExpensesBenchmarkChart(expenses) {
    const ctx = document.getElementById('expenses-benchmark-chart');
    if (!ctx) return;
    
    if (charts.expensesBenchmark) {
        charts.expensesBenchmark.destroy();
    }
    
    charts.expensesBenchmark = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: expenses.map(e => e.category),
            datasets: [
                {
                    label: 'Tu %',
                    data: expenses.map(e => e.percent_of_income),
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Benchmark %',
                    data: expenses.map(e => e.benchmark_percent),
                    backgroundColor: 'rgba(156, 163, 175, 0.5)',
                    borderColor: 'rgba(156, 163, 175, 1)',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Display Recommendations
 */
function displayRecommendations(expenses) {
    const recommendationsList = document.getElementById('recommendations-list');
    if (!recommendationsList) return;
    
    const statusIcons = {
        'optimal': '✅',
        'high': '⚠️',
        'very_high': '🚨'
    };
    
    recommendationsList.innerHTML = expenses.map(expense => `
        <div class="recommendation-card p-4 rounded-xl">
            <div class="flex items-start">
                <span class="text-2xl mr-3">${statusIcons[expense.status]}</span>
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-800 mb-1">${expense.category}</h4>
                    <p class="text-sm text-gray-600 mb-2">${expense.recommendation}</p>
                    <div class="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Tu gasto: ${expense.percent_of_income.toFixed(1)}%</span>
                        <span>•</span>
                        <span>Benchmark: ${expense.benchmark_percent.toFixed(1)}%</span>
                        <span>•</span>
                        <span>Total: €${expense.total_amount.toLocaleString('es-ES')}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Load Fiscal Data
 */
async function loadFiscalData() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentQuarter = Math.floor((now.getMonth()) / 3) + 1;
    
    // Load IVA
    const ivaData = await apiGet(`/fiscal/iva/${currentYear}/${currentQuarter}`);
    if (ivaData) {
        displayIVAData(ivaData);
    }
    
    // Load IRPF
    const irpfData = await apiGet(`/fiscal/irpf/${currentYear}/${currentQuarter}`);
    if (irpfData) {
        displayIRPFData(irpfData);
    }
}

/**
 * Display IVA Data
 */
function displayIVAData(data) {
    const container = document.getElementById('iva-calculator');
    if (!container) return;
    
    const daysColor = data.days_until_due < 0 ? 'text-red-600' : data.days_until_due < 15 ? 'text-orange-600' : 'text-green-600';
    
    container.innerHTML = `
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Trimestre</span>
                <span class="text-lg font-bold text-gray-800">${data.quarter_label}</span>
            </div>
            <hr>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">IVA Repercutido</span>
                <span class="font-semibold text-gray-800">€${data.iva_repercutido.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">IVA Soportado</span>
                <span class="font-semibold text-gray-800">-€${data.iva_soportado.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
            </div>
            <hr>
            <div class="flex justify-between items-center">
                <span class="text-lg font-semibold text-gray-800">A Pagar</span>
                <span class="text-2xl font-bold ${data.iva_to_pay > 0 ? 'text-red-600' : 'text-green-600'}">
                    €${Math.abs(data.iva_to_pay).toLocaleString('es-ES', {minimumFractionDigits: 2})}
                </span>
            </div>
            <div class="mt-4 p-3 rounded-xl bg-gray-50">
                <p class="text-sm text-gray-600 mb-1">Vencimiento</p>
                <p class="font-semibold text-gray-800">${formatDate(data.due_date)}</p>
                <p class="text-sm ${daysColor} mt-1">
                    ${data.is_overdue ? '⚠️ Vencido' : `${data.days_until_due} días restantes`}
                </p>
            </div>
        </div>
    `;
}

/**
 * Display IRPF Data
 */
function displayIRPFData(data) {
    const container = document.getElementById('irpf-calculator');
    if (!container) return;
    
    const daysColor = data.days_until_due < 0 ? 'text-red-600' : data.days_until_due < 15 ? 'text-orange-600' : 'text-green-600';
    
    container.innerHTML = `
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Trimestre</span>
                <span class="text-lg font-bold text-gray-800">${data.quarter_label}</span>
            </div>
            <hr>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Ingresos</span>
                <span class="font-semibold text-gray-800">€${data.total_income.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Gastos</span>
                <span class="font-semibold text-gray-800">-€${data.total_expenses.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Beneficio Neto</span>
                <span class="font-semibold text-gray-800">€${data.net_income.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
            </div>
            <hr>
            <div class="flex justify-between items-center">
                <span class="text-lg font-semibold text-gray-800">IRPF a Pagar</span>
                <span class="text-2xl font-bold text-orange-600">
                    €${data.quarterly_payment.toLocaleString('es-ES', {minimumFractionDigits: 2})}
                </span>
            </div>
            <div class="mt-4 p-3 rounded-xl bg-gray-50">
                <p class="text-sm text-gray-600 mb-1">Vencimiento</p>
                <p class="font-semibold text-gray-800">${formatDate(data.due_date)}</p>
                <p class="text-sm ${daysColor} mt-1">
                    ${data.is_overdue ? '⚠️ Vencido' : `${data.days_until_due} días restantes`}
                </p>
            </div>
        </div>
    `;
}

/**
 * Run Simulation
 */
async function runSimulation() {
    const income = parseFloat(document.getElementById('sim-income').value);
    const expenses = parseFloat(document.getElementById('sim-expenses').value);
    
    if (isNaN(income) || isNaN(expenses)) {
        alert('Por favor, introduce valores válidos');
        return;
    }
    
    const data = await apiPost(`/fiscal/simulate?projected_annual_income=${income}&projected_annual_expenses=${expenses}`, {});
    
    if (data) {
        displaySimulationResults(data);
    }
}

/**
 * Display Simulation Results
 */
function displaySimulationResults(data) {
    const container = document.getElementById('simulation-results');
    if (!container) return;
    
    const scenarios = data.scenarios;
    
    container.innerHTML = `
        <h3 class="text-xl font-bold text-gray-800 mb-4">Comparativa de Régimenes Fiscales</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            ${Object.entries(scenarios).map(([key, scenario]) => {
                const recommended = scenario.recommended ? 'border-4 border-purple-600' : 'border-2 border-gray-200';
                return `
                    <div class="glass-card rounded-2xl p-6 ${recommended}">
                        ${scenario.recommended ? '<div class="mb-2 text-sm font-bold text-purple-600">✨ RECOMENDADO</div>' : ''}
                        <h4 class="text-lg font-bold text-gray-800 mb-4">${scenario.name}</h4>
                        <div class="space-y-2 mb-4">
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">Impuestos totales</span>
                                <span class="font-semibold">€${scenario.total_tax.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">Neto después impuestos</span>
                                <span class="font-semibold">€${scenario.net_after_tax.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">Tipo efectivo</span>
                                <span class="font-semibold">${scenario.effective_rate.toFixed(2)}%</span>
                            </div>
                        </div>
                        ${scenario.note ? `<p class="text-xs text-gray-500 italic">${scenario.note}</p>` : ''}
                    </div>
                `;
            }).join('')}
        </div>
        
        <div class="p-6 rounded-xl bg-purple-50 border-l-4 border-purple-600">
            <h4 class="font-bold text-gray-800 mb-2">💡 Recomendación</h4>
            <p class="text-gray-700">${data.recommendation}</p>
        </div>
    `;
}

/**
 * Tab Navigation
 */
function initTabNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Update nav active state
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

/**
 * Utilities
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' });
}

function showLoading() {
    // Add loading state to key elements
    document.querySelectorAll('.metric-card h3, .health-badge span').forEach(el => {
        el.classList.add('loading-skeleton');
    });
}

function hideLoading() {
    document.querySelectorAll('.loading-skeleton').forEach(el => {
        el.classList.remove('loading-skeleton');
    });
}

function showError(message) {
    console.error(message);
    // Could show a toast notification here
}

/**
 * Auto-refresh every 5 minutes
 */
setInterval(() => {
    loadDashboard();
}, 5 * 60 * 1000);
