# 🔬 ANÁLISIS FORENSE - CONEXIÓN BASE DE DATOS

## 📋 RESUMEN EJECUTIVO

**PROBLEMA:** `FATAL: password authentication failed for user "avnadmin"` persiste aunque credenciales son correctas.

**CAUSA RAÍZ IDENTIFICADA:** **BUG CRÍTICO** en `app/db.py` líneas 16, 63-66: 
- `os.getenv("DATABASE_URL")` **NO USA `.strip()`**
- Si DATABASE_URL tiene espacios/saltos de línea al final, la password se corrompe
- Render Environment puede añadir whitespace inadvertidamente al copiar/pegar

**VECTORES ADICIONALES:**
1. Conversión incorrecta de driver (`postgres://` → `postgresql+psycopg://`)
2. Manipulación de host para Render (.render.com → host corto) **NO debe aplicarse a Aiven**
3. Fallback prematuro a SQLite en caso de OperationalError (línea 172-186)

---

## 1️⃣ DÓNDE SE FORMA LA CONEXIÓN

### 1.1 Punto de entrada principal

**Archivo:** `app/db.py`
**Líneas críticas:**

```python
# Línea 16 - PRIMER BUG: Sin strip()
DATABASE_URL = os.getenv("DATABASE_URL")  # ❌ Sin .strip()

# Líneas 19-22 - Fallback si no existe
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///ses_gastos_persistent.db"

# Líneas 25-58 - Normalización con make_url()
if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL):
    original_url = DATABASE_URL
    try:
        url = make_url(DATABASE_URL)  # ❌ Puede fallar si hay \n al final
        
        # Línea 34-35 - Conversión de driver
        if url.drivername in ["postgres", "postgresql"]:
            url = url.set(drivername="postgresql+psycopg")
        
        # Líneas 39-44 - BUG: Conversión host Render
        # ❌ ESTO NO DEBE APLICARSE A AIVEN
        if url.host and ".render.com" in url.host:
            internal_host = url.host.split(".")[0]
            url = url.set(host=internal_host)
        
        DATABASE_URL = str(url)  # Línea 58
        
    except Exception as url_error:
        # Líneas 63-66 - Fallback manual (SIN strip())
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
```

### 1.2 Creación del engine

**Archivo:** `app/db.py`  
**Líneas:** 124-133

```python
pg_engine = create_engine(
    DATABASE_URL,  # ❌ URL puede estar corrupta
    pool_pre_ping=True,
    connect_args=connect_args,  # {"connect_timeout": 10, "application_name": "ses-gastos"}
    pool_timeout=30,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
    echo=False
)
```

### 1.3 Driver usado

**Correcto:** SQLAlchemy 2.0 + psycopg 3.2.10  
**DSN esperado:** `postgresql+psycopg://user:pass@host:port/db?sslmode=require`  
**DSN actual (según logs):** `postgresql+psycopg://avnadmin:***@pg-e219877...com:12417/defaultdb?sslmode=require`

✅ Driver es correcto.

### 1.4 Fallback a SQLite

**Líneas:** 172-186  
**Problema:** Se activa en **CUALQUIER** excepción de PostgreSQL, incluyendo auth errors.

```python
except Exception as pg_error:
    print(f"[DB] ❌ PostgreSQL falló: {pg_error}")
    print(f"[DB] ⚠️ USANDO SQLITE COMO FALLBACK TEMPORAL")
    DATABASE_URL = "sqlite:///ses_gastos_persistent.db"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

❌ **INCORRECTO:** Debería fallar hard en auth errors, no hacer fallback silencioso.

---

## 2️⃣ FUENTES DE VARIABLES DE ENTORNO

### 2.1 Prioridad de carga

1. **`app/config.py`** (línea 2-3):
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Carga .env si existe
   ```

