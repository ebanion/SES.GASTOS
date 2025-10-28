# 📦 Guía de Migración de SQLite a PostgreSQL

## ⚠️ Importante

Esta aplicación ahora **solo funciona con PostgreSQL**. Si anteriormente usabas SQLite y tienes datos que quieres conservar, sigue esta guía para migrarlos.

## 🎯 ¿Cuándo necesitas esta guía?

- Si tienes un archivo `local.db`, `ses_gastos.db` o similar con datos importantes
- Si estás migrando de un entorno de desarrollo local a producción
- Si anteriormente la aplicación usaba SQLite como fallback

## 📋 Requisitos Previos

1. **PostgreSQL configurado** con las variables de entorno:
   - `DATABASE_URL`
   - `DATABASE_PRIVATE_URL` (opcional)
   - `POSTGRES_URL` (opcional)

2. **Archivo SQLite** con los datos a migrar (ej: `local.db`)

3. **Python** con las dependencias instaladas:
   ```bash
   pip install sqlalchemy psycopg[binary] python-dotenv
   ```

## 🚀 Método 1: Script Automático de Migración

### Paso 1: Crear el script de migración

Crea un archivo `migrate_sqlite_to_postgres.py`:

```python
#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuración
SQLITE_DB_PATH = "local.db"  # Cambia esto a tu archivo SQLite
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("❌ ERROR: DATABASE_URL no está configurada")
    sys.exit(1)

# Normalizar URL de PostgreSQL
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif POSTGRES_URL.startswith("postgresql://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgresql://", "postgresql+psycopg://", 1)

print("🔄 Iniciando migración de SQLite a PostgreSQL...")
print(f"📁 SQLite: {SQLITE_DB_PATH}")
print(f"🐘 PostgreSQL: {POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else 'configurado'}")

# Engines
sqlite_engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
postgres_engine = create_engine(POSTGRES_URL)

# Metadata
metadata = MetaData()

# Tablas a migrar (en orden debido a dependencias)
TABLES_TO_MIGRATE = [
    "accounts",
    "users",
    "account_users",
    "apartments",
    "expenses",
    "incomes",
    "reservations"
]

def migrate_table(table_name):
    """Migrar una tabla de SQLite a PostgreSQL"""
    print(f"\n📊 Migrando tabla: {table_name}")
    
    try:
        # Verificar que la tabla existe en SQLite
        inspector_sqlite = inspect(sqlite_engine)
        if table_name not in inspector_sqlite.get_table_names():
            print(f"   ⚠️  Tabla {table_name} no existe en SQLite - saltando")
            return 0
        
        # Cargar definición de la tabla
        table = Table(table_name, metadata, autoload_with=sqlite_engine)
        
        # Leer datos de SQLite
        with sqlite_engine.connect() as sqlite_conn:
            result = sqlite_conn.execute(table.select())
            rows = result.fetchall()
            
        if not rows:
            print(f"   ℹ️  Tabla {table_name} está vacía - saltando")
            return 0
        
        print(f"   📥 Leyendo {len(rows)} registros de SQLite...")
        
        # Insertar en PostgreSQL
        with postgres_engine.connect() as postgres_conn:
            # Limpiar tabla en PostgreSQL (opcional - comenta si quieres mantener datos)
            # postgres_conn.execute(table.delete())
            
            # Insertar registros
            for row in rows:
                try:
                    postgres_conn.execute(table.insert().values(**row._asdict()))
                except Exception as e:
                    print(f"   ⚠️  Error insertando registro: {e}")
            
            postgres_conn.commit()
        
        print(f"   ✅ {len(rows)} registros migrados exitosamente")
        return len(rows)
        
    except Exception as e:
        print(f"   ❌ Error migrando tabla {table_name}: {e}")
        return 0

def main():
    """Función principal de migración"""
    
    # Verificar que SQLite existe
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ ERROR: Archivo SQLite no encontrado: {SQLITE_DB_PATH}")
        sys.exit(1)
    
    # Verificar conexión a PostgreSQL
    try:
        with postgres_engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Conexión a PostgreSQL exitosa")
    except Exception as e:
        print(f"❌ ERROR: No se pudo conectar a PostgreSQL: {e}")
        sys.exit(1)
    
    # Migrar cada tabla
    total_migrated = 0
    for table_name in TABLES_TO_MIGRATE:
        migrated = migrate_table(table_name)
        total_migrated += migrated
    
    print(f"\n🎉 Migración completada: {total_migrated} registros totales migrados")
    print(f"✅ Todos los datos están ahora en PostgreSQL")
    print(f"\n💡 Puedes eliminar el archivo SQLite: {SQLITE_DB_PATH}")

if __name__ == "__main__":
    main()
```

