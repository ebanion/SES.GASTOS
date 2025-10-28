# 📦 Migración de Datos: SQLite → PostgreSQL

## ⚠️ Importante
Este proyecto ahora **solo funciona con PostgreSQL**. Si tienes datos en un archivo SQLite local (como `test_ses_gastos.db`), sigue estas instrucciones para migrarlos.

---

## 🔍 Archivos SQLite Detectados

Durante la revisión del proyecto, se encontró el siguiente archivo SQLite:

```
/workspace/test_ses_gastos.db (65 KB)
```

---

## 🚀 Método 1: Migración Automática (Recomendado)

### 1. Asegúrate de tener ambas bases de datos accesibles

Primero, verifica que PostgreSQL esté funcionando:

```bash
python3 << EOF
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1")).scalar()
    print("✅ PostgreSQL conectado" if result == 1 else "❌ Error")
EOF
```

### 2. Ejecuta el script de migración

Crea un archivo `migrate_data.py`:

```python
#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URLs de las bases de datos
SQLITE_URL = "sqlite:///test_ses_gastos.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

print("🔄 Iniciando migración de SQLite a PostgreSQL...")
print(f"📁 Origen: {SQLITE_URL}")
print(f"🐘 Destino: PostgreSQL")

# Conectar a ambas bases de datos
sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

SqliteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

# Importar modelos
from app import models
from app.db import Base

# Crear tablas en PostgreSQL si no existen
print("\n1️⃣ Creando estructura de tablas en PostgreSQL...")
Base.metadata.create_all(bind=postgres_engine)
print("✅ Tablas creadas")

# Obtener sesiones
sqlite_db = SqliteSession()
postgres_db = PostgresSession()

try:
    # Migrar Accounts
    print("\n2️⃣ Migrando Accounts...")
    accounts = sqlite_db.query(models.Account).all()
    for account in accounts:
        # Verificar si ya existe
        existing = postgres_db.query(models.Account).filter_by(id=account.id).first()
        if not existing:
            postgres_db.add(models.Account(
                id=account.id,
                name=account.name,
                slug=account.slug,
                description=account.description,
                max_apartments=account.max_apartments,
                is_active=account.is_active,
                created_at=account.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(accounts)} accounts migrados")
    
    # Migrar Users
    print("\n3️⃣ Migrando Users...")
    users = sqlite_db.query(models.User).all()
    for user in users:
        existing = postgres_db.query(models.User).filter_by(id=user.id).first()
        if not existing:
            postgres_db.add(models.User(
                id=user.id,
                email=user.email,
                hashed_password=user.hashed_password,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superadmin=user.is_superadmin,
                created_at=user.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(users)} users migrados")
    
    # Migrar Apartments
    print("\n4️⃣ Migrando Apartments...")
    apartments = sqlite_db.query(models.Apartment).all()
    for apt in apartments:
        existing = postgres_db.query(models.Apartment).filter_by(id=apt.id).first()
        if not existing:
            postgres_db.add(models.Apartment(
                id=apt.id,
                code=apt.code,
                name=apt.name,
                owner_email=apt.owner_email,
                account_id=apt.account_id,
                description=apt.description,
                address=apt.address,
                max_guests=apt.max_guests,
                created_at=apt.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(apartments)} apartments migrados")
    
    # Migrar Expenses
    print("\n5️⃣ Migrando Expenses...")
    expenses = sqlite_db.query(models.Expense).all()
    for expense in expenses:
        existing = postgres_db.query(models.Expense).filter_by(id=expense.id).first()
        if not existing:
            postgres_db.add(models.Expense(
                id=expense.id,
                apartment_id=expense.apartment_id,
                date=expense.date,
                amount_gross=expense.amount_gross,
                currency=expense.currency,
                category=expense.category,
                description=expense.description,
                vendor=expense.vendor,
                source=expense.source,
                telegram_user_id=expense.telegram_user_id,
                created_at=expense.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(expenses)} expenses migrados")
    
    # Migrar Incomes
    print("\n6️⃣ Migrando Incomes...")
    incomes = sqlite_db.query(models.Income).all()
    for income in incomes:
        existing = postgres_db.query(models.Income).filter_by(id=income.id).first()
        if not existing:
            postgres_db.add(models.Income(
                id=income.id,
                apartment_id=income.apartment_id,
                reservation_id=income.reservation_id,
                date=income.date,
                amount_gross=income.amount_gross,
                currency=income.currency,
                status=income.status,
                source=income.source,
                created_at=income.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(incomes)} incomes migrados")
    
    # Migrar Reservations
    print("\n7️⃣ Migrando Reservations...")
    reservations = sqlite_db.query(models.Reservation).all()
    for reservation in reservations:
        existing = postgres_db.query(models.Reservation).filter_by(id=reservation.id).first()
        if not existing:
            postgres_db.add(models.Reservation(
                id=reservation.id,
                apartment_id=reservation.apartment_id,
                guest_name=reservation.guest_name,
                guest_email=reservation.guest_email,
                check_in=reservation.check_in,
                check_out=reservation.check_out,
                num_guests=reservation.num_guests,
                status=reservation.status,
                total_amount=reservation.total_amount,
                source=reservation.source,
                created_at=reservation.created_at
            ))
    postgres_db.commit()
    print(f"✅ {len(reservations)} reservations migrados")
    
    print("\n🎉 ¡Migración completada exitosamente!")
    print(f"\n📊 Resumen:")
    print(f"   Accounts: {len(accounts)}")
    print(f"   Users: {len(users)}")
    print(f"   Apartments: {len(apartments)}")
    print(f"   Expenses: {len(expenses)}")
    print(f"   Incomes: {len(incomes)}")
    print(f"   Reservations: {len(reservations)}")
    
except Exception as e:
    print(f"\n❌ Error durante la migración: {e}")
    postgres_db.rollback()
    raise
finally:
    sqlite_db.close()
    postgres_db.close()
```

