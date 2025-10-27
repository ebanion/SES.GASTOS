// Sistema de actualización en tiempo real mejorado
// Para uso en interfaces de gestión de SES.GASTOS

class RealTimeUpdater {
    constructor() {
        this.updateQueue = [];
        this.isUpdating = false;
        this.lastUpdate = Date.now();
        this.updateInterval = null;
    }

    // Inicializar sistema de actualizaciones
    init() {
        // Actualizar cada 30 segundos automáticamente
        this.updateInterval = setInterval(() => {
            this.refreshCurrentView();
        }, 30000);

        // Actualizar cuando la ventana recupera el foco
        window.addEventListener('focus', () => {
            this.refreshCurrentView();
        });

        // Actualizar antes de cerrar
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    // Limpiar recursos
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    // Actualizar vista actual basada en la URL
    async refreshCurrentView() {
        const path = window.location.pathname;
        
        try {
            if (path.includes('/incomes')) {
                await this.refreshIncomes();
            } else if (path.includes('/expenses')) {
                await this.refreshExpenses();
            } else if (path.includes('/apartments')) {
                await this.refreshApartments();
            } else if (path === '/admin/manage/') {
                await this.refreshDashboard();
            }
        } catch (error) {
            console.warn('Error en actualización automática:', error);
        }
    }

    // Actualizar ingresos sin reload completo
    async refreshIncomes() {
        try {
            const response = await fetch('/admin/manage/api/incomes?key=' + encodeURIComponent(this.getAdminKey()));
            if (response.ok) {
                const data = await response.json();
                this.updateIncomesTable(data.incomes || data);
                this.showUpdateNotification('Ingresos actualizados');
            }
        } catch (error) {
            console.error('Error actualizando ingresos:', error);
        }
    }

    // Actualizar gastos
    async refreshExpenses() {
        try {
            const response = await fetch('/admin/manage/api/expenses?key=' + encodeURIComponent(this.getAdminKey()));
            if (response.ok) {
                const data = await response.json();
                this.updateExpensesTable(data.expenses || data);
                this.showUpdateNotification('Gastos actualizados');
            }
        } catch (error) {
            console.error('Error actualizando gastos:', error);
        }
    }

    // Actualizar apartamentos
    async refreshApartments() {
        try {
            const response = await fetch('/admin/manage/api/apartments?key=' + encodeURIComponent(this.getAdminKey()));
            if (response.ok) {
                const data = await response.json();
                this.updateApartmentsTable(data.apartments || data);
                this.showUpdateNotification('Apartamentos actualizados');
            }
        } catch (error) {
            console.error('Error actualizando apartamentos:', error);
        }
    }

    // Actualizar dashboard
    async refreshDashboard() {
        try {
            const response = await fetch('/admin/manage/api/stats?key=' + encodeURIComponent(this.getAdminKey()));
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
                this.showUpdateNotification('Dashboard actualizado');
            }
        } catch (error) {
            console.error('Error actualizando dashboard:', error);
        }
    }

