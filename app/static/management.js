// Management Dashboard JavaScript
const API_BASE = window.location.origin;
const ADMIN_KEY = 'test-admin-key'; // En producción esto debería venir de autenticación

// Global data storage
let apartmentsData = [];
let expensesData = [];
let incomesData = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    
    // Set today's date as default in forms
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expenseDate').value = today;
    document.getElementById('incomeDate').value = today;
});

// Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName).classList.add('active');
    
    // Add active class to clicked nav link
    event.target.classList.add('active');
    
    // Load section-specific data
    switch(sectionName) {
        case 'apartments':
            loadApartments();
            break;
        case 'expenses':
            loadExpenses();
            break;
        case 'incomes':
            loadIncomes();
            break;
        case 'dashboard':
            loadDashboardData();
            break;
    }
}

// API Helper Functions
async function apiCall(endpoint, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Internal-Key': ADMIN_KEY
        }
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showAlert('Error en la API: ' + error.message, 'danger');
        throw error;
    }
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        // Load all data in parallel
        const [apartments, expenses, incomes] = await Promise.all([
            apiCall('/api/v1/apartments'),
            apiCall('/api/v1/expenses'),
            apiCall('/api/v1/incomes')
        ]);
        
        // Update stats
        document.getElementById('total-apartments').textContent = apartments.length;
        document.getElementById('total-expenses').textContent = expenses.length;
        document.getElementById('total-incomes').textContent = incomes.length;
        
        // Update recent activity
        updateRecentActivity(expenses, incomes);
        
        // Store data globally
        apartmentsData = apartments;
        expensesData = expenses;
        incomesData = incomes;
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateRecentActivity(expenses, incomes) {
    const activityContainer = document.getElementById('recent-activity');
    const recentItems = [];
    
    // Add recent expenses
    expenses.slice(0, 5).forEach(expense => {
        recentItems.push({
            type: 'expense',
            date: expense.date,
            description: `Gasto: €${expense.amount_gross} - ${expense.vendor || expense.category}`,
            icon: 'fas fa-receipt text-danger'
        });
    });
    
    // Add recent incomes
    incomes.slice(0, 5).forEach(income => {
        recentItems.push({
            type: 'income',
            date: income.date,
            description: `Ingreso: €${income.amount_gross} - ${income.guest_name || income.source}`,
            icon: 'fas fa-coins text-success'
        });
    });
    
    // Sort by date (most recent first)
    recentItems.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    if (recentItems.length === 0) {
        activityContainer.innerHTML = '<p class="text-muted">No hay actividad reciente</p>';
        return;
    }
    
    const html = recentItems.slice(0, 8).map(item => `
        <div class="d-flex align-items-center mb-2">
            <i class="${item.icon} me-3"></i>
            <div class="flex-grow-1">
                <div class="fw-medium">${item.description}</div>
                <small class="text-muted">${formatDate(item.date)}</small>
            </div>
        </div>
    `).join('');
    
    activityContainer.innerHTML = html;
}

// Apartments Functions
async function loadApartments() {
    try {
        const apartments = await apiCall('/api/v1/apartments');
        apartmentsData = apartments;
        renderApartmentsTable(apartments);
        updateApartmentSelects(apartments);
    } catch (error) {
        console.error('Error loading apartments:', error);
    }
}