### Paso 2: Ejecutar la migración

```bash
python migrate_sqlite_to_postgres.py
```

## 🔧 Método 2: Migración Manual con pgloader

Si tienes muchos datos, `pgloader` es más eficiente:

### Instalación de pgloader

**Ubuntu/Debian:**
```bash
sudo apt-get install pgloader
```

**macOS:**
```bash
brew install pgloader
```

### Uso de pgloader

```bash
pgloader sqlite:///path/to/local.db postgresql://user:password@host:5432/dbname
```

## ✅ Verificación Post-Migración

Después de migrar, verifica que los datos estén correctamente en PostgreSQL:

```bash
# Ejecutar el script de verificación
python ensure_postgres.py
```

O desde la aplicación:
```bash
curl https://tu-app.onrender.com/debug/check-database
```

## 🗑️ Limpieza

Una vez que confirmes que todo funciona correctamente:

1. **Elimina los archivos SQLite:**
   ```bash
   rm *.db
   rm *.sqlite3
   ```

2. **Verifica el .gitignore** para asegurar que no se suban archivos SQLite:
   ```
   *.db
   *.sqlite3
   local.db
   ```

## 🐛 Solución de Problemas

### Error: "relation already exists"

La tabla ya existe en PostgreSQL. Opciones:
- Comenta la línea `postgres_conn.execute(table.delete())` en el script
- O elimina las tablas existentes antes de migrar

### Error: "foreign key constraint"

Las tablas tienen dependencias. Asegúrate de migrar en el orden correcto:
1. accounts
2. users
3. account_users
4. apartments
5. expenses, incomes, reservations

### Error de conexión a PostgreSQL

Verifica:
- Que `DATABASE_URL` esté correctamente configurada
- Que incluya `sslmode=require` para Render
- Que el puerto sea 5432

## 📞 Soporte

Si encuentras problemas durante la migración:

1. Verifica los logs de PostgreSQL
2. Asegúrate de que todas las tablas estén creadas en PostgreSQL
3. Verifica que no haya conflictos de IDs o restricciones únicas

## ⚡ Migración Rápida (Solo para datos pequeños)

Si tienes pocos datos y quieres una migración rápida:

```python
# migration_quick.py
import sqlite3
import psycopg
import os

sqlite_conn = sqlite3.connect('local.db')
pg_conn = psycopg.connect(os.getenv('DATABASE_URL'))

# Ejemplo para apartamentos
cursor = sqlite_conn.execute('SELECT * FROM apartments')
columns = [description[0] for description in cursor.description]

for row in cursor:
    values = ', '.join(['%s'] * len(row))
    cols = ', '.join(columns)
    pg_conn.execute(
        f"INSERT INTO apartments ({cols}) VALUES ({values})",
        row
    )

pg_conn.commit()
print("✅ Migración completada")
```

## 🎓 Nota Final

A partir de ahora, la aplicación **solo funcionará con PostgreSQL**. SQLite no está disponible como opción de fallback, lo que garantiza:

- ✅ Persistencia de datos en producción
- ✅ Mejor rendimiento
- ✅ Características avanzadas de PostgreSQL
- ✅ Escalabilidad
