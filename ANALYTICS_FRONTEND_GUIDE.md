# 📊 Guía del Dashboard de Analytics - Frontend

## 🎯 Resumen

Se han implementado **2 versiones del dashboard de analytics** con diseños modernos inspirados en las mejores prácticas de Fullstory y Power BI:

1. **Dashboard Estándar** (`/analytics/`) - Versión limpia y funcional
2. **Dashboard PRO** (`/analytics/pro`) - Versión avanzada con sidebar y visualizaciones profesionales

---

## 🚀 Acceso a los Dashboards

### Dashboard Estándar
```
URL: https://tu-dominio.com/analytics/
```

### Dashboard PRO
```
URL: https://tu-dominio.com/analytics/pro
```

---

## 📱 Dashboard Estándar

### Características
- ✨ Diseño glassmorphism moderno
- 🎨 Fondo con gradiente animado
- 📊 5 pestañas de navegación:
  - **Vista General**: KPIs, salud financiera, alertas
  - **KPIs Hoteleros**: ADR, Ocupación, RevPAR detallados
  - **Gastos**: Análisis por categoría con benchmarking
  - **Fiscal**: Calculadoras IVA e IRPF
  - **Simulador**: Comparador de regímenes fiscales

### Componentes Visuales

#### 1. Estado de Salud Financiera
- **Círculo de puntuación** (0-100) con colores:
  - 🟢 Verde (80-100): Excelente
  - 🟡 Amarillo (50-79): Moderado
  - 🔴 Rojo (0-49): Crítico
- **Métricas principales**:
  - Margen de beneficio
  - Tasa de ocupación
  - Control de gastos

#### 2. KPIs Cards
- 3 tarjetas con métricas hoteleras:
  - **ADR** (Average Daily Rate)
  - **Ocupación** (%)
  - **RevPAR** (Revenue Per Available Room)
- Indicadores de tendencia vs. mes anterior

#### 3. Gráficos
- **Evolución de Ingresos**: Gráfico de barras comparativo
- **Comparativa Mensual**: Métricas de ingreso actual vs. anterior

#### 4. Alertas Fiscales
- Lista de alertas con iconos, colores y mensajes
- Contador de alertas activas
- Fechas de vencimiento

---

## 🎨 Dashboard PRO

### Características Avanzadas
- 🎯 Sidebar fijo con navegación
- 📊 Múltiples páginas especializadas
- 🎨 Paleta de colores profesional
- 📈 Gráficos interactivos avanzados
- 🔄 Actualización automática cada 5 minutos

### Páginas

#### 1. **Vista General** (Overview)
- **Hero Section**: Estado de salud con diseño destacado
- **KPIs Grid**: 4 tarjetas con métricas principales
- **Gráficos**:
  - Evolución de ingresos y gastos (línea)
  - Margen de beneficio (dona)
- **Alertas Grid**: Sistema de notificaciones en cuadrícula

#### 2. **Rendimiento** (Performance)
- **Comparativa Año sobre Año**:
  - Ingresos YoY
  - Gastos YoY
  - Beneficio YoY
  - Ocupación YoY
  - ADR YoY
- Indicadores de cambio porcentual con colores

#### 3. **Fiscal**
- **Calculadora IVA (Modelo 303)**:
  - IVA Repercutido (10%)
  - IVA Soportado
  - Total a pagar
  - Fecha de vencimiento con contador
  - Botón de descarga de borrador

- **Calculadora IRPF (Modelo 130)**:
  - Ingresos totales
  - Gastos deducibles
  - Beneficio neto
  - Pago fraccionado
  - Fecha de vencimiento con contador
  - Botón de descarga de borrador

- **Simulador Fiscal**:
  - Inputs para ingresos y gastos proyectados
  - Comparación de 3 regímenes:
    - Autónomo Régimen General
    - Sociedad Limitada (SL)
    - Módulos
  - Recomendación personalizada
  - Tipo efectivo de cada escenario

#### 4. **Gastos** (Expenses)
- **Gráfico de Dona**: Distribución por categoría
- **Gráfico de Barras Horizontal**: Tu % vs Benchmark
- **Recomendaciones**:
  - ✅ Categorías óptimas
  - ⚠️ Categorías altas
  - 🚨 Categorías muy altas
  - Desglose detallado con sugerencias

#### 5. **Predicciones** (Forecast)
> Pendiente de implementación - Requiere integración con IA

#### 6. **Reportes** (Reports)
> Pendiente de implementación - Exportaciones PDF/Excel

---

## 🎨 Paleta de Colores

### Dashboard Estándar
- **Primario**: Purple gradient (`#667eea` → `#764ba2`)
- **Cards**: Glassmorphism blanco translúcido
- **Métricas**:
  - Verde: `#10b981` (positivo/saludable)
  - Amarillo: `#f59e0b` (advertencia)
  - Rojo: `#ef4444` (crítico)
  - Azul: `#3b82f6` (neutral)
  - Morado: `#8b5cf6` (destacado)