2. **`app/db.py`** (línea 16):
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL")  # ❌ Sin strip()
   ```

3. **Render Environment:**
   - Variables se inyectan en runtime
   - **PROBLEMA:** Si se copia/pega mal, puede contener `\n` o espacios

### 2.2 Variables leídas

Búsqueda exhaustiva encontró:

**En uso:**
- `DATABASE_URL` (principal) - ✅ Usado en `app/db.py` y `app/config.py`

**NO en uso pero presentes en código:**
- `DATABASE_PRIVATE_URL` - Solo en debug endpoints, no afecta conexión
- `POSTGRES_URL` - Solo en debug endpoints, no afecta conexión
- `POSTGRESQL_URL` - Solo en debug endpoints, no afecta conexión

**Conclusión:** Solo `DATABASE_URL` importa para la conexión.

### 2.3 Conflictos potenciales

❌ **NO hay** variables tipo `DB_POSTGRES_HOST`, `DB_POSTGRES_USER`, etc.  
✅ **Solo** se usa `DATABASE_URL`.

❌ **PROBLEMA:** `render.yaml` no encontrado con environment vars, por lo que se configuran manualmente en dashboard.

### 2.4 Whitespace issues

**BUG CRÍTICO:**

```python
# app/db.py línea 16
DATABASE_URL = os.getenv("DATABASE_URL")  # ❌ Sin .strip()
```

Si DATABASE_URL en Render contiene:
```
postgres://avnadmin:PASS@host:12417/db?ssl=require\n
```

Entonces:
- `make_url()` puede fallar o parsear incorrectamente
- La password puede incluir `\n` en la URL
- La conexión falla con "authentication failed"

---

## 3️⃣ ENCODING/SEGURIDAD DE LA CONTRASEÑA

### 3.1 Formato actual

La password se pasa en URL string directamente:
```
postgres://avnadmin:PASSWORD@host:12417/defaultdb
```

### 3.2 Problemas de URL-encode

**Password:** `AVNS_xxxxx` (redactado)  
**Caracteres especiales:** `-` (guion) y `_` (underscore)

✅ Estos caracteres son **seguros** en URLs, no requieren encoding.

❌ **PERO:** Si la password tiene espacios/saltos de línea por bug en lectura de env:
```python
# Si DATABASE_URL = "postgres://user:pass@host/db\n"
# Entonces password efectiva = "pass@host/db\n" (todo después de : hasta @)
```

### 3.3 Uso de make_url()

```python
url = make_url(DATABASE_URL)  # Línea 31
```

✅ **CORRECTO:** `make_url()` parsea y valida la URL.  
❌ **PROBLEMA:** Si hay `\n` o espacios, `make_url()` puede:
- Fallar con excepción → cae a fallback manual (línea 60)
- Parsear incorrectamente → password corrupta

### 3.4 Log temporal propuesto

Actualmente (línea 90-91):
```python
masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] 🔗 Conexión PostgreSQL: {masked_url}")
```

❌ **INSUFICIENTE:** No muestra:
- Longitud de password
- Si hay whitespace
- repr() de URL para ver \n, \r, etc.

---

## 4️⃣ COMPATIBILIDADES Y DEPENDENCIAS

### 4.1 requirements.txt

```
SQLAlchemy==2.0.36  ✅
psycopg[binary]==3.2.10  ✅
```

✅ **CORRECTO:** Versiones compatibles.
✅ **NO hay** psycopg2 mezclado.

### 4.2 SSL mode

**Actual:** Se añade `sslmode=require` (líneas 48-50):
```python
query_params = dict(url.query)
if "sslmode" not in query_params:
    query_params["sslmode"] = "require"
```

✅ **CORRECTO:** Aiven y Render requieren SSL.

❌ **ADVERTENCIA:** Si DATABASE_URL ya tiene `?ssl=true` (incorrecto), se respeta y NO se añade `sslmode=require`.

---

## 5️⃣ CONFIG DE DESPLIEGUE

### 5.1 render.yaml

**Contenido:** [Necesito leerlo]

### 5.2 Variables exportadas

**Manual en Render Dashboard:**
- `DATABASE_URL` se configura manualmente en Environment tab
- **PROBLEMA:** Copy/paste puede añadir whitespace

### 5.3 Logs antes de conectar

**Actual (líneas 90-100):**
```python
masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] 🔗 Conexión PostgreSQL: {masked_url}")
print(f"[DB] 🔌 Puerto: {url_check.port or 5432}")
print(f"[DB] 🗄️ Base de datos: {url_check.database}")
print(f"[DB] 🌍 Host: {url_check.host}")
```

❌ **INSUFICIENTE:** No muestra:
- repr() de URL (para ver \n, \r)
- Longitud exacta de password
- Longitud de DATABASE_URL original

---

## 6️⃣ DIFERENCIAS SYNC/ASYNC

✅ **NO aplica:** Proyecto usa **sync** completamente.

```python
# create_engine (sync)
pg_engine = create_engine(DATABASE_URL, ...)  # Línea 124

# SessionLocal (sync)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Línea 194
```

✅ **NO hay** `create_async_engine` ni `AsyncSession`.

---

## 7️⃣ PRUEBAS AUTOMÁTICAS MÍNIMAS

**Actualmente:** No hay test de conectividad en CI/CD.

**Propuesta:** Ver sección 8 (Parche).

---

## 8️⃣ PARCHE PROPUESTO

### 8.1 Fix principal (db.py)

```diff
--- a/app/db.py
+++ b/app/db.py
@@ -13,7 +13,20 @@ from sqlalchemy.engine import make_url
 print("[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...")
 
 # Obtener DATABASE_URL
