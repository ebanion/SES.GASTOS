# app/simple_auth.py
"""
Autenticación simple sin passlib para evitar problemas de compatibilidad
"""
import hashlib
import secrets
import bcrypt

def simple_hash_password(password: str) -> str:
    """Hash simple y directo usando bcrypt"""
    try:
        # Truncar a 72 bytes si es necesario
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Usar bcrypt directamente
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"[SIMPLE_AUTH] bcrypt failed, using fallback: {e}")
        # Fallback ultra simple con hashlib
        salt = secrets.token_hex(16)
        return f"sha256${salt}${hashlib.sha256((password + salt).encode()).hexdigest()}"

def simple_verify_password(password: str, hashed: str) -> bool:
    """Verificar contraseña simple"""
    try:
        if hashed.startswith("sha256$"):
            # Formato fallback
            parts = hashed.split("$")
            if len(parts) == 3:
                salt = parts[1]
                expected_hash = parts[2]
                actual_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return actual_hash == expected_hash
            return False
        else:
            # bcrypt normal
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            return bcrypt.checkpw(password_bytes, hashed.encode('utf-8'))
    except Exception as e:
        print(f"[SIMPLE_AUTH] Verification failed: {e}")
        return False