    // Actualizar tabla de ingresos
    updateIncomesTable(incomes) {
        const tbody = document.querySelector('#incomes-table tbody, .table tbody');
        if (!tbody || !incomes) return;

        const rows = incomes.map(income => `
            <tr data-id="${income.id}">
                <td>${this.formatDate(income.date)}</td>
                <td><span class="badge bg-info">${income.apartment_code || 'N/A'}</span></td>
                <td><strong>€${parseFloat(income.amount_gross || 0).toFixed(2)}</strong></td>
                <td>
                    <span class="badge ${this.getStatusBadge(income.status)}">
                        ${income.status}
                    </span>
                </td>
                <td>${income.guest_name || '-'}</td>
                <td>${income.booking_reference || '-'}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-success btn-sm" onclick="changeStatus('${income.id}', 'CONFIRMED')" title="Confirmar">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-outline-warning btn-sm" onclick="changeStatus('${income.id}', 'PENDING')" title="Pendiente">
                            <i class="fas fa-clock"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteIncome('${income.id}', '${income.guest_name || 'Sin nombre'}', '${income.amount_gross}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    // Actualizar estadísticas del dashboard
    updateDashboardStats(data) {
        const statsGrid = document.getElementById('stats-grid');
        if (!statsGrid || !data) return;

        const statsHtml = `
            <div class="stat-card apartments">
                <div class="stat-number">${data.totals?.active_apartments || 0}</div>
                <div class="stat-label">Apartamentos Activos</div>
            </div>
            <div class="stat-card expenses">
                <div class="stat-number">€${(data.monthly?.expenses_sum || 0).toFixed(2)}</div>
                <div class="stat-label">Gastos del Mes</div>
            </div>
            <div class="stat-card incomes">
                <div class="stat-number">€${(data.monthly?.incomes_sum || 0).toFixed(2)}</div>
                <div class="stat-label">Ingresos del Mes</div>
            </div>
            <div class="stat-card net">
                <div class="stat-number">€${(data.monthly?.net || 0).toFixed(2)}</div>
                <div class="stat-label">Beneficio Neto</div>
            </div>
        `;
        statsGrid.innerHTML = statsHtml;
    }

    // Mostrar notificación de actualización
    showUpdateNotification(message) {
        // Crear o actualizar notificación
        let notification = document.getElementById('update-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'update-notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 9999;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.style.opacity = '1';

        // Ocultar después de 2 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
        }, 2000);
    }

    // Actualización inmediata después de operaciones CRUD
    async immediateUpdate(operation, type) {
        this.showLoadingIndicator(`${operation} ${type}...`);
        
        // Esperar un poco para que el servidor procese
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Actualizar vista específica
        switch (type) {
            case 'ingreso':
                await this.refreshIncomes();
                break;
            case 'gasto':
                await this.refreshExpenses();
                break;
            case 'apartamento':
                await this.refreshApartments();
                break;
        }

        this.hideLoadingIndicator();
        
        // También actualizar dashboard si no estamos en él
        if (!window.location.pathname.includes('/admin/manage/')) {
            await this.refreshDashboard();
        }
    }

    // Mostrar indicador de carga
    showLoadingIndicator(message) {
        let indicator = document.getElementById('loading-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'loading-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 20px;
                border-radius: 8px;
                z-index: 10000;
                text-align: center;
            `;
            document.body.appendChild(indicator);
        }

        indicator.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
            ${message}
        `;
        indicator.style.display = 'block';
    }

    // Ocultar indicador de carga
    hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    // Utilidades
    getAdminKey() {
        let key = localStorage.getItem('admin_key');
        if (!key) {
            key = prompt('Introduce la clave de administrador:');
            if (key) {
                localStorage.setItem('admin_key', key);
            }
        }
        return key || '';
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    getStatusBadge(status) {
        switch (status) {
            case 'CONFIRMED': return 'bg-success';
            case 'PENDING': return 'bg-warning';
            case 'CANCELLED': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }
}

// Funciones globales mejoradas para reemplazar las existentes
window.realTimeUpdater = new RealTimeUpdater();

// Funciones mejoradas para operaciones CRUD
window.improvedSaveIncome = async function() {
    await window.realTimeUpdater.immediateUpdate('Guardando', 'ingreso');
};

window.improvedChangeStatus = async function(incomeId, newStatus) {
    await window.realTimeUpdater.immediateUpdate('Actualizando', 'ingreso');
};

window.improvedDeleteIncome = async function(incomeId) {
    await window.realTimeUpdater.immediateUpdate('Eliminando', 'ingreso');
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.realTimeUpdater.init();
    console.log('✅ Sistema de actualizaciones en tiempo real iniciado');
});

// Limpiar al salir
window.addEventListener('beforeunload', function() {
    if (window.realTimeUpdater) {
        window.realTimeUpdater.cleanup();
    }
});