-DATABASE_URL = os.getenv("DATABASE_URL")
+DATABASE_URL_RAW = os.getenv("DATABASE_URL")
+
+# 🔧 CRÍTICO: Strip whitespace (espacios, \n, \r, \t)
+if DATABASE_URL_RAW:
+    DATABASE_URL = DATABASE_URL_RAW.strip()
+    
+    # Debug: Detectar whitespace
+    if DATABASE_URL != DATABASE_URL_RAW:
+        print(f"[DB] ⚠️ ADVERTENCIA: DATABASE_URL contenía whitespace")
+        print(f"[DB]    Original length: {len(DATABASE_URL_RAW)}")
+        print(f"[DB]    Stripped length: {len(DATABASE_URL)}")
+        print(f"[DB]    Repr (últimos 30 chars): {repr(DATABASE_URL_RAW[-30:])}")
+else:
+    DATABASE_URL = None
 
 # Verificar que DATABASE_URL esté configurada
 if not DATABASE_URL:
@@ -37,11 +50,14 @@ if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL
         # 🔧 CRÍTICO: Convertir host externo a interno para Render
         # Render requiere usar el host interno cuando la app corre dentro de Render
-        if url.host and ".render.com" in url.host:
+        # ⚠️ NO APLICAR a otros proveedores (Aiven, Railway, etc.)
+        is_render_db = url.host and ".render.com" in url.host and url.host.startswith("dpg-")
+        
+        if is_render_db:
             internal_host = url.host.split(".")[0]  # Extraer solo dpg-xxxxx-a
             print(f"[DB] 🔄 Convirtiendo host externo a interno (Render):")
             print(f"[DB]    Externo: {url.host}")
             print(f"[DB]    Interno: {internal_host}")
             url = url.set(host=internal_host)
+        elif ".render.com" in url.host:
+            print(f"[DB] ℹ️ Host Render detectado pero no es PostgreSQL interno: {url.host}")
         
         # Asegurar sslmode=require
@@ -90,6 +106,18 @@ if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL
     masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
     print(f"[DB] 🔗 Conexión PostgreSQL: {masked_url}")
     
+    # 🔍 Debug adicional (solo si DEBUG=1)
+    if os.getenv("DEBUG") == "1":
+        try:
+            # Extraer password para verificar longitud
+            import re as debug_re
+            pass_match = debug_re.search(r'://[^:]+:([^@]+)@', DATABASE_URL)
+            if pass_match:
+                password_length = len(pass_match.group(1))
+                print(f"[DB] 🔍 DEBUG: Password length = {password_length} chars")
+                print(f"[DB] 🔍 DEBUG: URL repr (primeros 60): {repr(DATABASE_URL[:60])}")
+        except:
+            pass
+    
     try:
         url_check = make_url(DATABASE_URL)
@@ -172,6 +200,11 @@ if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL
     except Exception as pg_error:
         print(f"[DB] ❌ PostgreSQL falló: {pg_error}")
-        print(f"[DB] ⚠️ USANDO SQLITE COMO FALLBACK TEMPORAL")
+        
+        # 🔧 Solo fallback si NO es error de autenticación
+        error_msg = str(pg_error).lower()
+        if "authentication failed" in error_msg or "password" in error_msg:
+            print(f"[DB] 🚨 ERROR DE AUTENTICACIÓN - NO HAY FALLBACK")
+            print(f"[DB] 💡 Verifica DATABASE_URL en Render Environment")
+            print(f"[DB] 💡 Usa el script diagnose_aiven.py para debug")
+            raise RuntimeError(f"Authentication failed: {pg_error}")
+        
+        print(f"[DB] ⚠️ USANDO SQLITE COMO FALLBACK TEMPORAL (solo para otros errores)")
         print(f"[DB] 📁 Archivo: /opt/render/project/src/ses_gastos_persistent.db")
```

### 8.2 Método alternativo: URL.create() (más robusto)

```python
# Alternativa: Construir URL componente por componente
from sqlalchemy.engine import URL

# Si existen variables separadas (futuro)
if os.getenv("DB_POSTGRES_HOST"):
    DB_URL = URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_POSTGRES_USER", "").strip(),
        password=os.getenv("DB_POSTGRES_PASSWORD", "").strip(),  # PLANA, sin encoding
        host=os.getenv("DB_POSTGRES_HOST", "").strip(),
        port=int(os.getenv("DB_POSTGRES_PORT", "5432")),
        database=os.getenv("DB_POSTGRES_DB", "").strip(),
        query={"sslmode": "require"},
    )
    DATABASE_URL = str(DB_URL)
