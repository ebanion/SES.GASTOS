#!/usr/bin/env python3
"""
Test simple para verificar el hash de contraseñas
"""

def test_password_hash():
    from passlib.context import CryptContext
    
    # Contexto simple
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Contraseñas de prueba
    test_passwords = [
        "123456",
        "password123",
        "MiContraseña2024!",
        "a" * 50,  # 50 caracteres
        "a" * 72,  # 72 caracteres (límite)
        "a" * 100  # 100 caracteres (debería fallar)
    ]
    
    for password in test_passwords:
        print(f"\nProbando: '{password[:20]}...' (len: {len(password)}, bytes: {len(password.encode('utf-8'))})")
        
        try:
            # Truncar si es necesario
            if len(password) > 50:
                safe_password = password[:50]
                print(f"  Truncado a: '{safe_password[:20]}...' (len: {len(safe_password)})")
            else:
                safe_password = password
            
            # Verificar bytes
            if len(safe_password.encode('utf-8')) > 72:
                while len(safe_password.encode('utf-8')) > 72 and len(safe_password) > 0:
                    safe_password = safe_password[:-1]
                print(f"  Truncado por bytes a: '{safe_password[:20]}...' (bytes: {len(safe_password.encode('utf-8'))})")
            
            # Intentar hash
            hash_result = pwd_context.hash(safe_password)
            print(f"  ✅ Hash exitoso: {hash_result[:30]}...")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_password_hash()