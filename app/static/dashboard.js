// Dashboard JavaScript - Enhanced functionality

class DashboardManager {
    constructor() {
        this.charts = {};
        this.data = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTheme();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Theme toggle
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('theme-toggle')) {
                this.toggleTheme();
            }
        });

        // HTMX events
        document.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target.id === 'dashboardContent') {
                this.onContentUpdate();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshDashboard();
                        break;
                    case 'd':
                        e.preventDefault();
                        this.toggleTheme();
                        break;
                }
            }
        });

        // Window resize
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 300));
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeToggle(savedTheme);
    }

    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeToggle(newTheme);
        
        // Update charts with new theme
        setTimeout(() => this.updateChartsTheme(), 100);
    }

    updateThemeToggle(theme) {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    startAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.refreshDashboard();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    refreshDashboard() {
        const year = document.getElementById('yearSelect')?.value || new Date().getFullYear();
        const apartment = document.getElementById('apartmentSelect')?.value || '';
        
        let url = `/api/v1/dashboard/content?year=${year}`;
        if (apartment) {
            url += `&apartment_code=${apartment}`;
        }
        
        // Show loading state
        this.showLoadingState();
        
        htmx.ajax('GET', url, {
            target: '#dashboardContent',
            swap: 'innerHTML'
        });
    }

    showLoadingState() {
        const content = document.getElementById('dashboardContent');
        if (content) {
            content.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    Actualizando dashboard...
                </div>
            `;
        }
    }

    onContentUpdate() {
        // Re-initialize charts and components after HTMX update
        setTimeout(() => {
            this.initializeComponents();
        }, 100);
    }

    initializeComponents() {
        // This will be called after HTMX updates the content
        this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            const year = document.getElementById('yearSelect')?.value || new Date().getFullYear();
            const apartment = document.getElementById('apartmentSelect')?.value || '';
            
            let url = `/api/v1/dashboard/data?year=${year}`;
            if (apartment) {
                url += `&apartment_code=${apartment}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            this.data = data;
            this.updateMetrics();
            this.createCharts(data);
            this.populateTable(data);
            this.loadRecentExpenses();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Error cargando datos del dashboard');
        }
    }

    async updateMetrics() {
        try {
            const year = document.getElementById('yearSelect')?.value || new Date().getFullYear();
            const apartment = document.getElementById('apartmentSelect')?.value || '';
            
            let url = `/api/v1/dashboard/summary-stats?year=${year}`;
            if (apartment) {
                url += `&apartment_code=${apartment}`;
            }
            
            const response = await fetch(url);
            const stats = await response.json();
            
            this.animateMetricUpdate('totalIncome', stats.total_income);
            this.animateMetricUpdate('totalExpenses', stats.total_expenses);
            this.animateMetricUpdate('netProfit', stats.net_profit);
            this.animateMetricUpdate('profitMargin', stats.profit_margin, true);
            
            this.updateChangeIndicator('incomeChange', stats.income_change);
            this.updateChangeIndicator('expenseChange', stats.expense_change);
            this.updateChangeIndicator('netChange', stats.net_change);
            
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    animateMetricUpdate(elementId, newValue, isPercentage = false) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const currentValue = parseFloat(element.textContent.replace(/[€%,]/g, '')) || 0;
        const targetValue = newValue;
        const duration = 1000; // 1 second
        const steps = 60;
        const stepValue = (targetValue - currentValue) / steps;
        
        let currentStep = 0;
        const interval = setInterval(() => {
            currentStep++;
            const value = currentValue + (stepValue * currentStep);
            
            if (isPercentage) {
                element.textContent = this.formatPercentage(value);
            } else {
                element.textContent = this.formatCurrency(value);
            }
            
            if (currentStep >= steps) {
                clearInterval(interval);
                // Ensure final value is exact
                if (isPercentage) {
                    element.textContent = this.formatPercentage(targetValue);
                } else {
                    element.textContent = this.formatCurrency(targetValue);
                }
            }
        }, duration / steps);
    }

    updateChangeIndicator(elementId, change) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const changeSpan = element.querySelector('span:last-child');
        
        element.classList.remove('positive', 'negative', 'neutral');
        
        if (change > 0) {
            element.classList.add('positive');
            changeSpan.textContent = `+${this.formatPercentage(change)} vs año anterior`;
        } else if (change < 0) {
            element.classList.add('negative');
            changeSpan.textContent = `${this.formatPercentage(change)} vs año anterior`;
        } else {
            element.classList.add('neutral');
            changeSpan.textContent = 'Sin cambios vs año anterior';
        }
    }

    createCharts(data) {
        this.createMonthlyChart(data);
        this.createCategoryChart(data);
    }

    createMonthlyChart(data) {
        const ctx = document.getElementById('monthlyChart');
        if (!ctx) return;

        if (this.charts.monthly) {
            this.charts.monthly.destroy();
        }

        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        
        const incomes = data.items.map(item => item.incomes_accepted + item.incomes_pending);
        const expenses = data.items.map(item => item.expenses);
        const net = data.items.map(item => item.net);

        this.charts.monthly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Ingresos',
                        data: incomes,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Gastos',
                        data: expenses,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Beneficio Neto',
                        data: net,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#2563eb',
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                return context.dataset.label + ': ' + this.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    createCategoryChart(data) {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;

        if (this.charts.category) {
            this.charts.category.destroy();
        }

        // Aggregate expenses by category
        const categoryTotals = {};
        data.items.forEach(item => {
            if (item.expenses_by_category) {
                item.expenses_by_category.forEach(cat => {
                    categoryTotals[cat.category] = (categoryTotals[cat.category] || 0) + cat.total;
                });
            }
        });

        const categories = Object.keys(categoryTotals);
        const totals = Object.values(categoryTotals);
        const colors = [
            '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
        ];

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categories,
                datasets: [{
                    data: totals,
                    backgroundColor: colors.slice(0, categories.length),
                    borderWidth: 3,
                    borderColor: '#fff',
                    hoverBorderWidth: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + this.formatCurrency(context.parsed) + ' (' + percentage + '%)';
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
    }

    populateTable(data) {
        const tbody = document.getElementById('monthlyTableBody');
        if (!tbody) return;

        const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        
        tbody.innerHTML = '';
        
        data.items.forEach((item, index) => {
            const totalIncome = item.incomes_accepted + item.incomes_pending;
            const margin = totalIncome > 0 ? (item.net / totalIncome) * 100 : 0;
            const totalReservations = item.reservations_accepted + item.reservations_pending;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${months[index]}</strong></td>
                <td style="color: var(--success-color);">${this.formatCurrency(item.incomes_accepted)}</td>
                <td style="color: var(--warning-color);">${this.formatCurrency(item.incomes_pending)}</td>
                <td><strong>${this.formatCurrency(totalIncome)}</strong></td>
                <td style="color: var(--danger-color);">${this.formatCurrency(item.expenses)}</td>
                <td style="color: ${item.net >= 0 ? 'var(--success-color)' : 'var(--danger-color)'};">
                    <strong>${this.formatCurrency(item.net)}</strong>
                </td>
                <td>${this.formatPercentage(margin)}</td>
                <td>
                    <span class="status-indicator status-success"></span>${item.reservations_accepted}
                    <span class="status-indicator status-warning"></span>${item.reservations_pending}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadRecentExpenses() {
        try {
            const apartment = document.getElementById('apartmentSelect')?.value || '';
            let url = '/api/v1/dashboard/recent-expenses?limit=10';
            if (apartment) {
                url += `&apartment_code=${apartment}`;
            }
            
            const response = await fetch(url);
            const expenses = await response.json();
            
            const container = document.getElementById('recentExpenses');
            if (!container) return;
            
            if (expenses.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No hay gastos recientes</p>';
                return;
            }
            
            const expensesList = expenses.map(exp => `
                <div style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 500;">${exp.description || exp.vendor || 'Sin descripción'}</div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            ${exp.category || 'Sin categoría'} • ${exp.apartment_code} • ${new Date(exp.date).toLocaleDateString('es-ES')}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 600; color: var(--danger-color);">${this.formatCurrency(exp.amount)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">
                            ${new Date(exp.created_at).toLocaleString('es-ES')}
                        </div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = expensesList;
            
        } catch (error) {
            console.error('Error loading recent expenses:', error);
            const container = document.getElementById('recentExpenses');
            if (container) {
                container.innerHTML = '<p style="text-align: center; color: var(--danger-color); padding: 2rem;">Error cargando gastos recientes</p>';
            }
        }
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    updateChartsTheme() {
        // Update chart colors based on theme
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.update();
            }
        });
    }

    showError(message) {
        const content = document.getElementById('dashboardContent');
        if (content) {
            content.innerHTML = `
                <div style="text-align: center; color: var(--danger-color); padding: 3rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                    <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Error</div>
                    <div>${message}</div>
                    <button class="btn btn-primary" onclick="dashboard.refreshDashboard()" style="margin-top: 1rem;">
                        🔄 Reintentar
                    </button>
                </div>
            `;
        }
    }

    // Utility functions
    formatCurrency(amount) {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount || 0);
    }

    formatPercentage(value) {
        return new Intl.NumberFormat('es-ES', {
            style: 'percent',
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }).format((value || 0) / 100);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Export functions
    downloadChart(chartId) {
        const canvas = document.getElementById(chartId);
        if (canvas) {
            const url = canvas.toDataURL('image/png');
            const a = document.createElement('a');
            a.href = url;
            a.download = `${chartId}_${new Date().toISOString().split('T')[0]}.png`;
            a.click();
        }
    }

    exportToExcel() {
        // Implementation for Excel export
        alert('Función de exportación a Excel en desarrollo');
    }

    exportToPDF() {
        // Implementation for PDF export
        alert('Función de exportación a PDF en desarrollo');
    }
}

// Initialize dashboard manager
const dashboard = new DashboardManager();

// Global functions for backward compatibility
window.refreshDashboard = () => dashboard.refreshDashboard();
window.toggleTheme = () => dashboard.toggleTheme();
window.downloadChart = (chartId) => dashboard.downloadChart(chartId);
window.exportToExcel = () => dashboard.exportToExcel();
window.exportToPDF = () => dashboard.exportToPDF();