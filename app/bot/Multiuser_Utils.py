# app/bot/Multiuser_Utils.py
"""
Utilidades para el bot de Telegram con sistema multiusuario
"""
from __future__ import annotations

import os
import json
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Configuración
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("API_URL") or "http://localhost:8000"
INTERNAL_KEY = os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")

# Cache de usuarios y cuentas
USER_CACHE = {}
ACCOUNT_CACHE = {}

class MultiuserBotError(Exception):
    """Excepción personalizada para errores del bot multiusuario"""
    pass

# ---------- GESTIÓN DE USUARIOS ----------

def register_telegram_user(telegram_id: int, email: str, full_name: str, account_name: str) -> Tuple[bool, str]:
    """
    Registrar nuevo usuario de Telegram con su cuenta
    """
    try:
        api_base = API_BASE_URL.rstrip("/")
        
        # Registrar usuario y crear cuenta
        response = requests.post(
            f"{api_base}/api/v1/auth/register",
            json={
                "email": email,
                "full_name": full_name,
                "password": f"telegram_{telegram_id}",  # Contraseña temporal
                "account_name": account_name
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Guardar en cache
            USER_CACHE[telegram_id] = {
                "user_id": data["user"]["id"],
                "email": email,
                "full_name": full_name,
                "access_token": data["access_token"],
                "accounts": data["accounts"],
                "current_account_id": data["default_account_id"]
            }
            
            return True, f"Usuario registrado exitosamente. Cuenta: {account_name}"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Error en el registro")
            
    except Exception as e:
        return False, f"Error registrando usuario: {str(e)}"

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtener datos del usuario por su Telegram ID
    """
    return USER_CACHE.get(telegram_id)

def authenticate_user_by_email(telegram_id: int, email: str, password: str) -> Tuple[bool, str]:
    """
    Autenticar usuario existente por email y contraseña
    """
    try:
        api_base = API_BASE_URL.rstrip("/")
        
        response = requests.post(
            f"{api_base}/api/v1/auth/login",
            json={
                "email": email,
                "password": password
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Guardar en cache
            USER_CACHE[telegram_id] = {
                "user_id": data["user"]["id"],
                "email": email,
                "full_name": data["user"]["full_name"],
                "access_token": data["access_token"],
                "accounts": data["accounts"],
                "current_account_id": data["default_account_id"]
            }
            
            return True, f"Autenticado exitosamente. {len(data['accounts'])} cuentas disponibles"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Credenciales incorrectas")
            
    except Exception as e:
        return False, f"Error en autenticación: {str(e)}"

# ---------- GESTIÓN DE CUENTAS ----------

def get_user_accounts(telegram_id: int) -> List[Dict[str, Any]]:
    """
    Obtener cuentas del usuario
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return []
    
    return user_data.get("accounts", [])

def switch_account(telegram_id: int, account_id: str) -> Tuple[bool, str]:
    """
    Cambiar a una cuenta específica
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return False, "Usuario no autenticado"
    
    # Verificar que el usuario tenga acceso a la cuenta
    user_accounts = user_data.get("accounts", [])
    account = next((acc for acc in user_accounts if acc["id"] == account_id), None)
    
    if not account:
        return False, "No tienes acceso a esa cuenta"
    
    # Cambiar cuenta actual
    user_data["current_account_id"] = account_id
    USER_CACHE[telegram_id] = user_data
    
    return True, f"Cambiado a cuenta: {account['name']}"

def get_current_account(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtener cuenta actual del usuario
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return None
    
    current_account_id = user_data.get("current_account_id")
    if not current_account_id:
        return None
    
    # Buscar la cuenta en la lista de cuentas del usuario
    user_accounts = user_data.get("accounts", [])
    return next((acc for acc in user_accounts if acc["id"] == current_account_id), None)

# ---------- GESTIÓN DE APARTAMENTOS ----------

def get_account_apartments(telegram_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Obtener apartamentos de la cuenta actual
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return False, []
    
    current_account_id = user_data.get("current_account_id")
    if not current_account_id:
        return False, []
    
    try:
        api_base = API_BASE_URL.rstrip("/")
        token = user_data["access_token"]
        
        response = requests.get(
            f"{api_base}/api/v1/apartments/",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Account-ID": current_account_id
            },
            timeout=20
        )
        
        if response.status_code == 200:
            apartments = response.json()
            return True, apartments
        else:
            return False, []
            
    except Exception as e:
        print(f"Error obteniendo apartamentos: {e}")
        return False, []

def get_apartment_by_code(telegram_id: int, apartment_code: str) -> Optional[Dict[str, Any]]:
    """
    Obtener apartamento por código dentro de la cuenta actual
    """
    success, apartments = get_account_apartments(telegram_id)
    if not success:
        return None
    
    return next((apt for apt in apartments if apt["code"].upper() == apartment_code.upper()), None)

# ---------- GESTIÓN DE GASTOS ----------

def send_expense_to_account(telegram_id: int, expense_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Enviar gasto a la cuenta actual del usuario
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return False, "Usuario no autenticado. Usa /login primero"
    
    current_account_id = user_data.get("current_account_id")
    if not current_account_id:
        return False, "No tienes una cuenta seleccionada"
    
    try:
        api_base = API_BASE_URL.rstrip("/")
        token = user_data["access_token"]
        
        # Resolver apartment_id si se proporciona apartment_code
        apartment_code = expense_data.get("apartment_code")
        if apartment_code and not expense_data.get("apartment_id"):
            apartment = get_apartment_by_code(telegram_id, apartment_code)
            if not apartment:
                return False, f"Apartamento '{apartment_code}' no encontrado en tu cuenta"
            expense_data["apartment_id"] = apartment["id"]
        
        # Limpiar datos
        expense_data.pop("apartment_code", None)
        
        # Enviar gasto
        response = requests.post(
            f"{api_base}/api/v1/expenses/",
            json=expense_data,
            headers={
                "Authorization": f"Bearer {token}",
                "X-Account-ID": current_account_id,
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code in (200, 201):
            return True, "Gasto registrado exitosamente"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Error registrando gasto")
            
    except Exception as e:
        return False, f"Error enviando gasto: {str(e)}"

# ---------- COMANDOS DEL BOT ----------

def format_user_status(telegram_id: int) -> str:
    """
    Formatear estado del usuario para mostrar en Telegram
    """
    user_data = USER_CACHE.get(telegram_id)
    if not user_data:
        return "❌ No autenticado\n\nUsa /login para autenticarte"
    
    current_account = get_current_account(telegram_id)
    accounts = user_data.get("accounts", [])
    
    status = f"✅ **{user_data['full_name']}**\n"
    status += f"📧 {user_data['email']}\n\n"
    
    if current_account:
        status += f"🏢 **Cuenta actual:** {current_account['name']}\n"
        status += f"🏠 Apartamentos: {current_account.get('apartments_count', 0)}\n"
        status += f"📊 Plan: {current_account.get('subscription_status', 'trial').title()}\n\n"
    
    if len(accounts) > 1:
        status += f"📋 **Otras cuentas disponibles:**\n"
        for acc in accounts:
            if acc["id"] != user_data.get("current_account_id"):
                status += f"• {acc['name']} (@{acc['slug']})\n"
        status += "\nUsa /cuentas para cambiar de cuenta\n"
    
    return status

def format_apartments_list(telegram_id: int) -> str:
    """
    Formatear lista de apartamentos para mostrar en Telegram
    """
    success, apartments = get_account_apartments(telegram_id)
    if not success:
        return "❌ Error obteniendo apartamentos"
    
    if not apartments:
        return "📭 No tienes apartamentos registrados en esta cuenta"
    
    current_account = get_current_account(telegram_id)
    account_name = current_account["name"] if current_account else "Cuenta actual"
    
    result = f"🏠 **Apartamentos en {account_name}:**\n\n"
    
    for apt in apartments:
        status_icon = "✅" if apt.get("is_active") else "⏸️"
        result += f"{status_icon} **{apt['code']}** - {apt.get('name', 'Sin nombre')}\n"
        if apt.get("description"):
            result += f"   📝 {apt['description']}\n"
        result += "\n"
    
    result += f"💡 Usa `/usar CODIGO` para configurar un apartamento\n"
    result += f"📊 Ve tu dashboard: /dashboard"
    
    return result

# ---------- PERSISTENCIA ----------

def save_user_cache_to_file(filepath: str = "multiuser_sessions.json"):
    """
    Guardar cache de usuarios en archivo
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(USER_CACHE, f, indent=2, default=str)
    except Exception as e:
        print(f"Error guardando cache: {e}")

def load_user_cache_from_file(filepath: str = "multiuser_sessions.json"):
    """
    Cargar cache de usuarios desde archivo
    """
    global USER_CACHE
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            USER_CACHE = json.load(f)
    except FileNotFoundError:
        USER_CACHE = {}
    except Exception as e:
        print(f"Error cargando cache: {e}")
        USER_CACHE = {}

# ---------- INICIALIZACIÓN ----------

def initialize_multiuser_bot():
    """
    Inicializar bot multiusuario
    """
    load_user_cache_from_file()
    print(f"[Multiuser Bot] Inicializado con {len(USER_CACHE)} usuarios en cache")
    print(f"[Multiuser Bot] API Base URL: {API_BASE_URL}")

# Inicializar al importar
initialize_multiuser_bot()