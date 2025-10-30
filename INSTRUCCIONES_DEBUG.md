# 🔧 AÑADIR DEBUG=1 EN RENDER

## 📋 PASOS EXACTOS

### 1. Ve a Render Dashboard
https://dashboard.render.com/

### 2. Click en "ses-gastos"

### 3. Click en "Environment" (pestaña arriba)

### 4. Click en "Add Environment Variable"

### 5. Añade:
```
Key: DEBUG
Value: 1
```

### 6. Click "Save Changes"

### 7. Espera 2 minutos (auto-deploy)

---

## ✅ QUÉ VERÁS EN LOS LOGS

Con DEBUG=1, los logs mostrarán:

```
[DB] 🔍 DEBUG: Password length = XX chars
[DB] 🔍 DEBUG: URL total length = XXX chars
[DB] 🔍 DEBUG: URL repr (primeros 60): 'postgresql+psycopg://avnadmin:...'
```

**CRÍTICO:** Verifica que Password length coincida con la longitud real de tu password de Aiven.

---

## 🎯 SI LA LONGITUD NO COINCIDE

Entonces DATABASE_URL en Render tiene la password mal copiada.

**Solución:**
1. Ve a Aiven Dashboard: https://console.aiven.io/
2. Abre tu servicio PostgreSQL
3. Click en "Overview" o "Connection information"
4. Busca "Service URI"
5. Click en el botón **Copy** (📋) - NO tipes manualmente
6. Ve a Render → ses-gastos → Environment → DATABASE_URL
7. Borra completamente
8. Pega lo que copiaste
9. Save Changes

---

*Añade DEBUG=1 ahora y comparte los logs para ver la longitud de la password.*
