#!/usr/bin/env python3
"""
Debug bcrypt issue
"""

def test_bcrypt():
    from passlib.context import CryptContext
    
    # Test simple
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    test_password = "Test123"
    print(f"Testing password: '{test_password}' (len: {len(test_password)}, bytes: {len(test_password.encode('utf-8'))})")
    
    try:
        hash_result = pwd_context.hash(test_password)
        print(f"✅ Success: {hash_result[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_bcrypt()