### 3. Ejecuta el script:

```bash
python3 migrate_data.py
```

---

## 🛠️ Método 2: Migración Manual con SQL

Si prefieres hacerlo manualmente, puedes exportar e importar usando herramientas:

### 1. Exportar desde SQLite

```bash
sqlite3 test_ses_gastos.db .dump > sqlite_dump.sql
```

### 2. Convertir a formato PostgreSQL

Necesitarás ajustar el SQL porque SQLite y PostgreSQL tienen diferencias:

- Cambiar `INTEGER PRIMARY KEY AUTOINCREMENT` a `SERIAL PRIMARY KEY`
- Cambiar `TEXT` a `VARCHAR` donde sea apropiado
- Ajustar tipos de fecha/hora
- Remover pragmas específicos de SQLite

### 3. Importar a PostgreSQL

```bash
psql "postgresql://user:pass@host:5432/dbname" < postgres_dump.sql
```

---

## 🔧 Método 3: Usando Herramientas de Terceros

### pgloader (Recomendado para migraciones grandes)

```bash
# Instalar pgloader
sudo apt-get install pgloader

# Crear archivo de configuración
cat > migration.load << EOF
LOAD DATABASE
    FROM sqlite://test_ses_gastos.db
    INTO postgresql://user:pass@host:5432/dbname

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '16MB', maintenance_work_mem to '512 MB';
EOF

# Ejecutar migración
pgloader migration.load
```

---

## ✅ Verificación Post-Migración

Después de migrar, verifica que todo esté correcto:

```bash
python3 << EOF
import os
from sqlalchemy import create_engine, text
from app import models
from app.db import SessionLocal

db = SessionLocal()

print("📊 Verificando datos migrados:")
print(f"   Accounts: {db.query(models.Account).count()}")
print(f"   Users: {db.query(models.User).count()}")
print(f"   Apartments: {db.query(models.Apartment).count()}")
print(f"   Expenses: {db.query(models.Expense).count()}")
print(f"   Incomes: {db.query(models.Income).count()}")
print(f"   Reservations: {db.query(models.Reservation).count()}")

db.close()
print("✅ Verificación completada")
EOF
```

---

## 🗑️ Limpieza

Una vez verificado que todo funciona correctamente con PostgreSQL:

```bash
# Hacer backup del archivo SQLite (por seguridad)
mv test_ses_gastos.db test_ses_gastos.db.backup

# O eliminarlo si estás seguro
# rm test_ses_gastos.db
```

---

## 🆘 Solución de Problemas

### Error: "relation already exists"
Ya tienes tablas en PostgreSQL. Usa el Método 1 que verifica duplicados.

### Error: "foreign key constraint"
Asegúrate de migrar las tablas en el orden correcto (Accounts → Users → Apartments → Expenses/Incomes/Reservations).

### Error: "could not connect to database"
Verifica que las variables de entorno de PostgreSQL estén configuradas:
```bash
echo $DATABASE_URL
```

---

## 📞 Soporte

Si encuentras problemas durante la migración:

1. Verifica los logs de la aplicación
2. Asegúrate de que PostgreSQL esté corriendo
3. Verifica las credenciales de conexión
4. Revisa que las tablas estén creadas correctamente

---

## 📝 Notas Finales

- **Siempre haz un backup** de tus datos antes de migrar
- Este proyecto ahora **requiere PostgreSQL** y no funcionará con SQLite
- Los archivos `.db` locales están en `.gitignore` y no se subirán al repositorio
- PostgreSQL ofrece mejor rendimiento, concurrencia y características para producción
