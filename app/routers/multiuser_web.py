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

# ---------- SELECTOR DE CUENTAS ----------

@router.get("/account-selector", response_class=HTMLResponse)
async def account_selector_page(request: Request):
    """Página para seleccionar cuenta cuando el usuario tiene múltiples"""
    return templates.TemplateResponse("account_selector.html", {"request": request})

# ---------- DASHBOARD PRINCIPAL ----------

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard principal de la cuenta seleccionada"""
    # Por ahora redirigir al dashboard existente
    # TODO: Crear dashboard específico multiusuario
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "multiuser": True
    })

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