### Dashboard PRO
- **Sidebar**: Dark gradient (`#1e293b` → `#0f172a`)
- **Background**: Light gray (`#f8fafc`)
- **Cards**: White con sombras sutiles
- **Hover**: Lift effect (translateY -2px)

---

## 📊 Librerías Utilizadas

### Frontend
- **Tailwind CSS 3.x**: Framework CSS utility-first
- **Chart.js 4.4.0**: Librería de gráficos
- **Font Awesome 6.4**: Iconos
- **Google Fonts Inter**: Tipografía

### No se requiere instalación
Todos los recursos se cargan desde CDN.

---

## 🔐 Autenticación

Ambos dashboards requieren autenticación. El token se obtiene de:
1. `localStorage.getItem('access_token')`
2. Cookie `access_token`

Si no hay token, el usuario debe ser redirigido a `/login` o `/auth/login`.

---

## 🔄 Actualización de Datos

### Automática
- Cada **5 minutos** se recargan todos los datos automáticamente
- No requiere intervención del usuario

### Manual
El usuario puede refrescar la página para forzar una actualización inmediata.

---

## 📡 Endpoints Consumidos

Todos los endpoints están bajo `/analytics`:

| Endpoint | Descripción |
|----------|-------------|
| `GET /analytics/dashboard` | Dashboard integrado |
| `GET /analytics/kpis` | KPIs hoteleros |
| `GET /analytics/financial-health` | Salud financiera |
| `GET /analytics/expense-analysis` | Análisis de gastos |
| `GET /analytics/fiscal/iva/{year}/{quarter}` | IVA trimestral |
| `GET /analytics/fiscal/irpf/{year}/{quarter}` | IRPF trimestral |
| `GET /analytics/fiscal/alerts` | Alertas fiscales |
| `POST /analytics/fiscal/simulate` | Simulador fiscal |
| `GET /analytics/year-over-year` | Comparativa YoY |

---

## 🎯 UX Highlights

### Animaciones
- **Hover effects** en todas las cards
- **Pulse animation** en badges de alerta
- **Smooth transitions** (0.3s ease)
- **Loading skeletons** mientras se cargan datos

### Responsive
- ✅ Mobile-first design
- ✅ Tablet optimizado
- ✅ Desktop HD

### Accesibilidad
- Colores con contraste WCAG AA
- Iconos descriptivos
- Mensajes claros en español

---

## 🚀 Siguientes Pasos (Futuras Mejoras)

### Corto Plazo
1. **Exportación de reportes**:
   - PDF con gráficos
   - Excel con datos
   - Envío por email

2. **Filtros avanzados**:
   - Por apartamento
   - Por rango de fechas personalizado
   - Por categoría de gasto

3. **Comparativas**:
   - Multi-apartamento
   - Multi-año
   - Benchmark por zona geográfica

### Medio Plazo
4. **Predicciones con IA**:
   - Forecast de ingresos (3/6/12 meses)
   - Detección de anomalías
   - Recomendaciones automáticas

5. **Notificaciones**:
   - Push notifications
   - Email alerts
   - Telegram bot integration

6. **Dashboards personalizables**:
   - Drag & drop widgets
   - Widgets customizables
   - Temas (claro/oscuro)

### Largo Plazo
7. **Integración con IA generativa**:
   - Chat para consultas en lenguaje natural
   - Generación automática de informes
   - Asistente virtual fiscal

8. **Multi-idioma**:
   - Inglés
   - Francés
   - Alemán

---

## 🐛 Troubleshooting

### El dashboard no carga datos
1. Verificar que el usuario esté autenticado
2. Comprobar que la base de datos tiene datos
3. Revisar la consola del navegador (F12)
4. Verificar que los endpoints del backend estén activos

### Los gráficos no se muestran
1. Verificar que Chart.js se haya cargado correctamente
2. Comprobar que hay datos suficientes (mínimo 1 mes)
3. Revisar errores de JavaScript en consola

### Errores de autenticación
1. Limpiar localStorage: `localStorage.clear()`
2. Limpiar cookies
3. Volver a iniciar sesión
4. Verificar que el token no haya expirado

---

## 📞 Soporte

Para dudas o problemas con el frontend de analytics:
- Revisar la consola del navegador (F12)
- Verificar los logs del servidor
- Comprobar la documentación técnica en `ANALYTICS_MODULE_GUIDE.md`

---

## ✨ Créditos

Diseño inspirado en:
- [Fullstory Analytics](https://www.fullstory.com/ps/data-analytics-portfolio/)
- [Power BI Dashboards](https://blog.bismart.com/power-bi-dashboards-imprescindibles-2025)

Implementado con ❤️ para SES Gastos.
