# 🔍 CÓMO EJECUTAR EL DIAGNÓSTICO EN RENDER

## ⚡ PASOS RÁPIDOS

### 1. Ve a Render Shell
1. Abre Render Dashboard
2. Click en **ses-gastos** (tu servicio web)
3. Click en la pestaña **"Shell"** (arriba a la derecha)
4. Espera a que se abra la terminal

### 2. Ejecuta el Script de Diagnóstico
Copia y pega este comando en Render Shell:

```bash
python test_render_connection.py
```

### 3. Lee el Resultado

#### ✅ Si dice "DIAGNÓSTICO EXITOSO":
```
✅ ¡DIAGNÓSTICO EXITOSO! La conexión PostgreSQL FUNCIONA
```

**Entonces el problema está en cómo SQLAlchemy parsea la URL.**
Dame el output completo y lo arreglo.

#### ❌ Si dice "CONTRASEÑA INCORRECTA":
```
❌ CONTRASEÑA INCORRECTA
La contraseña en DATABASE_URL NO coincide con la de PostgreSQL
```

**Entonces:**
1. Ve a Render Dashboard → **Databases** → **dbname_datos**
2. Busca **"Internal Connection String"**
3. Click en botón **"Copy"** 📋
4. Ve a **ses-gastos** → **Environment** → **DATABASE_URL**
5. **BORRA** completamente DATABASE_URL
6. **PEGA** exactamente lo que copiaste
7. **AÑADE manualmente:**
   - Después del host (antes de `/`): `:5432`
   - Al final: `?sslmode=require`
8. Debe quedar así:
   ```
   postgresql://dbname_datos_user:PASSWORD@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require
   ```
9. **Save Changes**
10. **Manual Deploy**

---

## 🎯 POR QUÉ ESTO FUNCIONARÁ

Este script:
- ✅ Lee DATABASE_URL directamente del entorno (como la app)
- ✅ Prueba conexión con psycopg DIRECTO (sin SQLAlchemy)
- ✅ Te dice EXACTAMENTE qué componente falla
- ✅ Verifica cada parte de la URL
- ✅ Te da la solución específica para tu error

---

## 📋 Cómo Compartir el Resultado

Después de ejecutar `python test_render_connection.py`, copia TODO el output y pégalo aquí.

Eso me dirá EXACTAMENTE qué está mal.

---

## 🚨 SI RENDER SHELL NO FUNCIONA

Ejecuta esto en tu terminal local:

```bash
# Setear la variable (CAMBIA por tu URL real de Render)
export DATABASE_URL="postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require"

# Ejecutar script
python test_render_connection.py
```

⚠️ **IMPORTANTE:** Si funciona localmente pero NO en Render, significa que la variable `DATABASE_URL` en Render Environment está mal configurada.

---

*Este script es la única forma de saber QUÉ COÑO está pasando exactamente.*
