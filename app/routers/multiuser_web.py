# app/routers/multiuser_web.py
"""
Router para interfaces web del sistema multiusuario
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..auth_multiuser import get_current_user, require_superadmin
from ..models import User

router = APIRouter(prefix="/multiuser", tags=["Multiuser Web"])
templates = Jinja2Templates(directory="app/templates")

# ---------- PÁGINAS DE AUTENTICACIÓN ----------

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login multiusuario"""
    return templates.TemplateResponse("multiuser_login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro de anfitrión"""
    return templates.TemplateResponse("multiuser_register.html", {"request": request})

# ---------- ONBOARDING ----------

@router.get("/onboarding/apartment", response_class=HTMLResponse)
async def onboarding_apartment_page(request: Request):
    """Paso 2: Configuración del primer apartamento"""
    return templates.TemplateResponse("onboarding_apartment.html", {"request": request})

@router.get("/onboarding/telegram", response_class=HTMLResponse)
async def onboarding_telegram_page(request: Request):
    """Paso 3: Activación del bot de Telegram"""
    return templates.TemplateResponse("onboarding_telegram.html", {"request": request})

@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Página de prueba simple"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Test Multiuser</title></head>
    <body>
        <h1>🧪 Test del Sistema Multiusuario</h1>
        <button onclick="testRegister()">Test Registro</button>
        <button onclick="testLogin()">Test Login</button>
        <div id="result"></div>
        
        <script>
        async function testRegister() {
            try {
                const response = await fetch('/test-register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    '<h3>Resultado:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    '<h3>Error:</h3><p>' + error.message + '</p>';
            }
        }
        
        async function testLogin() {
            try {
                const response = await fetch('/test-login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    '<h3>Login Result:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    '<h3>Login Error:</h3><p>' + error.message + '</p>';
            }
        }
        </script>
    </body>
    </html>
    """)

# ---------- SELECTOR DE CUENTAS ----------

@router.get("/account-selector", response_class=HTMLResponse)
async def account_selector_page(request: Request):
    """Página para seleccionar cuenta cuando el usuario tiene múltiples"""
    return templates.TemplateResponse("account_selector.html", {"request": request})

# ---------- DASHBOARD PRINCIPAL ----------

@router.get("/dashboard-personal", response_class=HTMLResponse)
async def dashboard_personal_page(request: Request):
    """Dashboard financiero completo para anfitriones - sin redirecciones"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Financiero - SES.GASTOS</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; background: #f8fafc; min-height: 100vh;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 24px; border-radius: 16px; margin-bottom: 24px;
                display: flex; justify-content: space-between; align-items: center;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
            }
            .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .kpi-card { 
                background: white; padding: 20px; border-radius: 12px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.08); text-align: center;
                border-left: 4px solid #667eea;
            }
            .kpi-value { font-size: 28px; font-weight: bold; margin-bottom: 4px; }
            .kpi-label { color: #64748b; font-size: 14px; font-weight: 500; }
            .kpi-change { font-size: 12px; margin-top: 4px; }
            .positive { color: #10b981; }
            .negative { color: #ef4444; }
            .neutral { color: #64748b; }
            
            .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
            .full-width { grid-column: 1 / -1; }
            
            .card { 
                background: white; padding: 24px; border-radius: 12px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }
            .card h3 { margin: 0 0 16px 0; color: #1e293b; font-size: 18px; font-weight: 600; }
            
            .chart-container { position: relative; height: 400px; margin: 16px 0; }
            .chart-canvas { width: 100%; height: 100%; border-radius: 8px; }
            
            .filter-section {
                background: white; padding: 16px; border-radius: 12px; margin-bottom: 24px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08); display: flex; gap: 16px; align-items: center;
            }
            .filter-section select, .filter-section input {
                padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 8px;
                font-size: 14px; min-width: 150px;
            }
            
            .btn { 
                padding: 10px 20px; background: #667eea; color: white;
                border: none; border-radius: 8px; cursor: pointer; text-decoration: none;
                display: inline-block; font-weight: 500; transition: all 0.2s;
            }
            .btn:hover { background: #5a6fd8; transform: translateY(-1px); }
            .btn-secondary { background: #64748b; }
            .btn-secondary:hover { background: #475569; }
            
            .table { width: 100%; border-collapse: collapse; margin-top: 16px; }
            .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            .table th { background: #f8fafc; font-weight: 600; color: #374151; }
            .table tbody tr:hover { background: #f8fafc; }
            
            .category-item { 
                display: flex; justify-content: space-between; align-items: center;
                padding: 8px 0; border-bottom: 1px solid #f1f5f9;
            }
            .category-bar {
                height: 6px; background: #e2e8f0; border-radius: 3px; margin: 4px 0;
                position: relative; overflow: hidden;
            }
            .category-fill {
                height: 100%; background: linear-gradient(90deg, #667eea, #764ba2);
                border-radius: 3px; transition: width 0.3s ease;
            }
            
            .loading { text-align: center; padding: 40px; color: #64748b; }
            .error { text-align: center; padding: 40px; color: #ef4444; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>📊 Dashboard Financiero</h1>
                    <p id="accountName" style="margin: 4px 0; opacity: 0.9;">Cargando cuenta...</p>
                </div>
                <div>
                    <a href="/multiuser/dashboard" class="btn btn-secondary">← Volver</a>
                    <button onclick="exportData()" class="btn">📊 Exportar</button>
                </div>
            </div>

            <!-- Filtros -->
            <div class="filter-section">
                <label><strong>🏠 Apartamento:</strong></label>
                <select id="apartmentFilter" onchange="loadAllData()">
                    <option value="">Todos mis apartamentos</option>
                </select>
                
                <label><strong>📅 Año:</strong></label>
                <select id="yearFilter" onchange="loadAllData()">
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                </select>
                
                <button onclick="loadAllData()" class="btn">🔄 Actualizar</button>
            </div>

            <!-- KPIs Principales -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div id="totalIncome" class="kpi-value positive">€0.00</div>
                    <div class="kpi-label">Ingresos Totales</div>
                    <div id="incomeChange" class="kpi-change">-</div>
                </div>
                <div class="kpi-card">
                    <div id="totalExpenses" class="kpi-value negative">€0.00</div>
                    <div class="kpi-label">Gastos Totales</div>
                    <div id="expenseChange" class="kpi-change">-</div>
                </div>
                <div class="kpi-card">
                    <div id="netProfit" class="kpi-value neutral">€0.00</div>
                    <div class="kpi-label">Beneficio Neto</div>
                    <div id="profitChange" class="kpi-change">-</div>
                </div>
                <div class="kpi-card">
                    <div id="profitMargin" class="kpi-value neutral">0%</div>
                    <div class="kpi-label">% Beneficio Neto</div>
                    <div id="marginChange" class="kpi-change">-</div>
                </div>
            </div>

            <!-- Gráficos Principales -->
            <div class="main-grid">
                <div class="card">
                    <h3>📈 Evolución Mensual de Ingresos y Gastos</h3>
                    <div class="chart-container">
                        <canvas id="monthlyChart" class="chart-canvas"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🏷️ Gastos por Categoría</h3>
                    <div id="categoryChart" class="chart-container">
                        <canvas id="categoryCanvas" class="chart-canvas"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tablas Detalladas -->
            <div class="main-grid">
                <div class="card">
                    <h3>💸 Historial de Gastos Recientes</h3>
                    <div id="expensesTable" class="loading">Cargando gastos...</div>
                </div>
                
                <div class="card">
                    <h3>💰 Ingresos y Reservas</h3>
                    <div id="incomesTable" class="loading">Cargando ingresos...</div>
                </div>
            </div>

            <!-- Tabla Mensual Completa -->
            <div class="card full-width">
                <h3>📊 Resumen Mensual Detallado</h3>
                <div id="monthlyTable" class="loading">Cargando tabla mensual...</div>
            </div>
        </div>

        <script>
            let token = localStorage.getItem('access_token');
            let accountId = localStorage.getItem('current_account_id');
            let apartments = [];
            let monthlyChart = null;
            let categoryChart = null;
            
            async function loadUserData() {
                if (!token || !accountId) {
                    window.location.href = '/multiuser/login';
                    return;
                }
                
                try {
                    // Cargar información del usuario y cuenta
                    const userResponse = await fetch('/api/v1/auth/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (userResponse.ok) {
                        const userData = await userResponse.json();
                        const currentAccount = userData.accounts.find(acc => acc.id === accountId);
                        document.getElementById('accountName').textContent = currentAccount?.name || 'Mi Cuenta';
                    }
                    
                    // Cargar apartamentos
                    const response = await fetch('/api/v1/apartments/', {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'X-Account-ID': accountId
                        }
                    });
                    
                    if (response.ok) {
                        apartments = await response.json();
                        updateApartmentFilter(apartments);
                        loadAllData();
                    } else {
                        showError('Error cargando apartamentos');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showError('Error de conexión');
                }
            }
            
            function updateApartmentFilter(apartments) {
                const select = document.getElementById('apartmentFilter');
                select.innerHTML = '<option value="">Todos mis apartamentos (' + apartments.length + ')</option>';
                
                apartments.forEach(apt => {
                    const option = document.createElement('option');
                    option.value = apt.code;
                    option.textContent = `${apt.code} - ${apt.name}`;
                    select.appendChild(option);
                });
            }
            
            async function loadAllData() {
                const selectedApartment = document.getElementById('apartmentFilter').value;
                const selectedYear = document.getElementById('yearFilter').value;
                
                try {
                    // Cargar datos mensuales
                    await loadMonthlyData(selectedYear, selectedApartment);
                    
                    // Cargar estadísticas de resumen
                    await loadSummaryStats(selectedYear, selectedApartment);
                    
                    // Cargar gastos recientes
                    await loadRecentExpenses(selectedApartment);
                    
                    // Cargar ingresos y reservas
                    await loadIncomesData(selectedApartment);
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                    showError('Error cargando datos del dashboard');
                }
            }
            
            async function loadMonthlyData(year, apartmentCode) {
                let url = `/api/v1/dashboard/monthly?year=${year}`;
                if (apartmentCode) {
                    url += `&apartment_code=${apartmentCode}`;
                }
                
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Account-ID': accountId
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateMonthlyChart(data);
                    updateMonthlyTable(data);
                } else {
                    console.error('Error loading monthly data');
                }
            }
            
            async function loadSummaryStats(year, apartmentCode) {
                let url = `/api/v1/dashboard/summary-stats?year=${year}`;
                if (apartmentCode) {
                    url += `&apartment_code=${apartmentCode}`;
                }
                
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Account-ID': accountId
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateKPIs(data);
                } else {
                    console.error('Error loading summary stats');
                }
            }
            
            async function loadRecentExpenses(apartmentCode) {
                let url = '/api/v1/dashboard/recent-expenses?limit=15';
                if (apartmentCode) {
                    url += `&apartment_code=${apartmentCode}`;
                }
                
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Account-ID': accountId
                    }
                });
                
                if (response.ok) {
                    const expenses = await response.json();
                    updateExpensesTable(expenses);
                    updateCategoryChart(expenses);
                } else {
                    document.getElementById('expensesTable').innerHTML = '<p class="error">Error cargando gastos</p>';
                }
            }
            
            async function loadIncomesData(apartmentCode) {
                // Por ahora mostrar mensaje de desarrollo
                document.getElementById('incomesTable').innerHTML = `
                    <div style="text-align: center; padding: 20px; color: #64748b;">
                        <p><strong>💰 Ingresos y Reservas</strong></p>
                        <p>Esta sección mostrará:</p>
                        <ul style="text-align: left; max-width: 300px; margin: 16px auto;">
                            <li>Reservas confirmadas y pendientes</li>
                            <li>Ingresos por canal (Booking, Airbnb)</li>
                            <li>Estado de pagos</li>
                            <li>Próximos check-ins</li>
                        </ul>
                        <p><em>Funcionalidad en desarrollo</em></p>
                    </div>
                `;
            }
            
            function updateKPIs(data) {
                document.getElementById('totalIncome').textContent = `€${data.total_income.toFixed(2)}`;
                document.getElementById('totalExpenses').textContent = `€${data.total_expenses.toFixed(2)}`;
                document.getElementById('netProfit').textContent = `€${data.net_profit.toFixed(2)}`;
                document.getElementById('profitMargin').textContent = `${data.profit_margin.toFixed(1)}%`;
                
                // Cambios porcentuales
                document.getElementById('incomeChange').innerHTML = `
                    <span class="${data.income_change >= 0 ? 'positive' : 'negative'}">
                        ${data.income_change >= 0 ? '+' : ''}${data.income_change.toFixed(1)}% vs año anterior
                    </span>
                `;
                document.getElementById('expenseChange').innerHTML = `
                    <span class="${data.expense_change <= 0 ? 'positive' : 'negative'}">
                        ${data.expense_change >= 0 ? '+' : ''}${data.expense_change.toFixed(1)}% vs año anterior
                    </span>
                `;
                document.getElementById('profitChange').innerHTML = `
                    <span class="${data.net_change >= 0 ? 'positive' : 'negative'}">
                        ${data.net_change >= 0 ? '+' : ''}${data.net_change.toFixed(1)}% vs año anterior
                    </span>
                `;
                document.getElementById('marginChange').innerHTML = `
                    <span class="neutral">
                        Margen de beneficio
                    </span>
                `;
            }
            
            function updateMonthlyChart(data) {
                const ctx = document.getElementById('monthlyChart').getContext('2d');
                
                if (monthlyChart) {
                    monthlyChart.destroy();
                }
                
                const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                
                monthlyChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: months,
                        datasets: [
                            {
                                label: 'Ingresos Confirmados',
                                data: data.items.map(item => item.incomes_accepted),
                                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                                borderColor: 'rgba(16, 185, 129, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Ingresos Pendientes',
                                data: data.items.map(item => item.incomes_pending),
                                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                                borderColor: 'rgba(59, 130, 246, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Gastos',
                                data: data.items.map(item => item.expenses),
                                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                                borderColor: 'rgba(239, 68, 68, 1)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Evolución Mensual de Ingresos y Gastos'
                            },
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '€' + value.toFixed(0);
                                    }
                                }
                            }
                        }
                    }
                });
            }
            
            function updateCategoryChart(expenses) {
                // Agrupar gastos por categoría
                const categories = {};
                expenses.forEach(expense => {
                    const category = expense.category || 'Sin categoría';
                    categories[category] = (categories[category] || 0) + expense.amount;
                });
                
                const ctx = document.getElementById('categoryCanvas').getContext('2d');
                
                if (categoryChart) {
                    categoryChart.destroy();
                }
                
                const categoryNames = Object.keys(categories);
                const categoryValues = Object.values(categories);
                
                if (categoryNames.length === 0) {
                    ctx.font = '16px Arial';
                    ctx.fillStyle = '#64748b';
                    ctx.textAlign = 'center';
                    ctx.fillText('No hay gastos por categoría', ctx.canvas.width / 2, ctx.canvas.height / 2);
                    return;
                }
                
                categoryChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: categoryNames,
                        datasets: [{
                            data: categoryValues,
                            backgroundColor: [
                                '#667eea', '#764ba2', '#f093fb', '#f5576c',
                                '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
                                '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3'
                            ],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Distribución de Gastos por Categoría'
                            },
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            function updateExpensesTable(expenses) {
                if (expenses.length === 0) {
                    document.getElementById('expensesTable').innerHTML = `
                        <div style="text-align: center; padding: 40px; color: #64748b;">
                            <p>No hay gastos registrados</p>
                            <p><small>Usa el bot de Telegram para agregar gastos automáticamente</small></p>
                        </div>
                    `;
                    return;
                }
                
                document.getElementById('expensesTable').innerHTML = `
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Proveedor</th>
                                <th>Categoría</th>
                                <th>Apartamento</th>
                                <th style="text-align: right;">Importe</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${expenses.slice(0, 10).map(expense => `
                                <tr>
                                    <td>${new Date(expense.date).toLocaleDateString('es-ES')}</td>
                                    <td><strong>${expense.vendor || 'Sin proveedor'}</strong><br>
                                        <small style="color: #64748b;">${expense.description || ''}</small></td>
                                    <td><span style="background: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                                        ${expense.category || 'Sin categoría'}</span></td>
                                    <td>${expense.apartment_code}</td>
                                    <td style="text-align: right; font-weight: bold; color: #ef4444;">€${expense.amount.toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ${expenses.length > 10 ? `<p style="text-align: center; margin-top: 16px; color: #64748b;"><small>Mostrando 10 de ${expenses.length} gastos</small></p>` : ''}
                `;
            }
            
            function updateMonthlyTable(data) {
                const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
                
                document.getElementById('monthlyTable').innerHTML = `
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Mes</th>
                                <th style="text-align: right;">Ingresos Confirmados</th>
                                <th style="text-align: right;">Ingresos Pendientes</th>
                                <th style="text-align: right;">Total Ingresos</th>
                                <th style="text-align: right;">Gastos</th>
                                <th style="text-align: right;">Beneficio Neto</th>
                                <th style="text-align: right;">% Margen</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.items.map((item, index) => {
                                const totalIncome = item.incomes_accepted + item.incomes_pending;
                                const margin = totalIncome > 0 ? ((totalIncome - item.expenses) / totalIncome * 100) : 0;
                                return `
                                    <tr>
                                        <td><strong>${months[index]}</strong></td>
                                        <td style="text-align: right; color: #10b981;">€${item.incomes_accepted.toFixed(2)}</td>
                                        <td style="text-align: right; color: #3b82f6;">€${item.incomes_pending.toFixed(2)}</td>
                                        <td style="text-align: right; font-weight: bold;">€${totalIncome.toFixed(2)}</td>
                                        <td style="text-align: right; color: #ef4444;">€${item.expenses.toFixed(2)}</td>
                                        <td style="text-align: right; font-weight: bold; color: ${item.net >= 0 ? '#10b981' : '#ef4444'};">€${item.net.toFixed(2)}</td>
                                        <td style="text-align: right; color: ${margin >= 0 ? '#10b981' : '#ef4444'};">${margin.toFixed(1)}%</td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            function showError(message) {
                document.getElementById('expensesTable').innerHTML = `<p class="error">${message}</p>`;
                document.getElementById('incomesTable').innerHTML = `<p class="error">${message}</p>`;
                document.getElementById('monthlyTable').innerHTML = `<p class="error">${message}</p>`;
            }
            
            function exportData() {
                alert(`📊 Exportar Datos

Funcionalidades disponibles:
• 📄 Exportar a Excel
• 📋 Exportar a PDF
• 📊 Reportes personalizados
• 📈 Gráficos para presentaciones

Esta funcionalidad se implementará próximamente.`);
            }
            
            // Inicializar
            loadUserData();
        </script>
    </body>
    </html>
    """)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard principal de la cuenta seleccionada"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - SES.GASTOS</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; background: #f5f5f5; min-height: 100vh;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
                display: flex; justify-content: space-between; align-items: center;
            }
            .account-info { display: flex; align-items: center; }
            .account-icon { 
                width: 48px; height: 48px; background: rgba(255,255,255,0.2);
                border-radius: 12px; display: flex; align-items: center; justify-content: center;
                font-size: 24px; margin-right: 16px;
            }
            .btn { 
                padding: 8px 16px; background: rgba(255,255,255,0.2); color: white;
                border: none; border-radius: 6px; cursor: pointer; text-decoration: none;
                display: inline-block; margin-left: 8px;
            }
            .btn:hover { background: rgba(255,255,255,0.3); }
            .welcome-message {
                background: white; padding: 32px; border-radius: 12px; text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;
            }
            .no-apartments {
                background: #fff8e1; border: 1px solid #ffcc02; border-radius: 8px;
                padding: 24px; text-align: center; margin: 20px 0;
            }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { 
                background: white; padding: 20px; border-radius: 12px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .loading { text-align: center; padding: 40px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="account-info">
                    <div class="account-icon" id="accountIcon">🏠</div>
                    <div>
                        <h1 id="accountName">Cargando...</h1>
                        <p id="userEmail">-</p>
                    </div>
                </div>
                <div>
                    <a href="/analytics/pro" class="btn" style="background: rgba(255,255,255,0.95); color: #667eea; font-weight: 600;">
                        📊 Analytics
                    </a>
                    <a href="/multiuser/account-selector" class="btn">Cambiar Cuenta</a>
                    <button onclick="logout()" class="btn">Cerrar Sesión</button>
                </div>
            </div>

            <div id="dashboardContent" class="loading">
                <p>Cargando dashboard...</p>
            </div>
        </div>

        <script>
            let userData = null;
            let accountsData = null;
            let currentAccountId = null;

            async function loadUserData() {
                const token = localStorage.getItem('access_token');
                console.log('🔍 [DEBUG] Loading user data...');
                console.log('🔍 [DEBUG] Token exists:', !!token);
                
                if (!token) {
                    console.log('❌ [DEBUG] No token, redirecting to login');
                    window.location.href = '/multiuser/login';
                    return;
                }

                try {
                    const response = await fetch('/api/v1/auth/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });

                    console.log('🔍 [DEBUG] Auth response status:', response.status);

                    if (response.ok) {
                        const data = await response.json();
                        console.log('🔍 [DEBUG] User data:', data.user);
                        console.log('🔍 [DEBUG] Accounts data:', data.accounts);
                        
                        userData = data.user;
                        accountsData = data.accounts;
                        currentAccountId = localStorage.getItem('current_account_id') || data.default_account_id;
                        
                        console.log('🔍 [DEBUG] Selected account ID:', currentAccountId);
                        console.log('🔍 [DEBUG] Available accounts:', accountsData.map(acc => ({id: acc.id, name: acc.name})));

                        displayUserInfo();
                        await loadApartments();
                    } else {
                        const errorText = await response.text();
                        console.error('❌ [DEBUG] Auth failed:', response.status, errorText);
                        window.location.href = '/multiuser/login';
                    }
                } catch (error) {
                    console.error('❌ [DEBUG] Error loading user data:', error);
                    window.location.href = '/multiuser/login';
                }
            }

            function displayUserInfo() {
                const currentAccount = accountsData.find(acc => acc.id === currentAccountId);
                
                document.getElementById('accountName').textContent = currentAccount?.name || 'Cuenta';
                document.getElementById('userEmail').textContent = userData.email;
                document.getElementById('accountIcon').textContent = currentAccount?.name.charAt(0) || '🏠';
            }

            async function loadApartments() {
                const token = localStorage.getItem('access_token');
                
                console.log('🔍 [DEBUG] Loading apartments...');
                console.log('🔍 [DEBUG] Token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
                console.log('🔍 [DEBUG] Current Account ID:', currentAccountId);
                
                try {
                    const response = await fetch('/api/v1/apartments/', {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'X-Account-ID': currentAccountId
                        }
                    });

                    console.log('🔍 [DEBUG] Response status:', response.status);
                    
                    if (response.ok) {
                        const apartments = await response.json();
                        console.log('🔍 [DEBUG] Apartments received:', apartments);
                        console.log('🔍 [DEBUG] Number of apartments:', apartments.length);
                        
                        if (apartments.length > 0) {
                            apartments.forEach((apt, index) => {
                                console.log(`🔍 [DEBUG] Apartment ${index + 1}:`, {
                                    code: apt.code,
                                    name: apt.name,
                                    account_id: apt.account_id,
                                    owner_email: apt.owner_email
                                });
                            });
                        }
                        
                        displayDashboard(apartments);
                    } else {
                        const errorText = await response.text();
                        console.error('❌ [DEBUG] Error response:', errorText);
                        displayNoApartments();
                    }
                } catch (error) {
                    console.error('❌ [DEBUG] Network error:', error);
                    displayNoApartments();
                }
            }

            function displayNoApartments() {
                document.getElementById('dashboardContent').innerHTML = `
                    <div class="no-apartments">
                        <h2>🏠 ¡Vamos a configurar tu primer apartamento!</h2>
                        <p>Para empezar a gestionar gastos e ingresos, necesitas configurar al menos un apartamento.</p>
                        <br>
                        <button class="btn" onclick="window.location.href='/multiuser/onboarding/apartment'" 
                                style="background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">
                            ➕ Configurar mi primer apartamento
                        </button>
                    </div>
                `;
            }

            function displayDashboard(apartments) {
                const currentAccount = accountsData.find(acc => acc.id === currentAccountId);
                
                document.getElementById('dashboardContent').innerHTML = `
                    <div class="welcome-message">
                        <h2>🎉 ¡Bienvenido a tu Dashboard!</h2>
                        <p>Tienes <strong>${apartments.length} apartamento(s)</strong> configurado(s) en <strong>${currentAccount?.name}</strong></p>
                    </div>

                    <div class="grid">
                        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                            <h3 style="color: white;">📊 Analytics Financiero & Fiscal</h3>
                            <p>KPIs hoteleros, salud financiera, calculadoras IVA/IRPF</p>
                            <div style="margin: 16px 0;">
                                <div style="padding: 4px 0;">✅ ADR, Ocupación, RevPAR</div>
                                <div style="padding: 4px 0;">✅ Análisis de gastos con benchmarking</div>
                                <div style="padding: 4px 0;">✅ Calculadoras fiscales automáticas</div>
                                <div style="padding: 4px 0;">✅ Simulador de regímenes fiscales</div>
                            </div>
                            <button onclick="window.location.href='/analytics/pro'" class="btn" 
                                    style="background: white; color: #667eea; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; width: 100%; font-size: 16px;">
                                🚀 Abrir Analytics PRO
                            </button>
                        </div>

                        <div class="card">
                            <h3>🏠 Mis Apartamentos</h3>
                            <div id="apartmentsList">
                                ${apartments.map(apt => `
                                    <div style="padding: 8px; border-bottom: 1px solid #eee;">
                                        <strong>${apt.code}</strong> - ${apt.name || 'Sin nombre'}
                                        <span style="color: ${apt.is_active ? '#4caf50' : '#f44336'};">
                                            ${apt.is_active ? '✅ Activo' : '⏸️ Inactivo'}
                                        </span>
                                    </div>
                                `).join('')}
                            </div>
                            <br>
                            <button class="btn" onclick="window.location.href='/multiuser/onboarding/apartment'" 
                                    style="background: #667eea; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;">
                                ➕ Agregar apartamento
                            </button>
                        </div>

                        <div class="card">
                            <h3>🤖 Asistente Virtual</h3>
                            <p>Tu gestor automático de gastos con IA integrada</p>
                            <br>
                            <button onclick="openChat()" class="btn" 
                                    style="background: #667eea; color: white; padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer;">
                                💬 Abrir Chat
                            </button>
                            <button onclick="showChatFeatures()" class="btn" 
                                    style="background: #f8f9fa; color: #333; padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; cursor: pointer;">
                                Ver funciones
                            </button>
                        </div>

                        <div class="card">
                            <h3>📊 Resumen Financiero</h3>
                            <p>Gastos e ingresos de este mes</p>
                            <div style="margin-top: 16px; margin-bottom: 16px;">
                                <div style="padding: 4px 0;">💰 Ingresos: <strong>0 €</strong></div>
                                <div style="padding: 4px 0;">💸 Gastos: <strong>0 €</strong></div>
                                <div style="padding: 4px 0;">📈 Balance: <strong>0 €</strong></div>
                            </div>
                            <button onclick="openFullDashboard()" class="btn" 
                                    style="background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 14px;">
                                📊 Ver Dashboard Completo
                            </button>
                            <button onclick="openReports()" class="btn" 
                                    style="background: #f8f9fa; color: #333; padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 8px; font-size: 14px;">
                                📈 Generar Reportes
                            </button>
                        </div>
                    </div>

                    <div style="text-align: center; margin-top: 32px; padding: 20px; background: white; border-radius: 8px;">
                        <h3>🚀 ¡Tu sistema está listo!</h3>
                        <p>Ahora puedes:</p>
                        <ul style="text-align: left; max-width: 400px; margin: 16px auto;">
                            <li>📸 Enviar fotos de facturas al bot</li>
                            <li>💰 Registrar gastos automáticamente</li>
                            <li>📊 Ver reportes en tiempo real</li>
                            <li>🏠 Gestionar múltiples apartamentos</li>
                        </ul>
                    </div>
                `;
            }

            function showBotInstructions() {
                const firstApartment = apartments.length > 0 ? apartments[0] : null;
                const apartmentCode = firstApartment ? firstApartment.code : 'TU_CODIGO';
                
                alert(`🤖 Instrucciones del Bot:

1. Abre Telegram y busca: @UriApartment_Bot
2. Envía: /start
3. Envía: /usar ${apartmentCode}
4. ¡Envía una foto de factura!

El bot procesará la factura automáticamente y creará el gasto en tu cuenta.`);
            }

            function openFullDashboard() {
                // Redirigir al dashboard personal dedicado (mantiene autenticación)
                const token = localStorage.getItem('access_token');
                
                if (!token || !currentAccountId) {
                    alert('❌ Error de autenticación. Por favor, inicia sesión nuevamente.');
                    window.location.href = '/multiuser/login';
                    return;
                }
                
                // Redirigir al dashboard personal que usa localStorage para autenticación
                window.location.href = '/multiuser/dashboard-personal';
            }
            
            function showSimpleDashboard() {
                const currentAccount = accountsData.find(acc => acc.id === currentAccountId);
                
                document.getElementById('dashboardContent').innerHTML = `
                    <div class="welcome-message">
                        <h2>📊 Dashboard Personal - ${currentAccount?.name}</h2>
                        <button onclick="loadUserData()" class="btn" style="background: #667eea; color: white;">← Volver</button>
                    </div>
                    
                    <div class="grid">
                        <div class="card">
                            <h3>🏠 Filtrar por Apartamento</h3>
                            <select id="apartmentFilter" onchange="loadDashboardStats()" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">Todos mis apartamentos</option>
                                ${apartments.map(apt => `<option value="${apt.code}">${apt.code} - ${apt.name}</option>`).join('')}
                            </select>
                        </div>
                        
                        <div class="card">
                            <h3>📈 Resumen 2025</h3>
                            <div id="dashboardStats">
                                <div style="text-align: center; padding: 20px;">
                                    <div style="font-size: 24px; color: #4caf50; margin: 8px;">€0.00</div>
                                    <div style="color: #666;">Ingresos Totales</div>
                                    <div style="font-size: 24px; color: #f44336; margin: 8px;">€0.00</div>
                                    <div style="color: #666;">Gastos Totales</div>
                                    <div style="font-size: 24px; color: #2196f3; margin: 8px;">€0.00</div>
                                    <div style="color: #666;">Balance</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>💸 Últimos Gastos</h3>
                            <div id="recentExpenses">
                                <p style="text-align: center; color: #666; padding: 20px;">
                                    No hay gastos registrados aún.<br>
                                    <small>Usa el bot de Telegram para agregar gastos automáticamente.</small>
                                </p>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🤖 Instrucciones del Bot</h3>
                            <div style="padding: 16px; background: #f8f9fa; border-radius: 8px; margin-top: 12px;">
                                <p><strong>Para agregar gastos automáticamente:</strong></p>
                                <ol style="margin: 8px 0; padding-left: 20px;">
                                    <li>Busca <strong>@UriApartment_Bot</strong> en Telegram</li>
                                    <li>Envía <code>/start</code></li>
                                    <li>Configura con <code>/usar ${apartments.length > 0 ? apartments[0].code : 'TU_CODIGO'}</code></li>
                                    <li>¡Envía fotos de facturas!</li>
                                </ol>
                                <a href="https://t.me/UriApartment_Bot" target="_blank" class="btn" 
                                   style="background: #0088cc; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; display: inline-block; margin-top: 8px;">
                                    🤖 Abrir Bot
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                
                // Cargar estadísticas reales
                loadDashboardStats();
            }
            
            async function loadDashboardStats() {
                const token = localStorage.getItem('access_token');
                const selectedApartment = document.getElementById('apartmentFilter')?.value || '';
                
                try {
                    // Cargar datos del año actual
                    const year = new Date().getFullYear();
                    let url = `/api/v1/dashboard/monthly?year=${year}`;
                    if (selectedApartment) {
                        url += `&apartment_code=${selectedApartment}`;
                    }
                    
                    const response = await fetch(url, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'X-Account-ID': currentAccountId
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        updateDashboardStats(data);
                    } else {
                        console.error('Error loading dashboard stats:', response.status);
                    }
                    
                    // Cargar gastos recientes
                    const expensesUrl = selectedApartment 
                        ? `/api/v1/dashboard/recent-expenses?apartment_code=${selectedApartment}`
                        : '/api/v1/dashboard/recent-expenses';
                        
                    const expensesResponse = await fetch(expensesUrl, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'X-Account-ID': currentAccountId
                        }
                    });
                    
                    if (expensesResponse.ok) {
                        const expenses = await expensesResponse.json();
                        updateRecentExpenses(expenses);
                    }
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                }
            }
            
            function updateDashboardStats(data) {
                const totalIncome = data.items.reduce((sum, item) => sum + item.incomes_accepted + item.incomes_pending, 0);
                const totalExpenses = data.items.reduce((sum, item) => sum + item.expenses, 0);
                const balance = totalIncome - totalExpenses;
                
                document.getElementById('dashboardStats').innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 24px; color: #4caf50; margin: 8px;">€${totalIncome.toFixed(2)}</div>
                        <div style="color: #666;">Ingresos Totales</div>
                        <div style="font-size: 24px; color: #f44336; margin: 8px;">€${totalExpenses.toFixed(2)}</div>
                        <div style="color: #666;">Gastos Totales</div>
                        <div style="font-size: 24px; color: ${balance >= 0 ? '#4caf50' : '#f44336'}; margin: 8px;">€${balance.toFixed(2)}</div>
                        <div style="color: #666;">Balance</div>
                    </div>
                `;
            }
            
            function updateRecentExpenses(expenses) {
                if (expenses.length === 0) {
                    document.getElementById('recentExpenses').innerHTML = `
                        <p style="text-align: center; color: #666; padding: 20px;">
                            No hay gastos registrados aún.<br>
                            <small>Usa el bot de Telegram para agregar gastos automáticamente.</small>
                        </p>
                    `;
                    return;
                }
                
                document.getElementById('recentExpenses').innerHTML = expenses.slice(0, 5).map(expense => `
                    <div style="padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between;">
                        <div>
                            <strong>${expense.vendor || 'Sin proveedor'}</strong><br>
                            <small style="color: #666;">${expense.category || 'Sin categoría'} • ${expense.date}</small>
                        </div>
                        <div style="text-align: right; color: #f44336; font-weight: bold;">
                            €${expense.amount.toFixed(2)}
                        </div>
                    </div>
                `).join('');
            }

            function openReports() {
                alert(`📈 Reportes Disponibles:

• 📊 Resumen mensual por apartamento
• 💰 Análisis de ingresos vs gastos
• 📋 Exportación a Excel/PDF
• 📈 Gráficos de tendencias
• 🏷️ Gastos por categoría

Esta funcionalidad se está desarrollando.
Por ahora usa el Dashboard Completo.`);
            }

            function logout() {
                localStorage.clear();
                window.location.href = '/multiuser/login';
            }

            // ========== FUNCIONES DEL CHAT INTEGRADO ==========
            
            let chatActiveApartment = null;
            let chatApartments = [];
            
            function openChat() {
                document.getElementById('chatModal').style.display = 'block';
                document.body.style.overflow = 'hidden';
                loadChatApartments();
            }
            
            function closeChat() {
                document.getElementById('chatModal').style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            
            function showChatFeatures() {
                alert(`🤖 Funciones del Asistente Virtual:

📸 SUBIR FACTURAS
• Sube fotos de tickets y facturas
• OCR automático + IA para extraer datos
• Categorización inteligente

✍️ ESCRIBIR GASTOS
• "Restaurante La Marina, 35€, cena"
• "Taxi aeropuerto, 25€"
• "Supermercado, 67.45€, compra semanal"

🏠 GESTIONAR APARTAMENTOS
• Ver lista de apartamentos
• Crear nuevos apartamentos
• Cambiar apartamento activo

📊 CONSULTAS
• "¿Cuánto gasté este mes?"
• "Mostrar gastos de limpieza"
• "Resumen del apartamento SES01"`);
            }
            
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Verificar que hay apartamento seleccionado para gastos
                const isExpenseMessage = message.includes('€') || message.includes('eur') || 
                                       message.toLowerCase().includes('gasto') || 
                                       message.toLowerCase().includes('pagué') ||
                                       message.toLowerCase().includes('compré');
                
                if (isExpenseMessage && !chatActiveApartment) {
                    alert('❌ Primero selecciona un apartamento para registrar gastos');
                    return;
                }
                
                // Agregar mensaje del usuario
                addChatMessage(message, 'user');
                input.value = '';
                
                // Mostrar indicador de escritura
                addTypingIndicator();
                
                try {
                    // Enviar al endpoint de chat
                    const response = await fetch('/api/v1/chat/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                            'X-Account-ID': currentAccountId
                        },
                        body: JSON.stringify({
                            message: message,
                            context: 'dashboard',
                            apartment_code: chatActiveApartment ? chatActiveApartment.code : null
                        })
                    });
                    
                    removeTypingIndicator();
                    
                    if (response.ok) {
                        const data = await response.json();
                        addChatMessage(data.response, 'assistant');
                        
                        // Si se creó un gasto, actualizar dashboard
                        if (data.action === 'expense_created') {
                            setTimeout(() => {
                                loadUserData(); // Recargar datos
                            }, 1000);
                        }
                    } else {
                        addChatMessage('❌ Error procesando tu mensaje. Inténtalo de nuevo.', 'assistant');
                    }
                } catch (error) {
                    removeTypingIndicator();
                    addChatMessage('❌ Error de conexión. Verifica tu internet.', 'assistant');
                }
            }
            
            function addChatMessage(message, sender) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}`;
                messageDiv.style.marginBottom = '16px';
                messageDiv.style.textAlign = sender === 'user' ? 'right' : 'left';
                
                const bubble = document.createElement('div');
                bubble.style.display = 'inline-block';
                bubble.style.maxWidth = '80%';
                bubble.style.padding = '12px 16px';
                bubble.style.borderRadius = sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px';
                bubble.style.background = sender === 'user' ? '#667eea' : '#f1f5f9';
                bubble.style.color = sender === 'user' ? 'white' : '#374151';
                bubble.innerHTML = message.replace(/\\n/g, '<br>');
                
                messageDiv.appendChild(bubble);
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function addTypingIndicator() {
                const messagesContainer = document.getElementById('chatMessages');
                const typingDiv = document.createElement('div');
                typingDiv.id = 'typingIndicator';
                typingDiv.style.marginBottom = '16px';
                typingDiv.innerHTML = `
                    <div style="display: inline-block; background: #f1f5f9; padding: 12px 16px; border-radius: 18px 18px 18px 4px; color: #64748b;">
                        <span style="animation: pulse 1.5s infinite;">🤖 Escribiendo...</span>
                    </div>
                `;
                messagesContainer.appendChild(typingDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function removeTypingIndicator() {
                const indicator = document.getElementById('typingIndicator');
                if (indicator) {
                    indicator.remove();
                }
            }
            
            function handleChatKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            }
            
            async function loadChatApartments() {
                try {
                    const response = await fetch('/api/v1/apartments/', {
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                            'X-Account-ID': currentAccountId
                        }
                    });
                    
                    if (response.ok) {
                        chatApartments = await response.json();
                        updateChatApartmentSelector();
                        
                        // Auto-seleccionar el primer apartamento si solo hay uno
                        if (chatApartments.length === 1) {
                            chatActiveApartment = chatApartments[0];
                            document.getElementById('chatApartmentSelect').value = chatActiveApartment.code;
                            addChatMessage(`✅ Apartamento seleccionado: **${chatActiveApartment.code}** - ${chatActiveApartment.name}\\n\\n¡Ahora puedes enviar facturas o escribir gastos!`, 'assistant');
                        }
                    }
                } catch (error) {
                    console.error('Error loading chat apartments:', error);
                }
            }
            
            function updateChatApartmentSelector() {
                const select = document.getElementById('chatApartmentSelect');
                select.innerHTML = '<option value="">Selecciona un apartamento...</option>';
                
                chatApartments.forEach(apt => {
                    const option = document.createElement('option');
                    option.value = apt.code;
                    option.textContent = `${apt.code} - ${apt.name}`;
                    select.appendChild(option);
                });
            }
            
            function changeActiveApartment() {
                const select = document.getElementById('chatApartmentSelect');
                const selectedCode = select.value;
                
                if (selectedCode) {
                    chatActiveApartment = chatApartments.find(apt => apt.code === selectedCode);
                    addChatMessage(`🏠 Apartamento cambiado a: **${chatActiveApartment.code}** - ${chatActiveApartment.name}\\n\\n¡Listo para procesar facturas!`, 'assistant');
                } else {
                    chatActiveApartment = null;
                }
            }

            async function handleFileUpload(event) {
                const file = event.target.files[0];
                if (!file) return;
                
                // Verificar que hay apartamento seleccionado
                if (!chatActiveApartment) {
                    alert('❌ Primero selecciona un apartamento');
                    event.target.value = '';
                    return;
                }
                
                // Validar tipo de archivo
                const isImage = file.type.startsWith('image/');
                const isPDF = file.type === 'application/pdf';
                
                if (!isImage && !isPDF) {
                    alert('❌ Solo se permiten imágenes (JPG, PNG) y archivos PDF');
                    event.target.value = '';
                    return;
                }
                
                // Validar tamaño (máximo 10MB)
                if (file.size > 10 * 1024 * 1024) {
                    alert('❌ El archivo es muy grande. Máximo 10MB');
                    event.target.value = '';
                    return;
                }
                
                const fileType = isPDF ? 'PDF' : 'imagen';
                addChatMessage(`📄 Procesando ${fileType}...`, 'user');
                addTypingIndicator();
                
                try {
                    // Crear FormData para subir el archivo
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('apartment_code', chatActiveApartment.code);
                    formData.append('context', 'dashboard');
                    
                    const response = await fetch('/api/v1/chat/file', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                            'X-Account-ID': currentAccountId
                        },
                        body: formData
                    });
                    
                    removeTypingIndicator();
                    
                    if (response.ok) {
                        const data = await response.json();
                        addChatMessage(data.response, 'assistant');
                        
                        // Si se creó un gasto, actualizar dashboard
                        if (data.action === 'expense_created') {
                            setTimeout(() => {
                                loadUserData(); // Recargar datos
                            }, 1000);
                        }
                    } else {
                        addChatMessage(`❌ Error procesando el ${fileType}. Inténtalo de nuevo.`, 'assistant');
                    }
                } catch (error) {
                    removeTypingIndicator();
                    addChatMessage(`❌ Error subiendo el ${fileType}. Verifica tu conexión.`, 'assistant');
                }
                
                // Limpiar input
                event.target.value = '';
            }

            // Inicializar
            loadUserData();
        </script>
        
        <!-- Modal del Chat Integrado -->
        <div id="chatModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 800px; height: 80%; background: white; border-radius: 12px; display: flex; flex-direction: column;">
                <!-- Header del Chat -->
                <div style="padding: 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px 12px 0 0;">
                    <div>
                        <h3 style="margin: 0; font-size: 18px;">🤖 Asistente Virtual</h3>
                        <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.9;">Tu gestor automático de gastos</p>
                    </div>
                    <button onclick="closeChat()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 16px;">✕</button>
                </div>
                
                <!-- Área de mensajes -->
                <div id="chatMessages" style="flex: 1; padding: 20px; overflow-y: auto; background: #f8fafc;">
                    <div class="chat-message assistant" style="margin-bottom: 16px;">
                        <div style="background: #667eea; color: white; padding: 16px 20px; border-radius: 18px 18px 18px 4px; max-width: 85%; display: inline-block; line-height: 1.5;">
                            ¡Hola! 👋<br><br>
                            🤖 <strong>Asistente SES.GASTOS con IA + OCR</strong><br><br>
                            📋 <strong>Pasos para usar:</strong><br>
                            1️⃣ Selecciona tu apartamento<br>
                            2️⃣ <strong>Envía factura:</strong><br>
                            &nbsp;&nbsp;&nbsp;📸 <strong>Foto de factura</strong> → IA automática<br>
                            &nbsp;&nbsp;&nbsp;📄 <strong>PDF de factura</strong> → OCR completo<br>
                            &nbsp;&nbsp;&nbsp;📝 <strong>Datos manuales</strong> → Escribir gasto<br><br>
                            🤖 <strong>Procesamiento Automático:</strong><br>
                            • 📅 Fecha de la factura<br>
                            • 💰 Importe total<br>
                            • 🏪 Proveedor/Empresa<br>
                            • 📂 Categoría del gasto<br>
                            • 🧾 Número de factura<br><br>
                            💡 <strong>Tip:</strong> Las fotos deben ser claras y los PDFs legibles.<br><br>
                            <em>¿Con qué apartamento quieres trabajar?</em>
                        </div>
                    </div>
                </div>
                
                <!-- Input del Chat -->
                <div style="padding: 20px; border-top: 1px solid #e2e8f0; background: white; border-radius: 0 0 12px 12px;">
                    <!-- Selector de Apartamento -->
                    <div id="apartmentSelector" style="margin-bottom: 16px; padding: 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <label style="font-weight: 500; color: #374151; margin-bottom: 8px; display: block;">🏠 Apartamento activo:</label>
                        <select id="chatApartmentSelect" onchange="changeActiveApartment()" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                            <option value="">Selecciona un apartamento...</option>
                        </select>
                    </div>
                    
                    <div style="display: flex; gap: 12px; align-items: end;">
                        <div style="flex: 1;">
                            <textarea id="chatInput" placeholder="Escribe un gasto: 'Restaurante La Marina, 35€, cena' o haz una pregunta..." 
                                     style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; resize: none; font-family: inherit; min-height: 44px; max-height: 120px;"
                                     onkeypress="handleChatKeyPress(event)"></textarea>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <button onclick="sendMessage()" style="background: #667eea; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-weight: 500;">
                                Enviar
                            </button>
                            <label for="fileUpload" style="background: #10b981; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-weight: 500; text-align: center; font-size: 14px;">
                                📄 Archivo
                            </label>
                            <input type="file" id="fileUpload" accept="image/*,.pdf" style="display: none;" onchange="handleFileUpload(event)">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

# ---------- GESTIÓN DE CUENTAS ----------

@router.get("/account-settings", response_class=HTMLResponse)
async def account_settings_page(request: Request):
    """Página de configuración de la cuenta"""
    # TODO: Implementar página de configuración
    return HTMLResponse("""
    <html>
    <head><title>Configuración de Cuenta</title></head>
    <body>
        <h1>🚧 Configuración de Cuenta</h1>
        <p>Esta página está en desarrollo.</p>
        <a href="/multiuser/dashboard">← Volver al Dashboard</a>
    </body>
    </html>
    """)

@router.get("/create-account", response_class=HTMLResponse)
async def create_account_page(request: Request):
    """Página para crear nueva cuenta adicional"""
    # TODO: Implementar página de creación de cuenta adicional
    return HTMLResponse("""
    <html>
    <head><title>Crear Nueva Cuenta</title></head>
    <body>
        <h1>➕ Crear Nueva Cuenta</h1>
        <p>Esta funcionalidad está en desarrollo.</p>
        <a href="/multiuser/account-selector">← Volver al Selector</a>
    </body>
    </html>
    """)

# ---------- PANEL DE SUPERADMINISTRADOR ----------

@router.get("/superadmin", response_class=HTMLResponse)
async def superadmin_panel(request: Request):
    """Panel de superadministrador"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Superadministrador</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; background: #f5f5f5;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
            }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { 
                background: white; padding: 20px; border-radius: 12px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .btn {
                display: inline-block; padding: 10px 20px; background: #667eea;
                color: white; text-decoration: none; border-radius: 6px; margin: 5px;
            }
            .btn:hover { background: #5a67d8; }
            .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }
            .stat { background: white; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-number { font-size: 24px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👑 Panel de Superadministrador</h1>
                <p>Control total del sistema SES.GASTOS</p>
            </div>

            <div class="stats" id="systemStats">
                <!-- Las estadísticas se cargarán dinámicamente -->
            </div>

            <div class="grid">
                <div class="card">
                    <h3>🏢 Gestión de Cuentas</h3>
                    <p>Administrar todas las cuentas de anfitriones</p>
                    <a href="/api/v1/accounts/" class="btn">Ver API Cuentas</a>
                    <a href="#" class="btn" onclick="loadAccounts()">Listar Cuentas</a>
                </div>

                <div class="card">
                    <h3>👥 Gestión de Usuarios</h3>
                    <p>Administrar usuarios del sistema</p>
                    <a href="#" class="btn" onclick="loadUsers()">Ver Usuarios</a>
                    <a href="#" class="btn" onclick="createUser()">Crear Usuario</a>
                </div>

                <div class="card">
                    <h3>🏠 Apartamentos Globales</h3>
                    <p>Vista global de todos los apartamentos</p>
                    <a href="/api/v1/apartments/" class="btn">API Apartamentos</a>
                    <a href="#" class="btn" onclick="loadApartments()">Ver Todos</a>
                </div>

                <div class="card">
                    <h3>🔧 Migración y Mantenimiento</h3>
                    <p>Herramientas de sistema</p>
                    <a href="/migrate/status" class="btn">Estado Migración</a>
                    <a href="#" class="btn" onclick="runMigration()">Migrar a Multiusuario</a>
                </div>

                <div class="card">
                    <h3>📊 Estadísticas del Sistema</h3>
                    <p>Métricas y análisis</p>
                    <a href="/api/v1/dashboard/" class="btn">Dashboard Global</a>
                    <a href="#" class="btn" onclick="loadStats()">Actualizar Stats</a>
                </div>

                <div class="card">
                    <h3>🤖 Bot de Telegram</h3>
                    <p>Estado y configuración del bot</p>
                    <a href="/bot/status" class="btn">Estado Bot</a>
                    <a href="/bot/diagnose" class="btn">Diagnóstico</a>
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h3>🔍 Consola de Administración</h3>
                <div id="adminConsole" style="background: #f8f9fa; padding: 15px; border-radius: 6px; font-family: monospace; min-height: 200px; margin-top: 10px;">
                    Consola lista. Usa los botones de arriba para cargar información.
                </div>
            </div>
        </div>

        <script>
            function log(message) {
                const console = document.getElementById('adminConsole');
                console.innerHTML += new Date().toLocaleTimeString() + ' - ' + message + '\\n';
                console.scrollTop = console.scrollHeight;
            }

            async function apiCall(url, method = 'GET') {
                const token = localStorage.getItem('access_token');
                try {
                    const response = await fetch(url, {
                        method,
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    return await response.json();
                } catch (error) {
                    log('Error: ' + error.message);
                    return null;
                }
            }

            async function loadStats() {
                log('Cargando estadísticas del sistema...');
                const stats = await apiCall('/migrate/status');
                if (stats) {
                    document.getElementById('systemStats').innerHTML = `
                        <div class="stat">
                            <div class="stat-number">${stats.apartments?.total || 0}</div>
                            <div class="stat-label">Apartamentos</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${stats.accounts?.total || 0}</div>
                            <div class="stat-label">Cuentas</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${stats.users?.total || 0}</div>
                            <div class="stat-label">Usuarios</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${stats.system_ready ? '✅' : '⚠️'}</div>
                            <div class="stat-label">Sistema</div>
                        </div>
                    `;
                    log('Estadísticas actualizadas');
                }
            }

            async function loadAccounts() {
                log('Cargando cuentas...');
                const accounts = await apiCall('/api/v1/accounts/?include_stats=true');
                if (accounts) {
                    log(`Encontradas ${accounts.length} cuentas:`);
                    accounts.forEach(acc => {
                        log(`- ${acc.name} (@${acc.slug}) - ${acc.apartments_count} apts, ${acc.users_count} users`);
                    });
                }
            }

            async function runMigration() {
                if (confirm('¿Migrar datos existentes al sistema multiusuario?')) {
                    log('Ejecutando migración...');
                    const result = await apiCall('/migrate/to-multiuser', 'POST');
                    if (result) {
                        log('Migración completada: ' + result.message);
                        if (result.details) {
                            result.details.forEach(detail => log('  ' + detail));
                        }
                    }
                }
            }

            // Cargar estadísticas al inicio
            loadStats();
        </script>
    </body>
    </html>
    """)

# ---------- PÁGINAS DE ERROR ----------

@router.get("/unauthorized", response_class=HTMLResponse)
async def unauthorized_page(request: Request):
    """Página de acceso no autorizado"""
    return HTMLResponse("""
    <html>
    <head><title>Acceso No Autorizado</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🚫 Acceso No Autorizado</h1>
        <p>No tienes permisos para acceder a esta página.</p>
        <a href="/multiuser/login">Iniciar Sesión</a> | 
        <a href="/multiuser/account-selector">Seleccionar Cuenta</a>
    </body>
    </html>
    """)

# ---------- REDIRECCIONES ----------

@router.get("/", response_class=HTMLResponse)
async def multiuser_home(request: Request):
    """Página principal del sistema multiusuario"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SES.GASTOS - Sistema Multiusuario</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container { 
                background: white; padding: 40px; border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; max-width: 500px;
            }
            .logo { font-size: 48px; margin-bottom: 16px; }
            h1 { color: #333; margin-bottom: 16px; }
            p { color: #666; margin-bottom: 32px; line-height: 1.6; }
            .btn { 
                display: inline-block; padding: 12px 24px; margin: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; text-decoration: none; border-radius: 8px;
                font-weight: 600; transition: transform 0.2s;
            }
            .btn:hover { transform: translateY(-2px); }
            .btn-secondary { 
                background: #f8f9fa; color: #333; border: 2px solid #e1e5e9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🏠</div>
            <h1>SES.GASTOS</h1>
            <p>Sistema de Gestión de Apartamentos Turísticos con IA</p>
            
            <a href="/multiuser/login" class="btn">Iniciar Sesión</a>
            <a href="/multiuser/register" class="btn btn-secondary">Registrar Cuenta</a>
            
            <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee;">
                <p style="font-size: 14px; color: #999;">
                    ¿Eres administrador del sistema?
                    <a href="/multiuser/login" style="color: #667eea;">Acceder como SuperAdmin</a>
                </p>
            </div>
        </div>

        <script>
            // Auto-redirigir si ya está logueado
            const token = localStorage.getItem('access_token');
            if (token) {
                const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
                if (userData.is_superadmin) {
                    window.location.href = '/multiuser/superadmin';
                } else {
                    window.location.href = '/multiuser/account-selector';
                }
            }
        </script>
    </body>
    </html>
    """)

# ---------- API DE UTILIDADES ----------

@router.get("/api/user-context")
async def get_user_context(request: Request):
    """Obtener contexto del usuario para JavaScript"""
    # Este endpoint se puede usar desde JavaScript para obtener información del usuario
    # sin necesidad de autenticación Bearer (usando cookies si las implementamos)
    return {
        "authenticated": False,
        "message": "Use /api/v1/auth/me with Bearer token"
    }