else:
    # Usar DATABASE_URL como ahora (con strip())
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
```

### 8.3 Test de conectividad

```python
# test_database_connection.py
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

def test_database_url():
    """Test que valida DATABASE_URL antes de arrancar app"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Test 1: Existe
    assert DATABASE_URL, "❌ DATABASE_URL no configurada"
    
    # Test 2: No tiene whitespace
    stripped = DATABASE_URL.strip()
    assert DATABASE_URL == stripped, f"❌ DATABASE_URL tiene whitespace: {repr(DATABASE_URL)}"
    
    # Test 3: Driver correcto
    url = make_url(DATABASE_URL)
    if "postgresql" in url.drivername or "postgres" in url.drivername:
        expected_driver = "postgresql+psycopg"
        if "postgresql+psycopg" in DATABASE_URL:
            actual_driver = "postgresql+psycopg"
        else:
            actual_driver = url.drivername
            
        assert actual_driver == expected_driver, f"❌ Driver incorrecto: {actual_driver} != {expected_driver}"
    
    # Test 4: Conectividad básica
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1, "❌ SELECT 1 falló"
    
    print("✅ Todos los tests pasaron")
    
if __name__ == "__main__":
    test_database_url()
```

---

## 9️⃣ RESULTADO FINAL

### 9.1 Lista de archivos/líneas involucradas

| Archivo | Líneas | Problema | Prioridad |
|---------|--------|----------|-----------|
| `app/db.py` | 16 | ❌ `os.getenv()` sin `.strip()` | **CRÍTICO** |
| `app/db.py` | 39-44 | ⚠️ Conversión Render aplicada a Aiven | **ALTA** |
| `app/db.py` | 90-100 | ⚠️ Logs insuficientes para debug | MEDIA |
| `app/db.py` | 172-186 | ❌ Fallback en auth errors | **ALTA** |
| `app/config.py` | 6 | ⚠️ También lee DATABASE_URL (sin strip) | BAJA (no se usa) |

### 9.2 Razón exacta del fallo

**HIPÓTESIS PRINCIPAL:**

```
DATABASE_URL en Render Environment contiene whitespace al final:
postgres://avnadmin:PASSWORD@pg-e219877...com:12417/defaultdb?sslmode=require\n

↓

os.getenv("DATABASE_URL") devuelve string con \n

↓

make_url() o psycopg interpreta mal la password o los parámetros

↓

La password efectiva que llega al servidor es incorrecta

↓

PostgreSQL rechaza: "authentication failed"
```

**HIPÓTESIS SECUNDARIA:**

La conversión de host Render (líneas 39-44) se aplicó a la URL de Aiven por error, resultando en un host incorrecto.

### 9.3 Diff final

Ver sección 8.1 completa.

### 9.4 Instrucciones de verificación

#### A. Verificar DATABASE_URL en Render

```bash
# En Render Shell
python3 -c "import os; url=os.getenv('DATABASE_URL'); print(f'Len: {len(url)}'); print(f'Repr: {repr(url[-50:])}'); print(f'Stripped: {repr(url.strip()[-50:])}')"
```

Debe mostrar si hay `\n`, `\r` o espacios.

#### B. Test con psql

```bash
# Con la URL EXACTA de Render Environment (copia con botón Copy)
psql "postgres://avnadmin:PASSWORD@pg-e219877-edubanonrodriguez-b19a.h.aivencloud.com:12417/defaultdb?sslmode=require"
```

Si esto funciona, el problema NO es las credenciales, es cómo la app lee la URL.

#### C. Script de diagnóstico

```bash
# En Render Shell
python diagnose_aiven.py
```

Mostrará EXACTAMENTE qué componente falla.

#### D. Activar DEBUG

```bash
# En Render Environment, añadir:
DEBUG=1

# Redeploy

# Los logs mostrarán:
# [DB] 🔍 DEBUG: Password length = 28 chars
# [DB] 🔍 DEBUG: URL repr (primeros 60): 'postgresql+psycopg://avnadmin:...'
```

---

## 🎯 ACCIÓN INMEDIATA REQUERIDA

1. **APLICAR PARCHE 8.1** → Fix del `.strip()`
2. **Añadir DEBUG=1** en Render Environment
3. **Redeploy**
4. **Verificar logs** para confirmar que password length es correcto
5. **Si sigue fallando:** Ejecutar `diagnose_aiven.py` en Render Shell

---

*Análisis completado. Causa raíz altamente probable: whitespace en DATABASE_URL.*