function renderApartmentsTable(apartments) {
    const tbody = document.getElementById('apartments-table');
    
    if (apartments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No hay apartamentos registrados</td></tr>';
        return;
    }
    
    const html = apartments.map(apt => `
        <tr>
            <td><strong>${apt.code}</strong></td>
            <td>${apt.name || '-'}</td>
            <td>${apt.owner_email || '-'}</td>
            <td>
                <span class="badge ${apt.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${apt.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>${formatDate(apt.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editApartment('${apt.id}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteApartment('${apt.id}', '${apt.code}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function updateApartmentSelects(apartments) {
    const expenseSelect = document.getElementById('expenseApartment');
    const incomeSelect = document.getElementById('incomeApartment');
    
    const options = apartments.filter(apt => apt.is_active).map(apt => 
        `<option value="${apt.id}">${apt.code} - ${apt.name || 'Sin nombre'}</option>`
    ).join('');
    
    expenseSelect.innerHTML = '<option value="">Seleccionar apartamento...</option>' + options;
    incomeSelect.innerHTML = '<option value="">Seleccionar apartamento...</option>' + options;
}

async function createApartment() {
    const code = document.getElementById('apartmentCode').value.trim().toUpperCase();
    const name = document.getElementById('apartmentName').value.trim();
    const email = document.getElementById('apartmentEmail').value.trim();
    
    if (!code || !name) {
        showAlert('Por favor, completa todos los campos obligatorios', 'warning');
        return;
    }
    
    try {
        const newApartment = await apiCall('/api/v1/apartments', 'POST', {
            code: code,
            name: name,
            owner_email: email || null
        });
        
        showAlert(`Apartamento ${code} creado exitosamente`, 'success');
        
        // Close modal and refresh data
        bootstrap.Modal.getInstance(document.getElementById('createApartmentModal')).hide();
        document.getElementById('apartmentForm').reset();
        loadApartments();
        
    } catch (error) {
        console.error('Error creating apartment:', error);
    }
}

async function deleteApartment(id, code) {
    if (!confirm(`¿Estás seguro de eliminar el apartamento ${code}?`)) {
        return;
    }
    
    try {
        await apiCall(`/api/v1/apartments/${id}`, 'DELETE');
        showAlert(`Apartamento ${code} eliminado exitosamente`, 'success');
        loadApartments();
    } catch (error) {
        console.error('Error deleting apartment:', error);
    }
}

// Expenses Functions
async function loadExpenses() {
    try {
        const expenses = await apiCall('/api/v1/expenses');
        expensesData = expenses;
        renderExpensesTable(expenses);
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

function renderExpensesTable(expenses) {
    const tbody = document.getElementById('expenses-table');
    
    if (expenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay gastos registrados</td></tr>';
        return;
    }
    
    const html = expenses.map(expense => {
        const apartment = apartmentsData.find(apt => apt.id === expense.apartment_id);
        const apartmentCode = apartment ? apartment.code : 'N/A';
        
        return `
            <tr>
                <td>${formatDate(expense.date)}</td>
                <td><span class="badge bg-info">${apartmentCode}</span></td>
                <td><strong>€${parseFloat(expense.amount_gross).toFixed(2)}</strong></td>
                <td>
                    <span class="badge bg-secondary">${expense.category || 'Sin categoría'}</span>
                </td>
                <td>${expense.vendor || '-'}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(expense.status)}">
                        ${expense.status || 'PENDING'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editExpense('${expense.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteExpense('${expense.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = html;
}

async function createExpense() {
    const apartmentId = document.getElementById('expenseApartment').value;
    const date = document.getElementById('expenseDate').value;
    const amount = document.getElementById('expenseAmount').value;
    const category = document.getElementById('expenseCategory').value;
    const vendor = document.getElementById('expenseVendor').value.trim();
    const description = document.getElementById('expenseDescription').value.trim();
    
    if (!apartmentId || !date || !amount) {
        showAlert('Por favor, completa todos los campos obligatorios', 'warning');
        return;
    }
    
    try {
        const newExpense = await apiCall('/api/v1/expenses', 'POST', {
            apartment_id: apartmentId,
            date: date,
            amount_gross: parseFloat(amount),
            currency: 'EUR',
            category: category,
            vendor: vendor || null,
            description: description || null,
            source: 'manual_web'
        });
        
        showAlert('Gasto creado exitosamente', 'success');
        
        // Close modal and refresh data
        bootstrap.Modal.getInstance(document.getElementById('createExpenseModal')).hide();
        document.getElementById('expenseForm').reset();
        loadExpenses();
        
    } catch (error) {
        console.error('Error creating expense:', error);
    }
}

async function deleteExpense(id) {
    if (!confirm('¿Estás seguro de eliminar este gasto?')) {
        return;
    }
    
    try {
        await apiCall(`/api/v1/expenses/${id}`, 'DELETE');
        showAlert('Gasto eliminado exitosamente', 'success');
        loadExpenses();
    } catch (error) {
        console.error('Error deleting expense:', error);
    }
}

// Incomes Functions
async function loadIncomes() {
    try {
        const incomes = await apiCall('/api/v1/incomes');
        incomesData = incomes;
        renderIncomesTable(incomes);
    } catch (error) {
        console.error('Error loading incomes:', error);
    }
}

function renderIncomesTable(incomes) {
    const tbody = document.getElementById('incomes-table');
    
    if (incomes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay ingresos registrados</td></tr>';
        return;
    }
    
    const html = incomes.map(income => {
        const apartment = apartmentsData.find(apt => apt.id === income.apartment_id);
        const apartmentCode = apartment ? apartment.code : 'N/A';
        
        return `
            <tr>
                <td>${formatDate(income.date)}</td>
                <td><span class="badge bg-info">${apartmentCode}</span></td>
                <td><strong>€${parseFloat(income.amount_gross).toFixed(2)}</strong></td>
                <td>
                    <span class="badge ${getStatusBadgeClass(income.status)}">
                        ${income.status}
                    </span>
                </td>
                <td>${income.guest_name || '-'}</td>
                <td>${income.booking_reference || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editIncome('${income.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteIncome('${income.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = html;
}

async function createIncome() {
    const apartmentId = document.getElementById('incomeApartment').value;
    const date = document.getElementById('incomeDate').value;
    const amount = document.getElementById('incomeAmount').value;
    const status = document.getElementById('incomeStatus').value;
    const guest = document.getElementById('incomeGuest').value.trim();
    const reference = document.getElementById('incomeReference').value.trim();
    const source = document.getElementById('incomeSource').value;
    
    if (!apartmentId || !date || !amount) {
        showAlert('Por favor, completa todos los campos obligatorios', 'warning');
        return;
    }
    
    try {
        const newIncome = await apiCall('/api/v1/incomes', 'POST', {
            apartment_id: apartmentId,
            date: date,
            amount_gross: parseFloat(amount),
            currency: 'EUR',
            status: status,
            source: source,
            guest_name: guest || null,
            booking_reference: reference || null
        });
        
        showAlert('Ingreso creado exitosamente', 'success');
        
        // Close modal and refresh data
        bootstrap.Modal.getInstance(document.getElementById('createIncomeModal')).hide();
        document.getElementById('incomeForm').reset();
        loadIncomes();
        
    } catch (error) {
        console.error('Error creating income:', error);
    }
}

async function deleteIncome(id) {
    if (!confirm('¿Estás seguro de eliminar este ingreso?')) {
        return;
    }
    
    try {
        await apiCall(`/api/v1/incomes/${id}`, 'DELETE');
        showAlert('Ingreso eliminado exitosamente', 'success');
        loadIncomes();
    } catch (error) {
        console.error('Error deleting income:', error);
    }
}

// Modal Functions
function showCreateApartmentModal() {
    new bootstrap.Modal(document.getElementById('createApartmentModal')).show();
}

function showCreateExpenseModal() {
    // Make sure apartments are loaded for the select
    if (apartmentsData.length === 0) {
        loadApartments().then(() => {
            new bootstrap.Modal(document.getElementById('createExpenseModal')).show();
        });
    } else {
        new bootstrap.Modal(document.getElementById('createExpenseModal')).show();
    }
}

function showCreateIncomeModal() {
    // Make sure apartments are loaded for the select
    if (apartmentsData.length === 0) {
        loadApartments().then(() => {
            new bootstrap.Modal(document.getElementById('createIncomeModal')).show();
        });
    } else {
        new bootstrap.Modal(document.getElementById('createIncomeModal')).show();
    }
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'CONFIRMED':
            return 'bg-success';
        case 'PENDING':
            return 'bg-warning';
        case 'CANCELLED':
            return 'bg-danger';
        case 'PAID':
            return 'bg-success';
        default:
            return 'bg-secondary';
    }
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Edit functions (placeholder for future implementation)
function editApartment(id) {
    showAlert('Función de edición en desarrollo', 'info');
}

function editExpense(id) {
    showAlert('Función de edición en desarrollo', 'info');
}

function editIncome(id) {
    showAlert('Función de edición en desarrollo', 'info');
}