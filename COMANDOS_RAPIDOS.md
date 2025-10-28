# ⚡ Comandos Rápidos - PostgreSQL

## 🚀 Verificar y Arrancar

### 1. Verificar Conexión PostgreSQL
```bash
python setup_database.py
```

**✅ Salida esperada:**
```
✅ Conexión a PostgreSQL exitosa
🎯 Base de datos: dbname_zoe8
📊 Versión: 16.4
🎉 Base de datos configurada exitosamente
```

---

### 2. Iniciar la Aplicación
```bash
uvicorn app.main:app --reload
```

**✅ Logs esperados:**
```
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: dbname_zoe8
[startup] ✅ PostgreSQL conectado exitosamente
[startup] ✅ Tablas creadas/verificadas
```

---

### 3. Verificar Estado de la Base de Datos
```bash
# Opción 1: Desde Python
python -c "from app.db import engine; print('✅ DB OK')"

# Opción 2: Desde la API (con la app corriendo)
curl http://localhost:8000/debug/database-status
```

---

## 🔍 Diagnóstico

### Ver Tablas Creadas
```python
python -c "
from app.db import engine, Base
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print('📋 Tablas:', tables)
print(f'✅ Total: {len(tables)} tablas')
"
```

### Ver Conexión Actual
```python
python -c "
from app.db import engine
print('🔗 URL:', str(engine.url))
print('🔌 Pool size:', engine.pool.size())
"
```

---

## 🔧 Mantenimiento

### Recrear Tablas (¡CUIDADO! Elimina datos)
```bash
python -c "
from app.db import Base, engine
from app import models
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('✅ Tablas recreadas')
"
```

### Inicializar Datos de Prueba
```bash
python init_db_direct.py
```

---

## 📊 Verificación de Producción

### Test de Conexión Render/Producción
```bash
# Verificar variables de entorno
echo $DATABASE_URL | grep -o "postgresql://[^:]*:.*@[^/]*/[^?]*"

# Test rápido
python -c "
import os
from sqlalchemy import create_engine, text

url = os.getenv('DATABASE_URL')
if url:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ PostgreSQL OK en producción')
else:
    print('❌ DATABASE_URL no configurada')
"
```

---

## 🐛 Solución de Problemas

### Error: "DATABASE_URL no está configurada"
```bash
# Verificar variable
echo $DATABASE_URL

# Si está vacía, configurarla:
export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

### Error: "No se pudo conectar"
```bash
# Verificar conectividad
nc -zv dpg-d33s6rruibrs73asgjp0-a 5432

# Verificar SSL
python -c "
import ssl
print('✅ SSL disponible' if ssl.OPENSSL_VERSION else '❌ Sin SSL')
"
```

### Ver Logs Detallados
```bash
# Con logs de SQL
python -c "
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from app.db import engine
print('Engine creado con logs SQL')
"
```

---

## 📚 Documentación

- **README_POSTGRESQL.md** - Inicio rápido
- **RESUMEN_MIGRACION.md** - Resumen ejecutivo
- **CAMBIOS_MIGRACION_POSTGRESQL.md** - Detalles técnicos
- **MIGRACION_SQLITE_A_POSTGRESQL.md** - Migrar datos SQLite
- **VERIFICACION_FINAL.txt** - Checklist

---

## ⚡ Atajos Útiles

```bash
# Alias útiles (añadir a ~/.bashrc o ~/.zshrc)
alias pg-check='python setup_database.py'
alias pg-start='uvicorn app.main:app --reload'
alias pg-tables='python -c "from app.db import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"'
alias pg-status='curl -s http://localhost:8000/debug/database-status | python -m json.tool'
```

---

## 🎯 Todo en Uno

```bash
# Script completo de verificación
#!/bin/bash
echo "🔍 Verificando PostgreSQL..."
python setup_database.py && \
echo "✅ Conexión OK" && \
echo "🚀 Iniciando aplicación..." && \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

*Sistema configurado exclusivamente con PostgreSQL ✅*
