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
                if (!token) {
                    window.location.href = '/multiuser/login';
                    return;
                }

                try {
                    const response = await fetch('/api/v1/auth/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        userData = data.user;
                        accountsData = data.accounts;
                        currentAccountId = localStorage.getItem('current_account_id') || data.default_account_id;

                        displayUserInfo();
                        await loadApartments();
                    } else {
                        window.location.href = '/multiuser/login';
                    }
                } catch (error) {
                    console.error('Error loading user data:', error);
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
                
                try {
                    const response = await fetch('/api/v1/apartments/', {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'X-Account-ID': currentAccountId
                        }
                    });

                    if (response.ok) {
                        const apartments = await response.json();
                        displayDashboard(apartments);
                    } else {
                        displayNoApartments();
                    }
                } catch (error) {
                    console.error('Error loading apartments:', error);
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
                            <h3>🤖 Bot de Telegram</h3>
                            <p>Envía fotos de facturas y se procesarán automáticamente</p>
                            <br>
                            <a href="https://t.me/UriApartment_Bot" target="_blank" class="btn" 
                               style="background: #0088cc; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none;">
                                Abrir Bot
                            </a>
                            <button onclick="showBotInstructions()" class="btn" 
                                    style="background: #f8f9fa; color: #333; padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; cursor: pointer;">
                                Ver instrucciones
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
                // Redirigir al dashboard financiero completo (legacy)
                const currentAccount = accountsData.find(acc => acc.id === currentAccountId);
                
                // Opción 1: Dashboard legacy existente
                window.open('/api/v1/dashboard/', '_blank');
                
                // Opción 2: Mostrar información adicional
                alert(`📊 Dashboard Financiero Completo

🏠 Cuenta: ${currentAccount?.name}
📈 Apartamentos: ${apartments.length}

El dashboard completo se abrirá en una nueva pestaña con:
• Gráficos interactivos
• Filtros por apartamento  
• Exportación de datos
• Análisis detallado`);
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

            // Inicializar
            loadUserData();
        </script>
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