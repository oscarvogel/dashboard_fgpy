# Informe Automático de Consumo de Combustible por Equipo

Sistema automático para generar y enviar informes detallados de consumo de combustible por equipo con análisis comparativo de los últimos 6 meses.

## 📋 Características

El informe incluye:

- **Consumo del mes actual** de cada equipo (solo combustibles: GasOil, Nafta, Diesel)
- **Horas/Km trabajados** en el período
- **Consumo por hora/km** (eficiencia en L/hr)
- **Promedio de litros/hora de los últimos 6 meses** para comparación histórica
- **Alertas automáticas** de equipos con consumo/hora elevado (>20% sobre promedio L/hr)
- **Detalle completo de cargas** con filtro interactivo por equipo en el HTML
- **Separación visual** entre combustibles (usados en cálculos) y aceites/lubricantes (solo referencia)
- **Email HTML** con diseño moderno y minimalista
- **Archivo Excel adjunto** con todos los datos detallados en múltiples hojas

## 🚀 Uso

### Opción 1: Comando de Django (Recomendado para automatización)

#### Enviar informe del mes actual
```bash
python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-actual
```

#### Enviar informe del mes anterior
```bash
python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-anterior
```

#### Enviar informe de un mes específico
```bash
python manage.py enviar_informe_combustible --emails admin@empresa.com --mes 3 --year 2024
```

#### Enviar informe de un período personalizado
```bash
python manage.py enviar_informe_combustible --emails admin@empresa.com --fecha-desde 2024-01-01 --fecha-hasta 2024-01-31
```

#### Enviar a múltiples destinatarios
```bash
python manage.py enviar_informe_combustible --emails email1@test.com email2@test.com email3@test.com --mes-actual
```

#### Especificar usuario que solicita
```bash
python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-actual --usuario "Juan Pérez"
```

### Opción 2: API Endpoint

**Endpoint:** `POST /api/informe-combustible/enviar/`

**Headers:**
```
Authorization: Session (debe estar autenticado)
Content-Type: application/json
```

**Body JSON:**
```json
{
  "email": "destino@empresa.com",
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-01-31"
}
```

O múltiples emails:
```json
{
  "email": ["email1@empresa.com", "email2@empresa.com"],
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-01-31"
}
```

**Nota:** Si no se especifican fechas, se usa el mes actual por defecto.

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "El informe se está generando y será enviado a destino@empresa.com"
}
```

### Opción 3: Programación Automática (Cron/Task Scheduler)

#### Linux/macOS (crontab)

Editar crontab:
```bash
crontab -e
```

Enviar informe el primer día de cada mes a las 8:00 AM:
```cron
0 8 1 * * cd /ruta/al/proyecto/backend && /ruta/al/venv/bin/python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-anterior
```

#### Windows (Task Scheduler)

Crear un archivo BAT (`enviar_informe.bat`):
```batch
@echo off
cd /d O:\django\fgpy\backend
call ..\venv\Scripts\activate.bat
python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-anterior
```

Luego crear una tarea programada en Task Scheduler que ejecute este archivo.

## 📊 Estructura del Informe

### Email HTML

El email incluye:

1. **Header:** Título del informe y período
2. **KPIs:** Resumen visual con:
   - Consumo total del período
   - Horas/Km totales
   - Número de equipos activos
   - Número de equipos con alerta
3. **Alertas:** Sección destacada con equipos que tienen consumo elevado
4. **Tabla detallada:** Información completa de todos los equipos
5. **Detalle de cargas:** Tabla interactiva con todas las cargas del período
   - **Filtro por equipo:** Selector desplegable para filtrar cargas por móvil específico
   - **Separación visual:** Combustibles con fondo verde claro, aceites/lubricantes con fondo gris
   - **Iconos:** ⛽ para combustibles, 🛢️ para aceites
   - Información: fecha, equipo, tipo combustible, litros, km/hr, precio, costo total
   - JavaScript embebido para filtrado en tiempo real sin necesidad de servidor
   - **Nota informativa:** Explica que solo combustibles se usan en cálculos

### Archivo Excel

El archivo Excel adjunto contiene 4 hojas:

1. **Resumen:** KPIs generales del período
2. **Detalle de Equipos:** Tabla completa con todos los datos de consumo por equipo
3. **Alertas:** Lista de equipos con consumo elevado (si hay)
4. **Detalle de Cargas:** Registro completo de todas las cargas del período
   - Incluye: fecha, equipo, patente, tipo combustible, **categoría** (Combustible/Aceite), litros, km/hr, precio/litro, costo total, observaciones
   - **Formato con colores:** Combustibles con fondo verde claro, aceites/lubricantes con fondo gris
   - Nota explicativa sobre qué tipos se usan en cálculos
   - Ordenado por fecha descendente y equipo

## 🎨 Estilo del Email

El email HTML tiene un diseño moderno y minimalista con:

- Gradiente púrpura en el header
- Tarjetas de KPIs con estilos claros
- Tabla responsive y bien formateada
- Alertas destacadas en amarillo/naranja
- Colores consistentes y profesionales

## ⚙️ Configuración de Email

Asegúrate de configurar el servidor SMTP en `backend/settings.py` o en el archivo `.env`:

```python
# settings.py o .env
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicación'
DEFAULT_FROM_EMAIL = 'Sistema FGPY <noreply@empresa.com>'
```

## 🔍 Criterio de Alertas

Un equipo se marca como **consumo elevado** si:

- Su **consumo por hora (L/hr) del mes actual** es **20% mayor** que el promedio de litros/hora de los últimos 6 meses

**IMPORTANTE:** Solo se utilizan **combustibles** (GasOil, Nafta, Diesel) para los cálculos. Los aceites hidráulicos y lubricantes se excluyen automáticamente.

**Ejemplo:**
- Si un equipo consumió en promedio 2.5 litros/hora de GasOil en los últimos 6 meses
- Y en el mes actual tiene un consumo de 3.1 litros/hora o más de GasOil
- Se generará una alerta (diferencia del +24%)

**Cálculo del promedio L/hr de 6 meses:**
1. Para cada uno de los últimos 6 meses se calcula: litros de combustible / horas trabajadas
2. Se promedian esos 6 valores de litros/hora
3. Solo se incluyen meses donde el equipo trabajó (horas > 0)

Los equipos con alerta se muestran con:
- Fondo amarillo claro en la tabla
- Icono de advertencia ⚠️
- Sección dedicada de alertas en el email con detalle de la patente y diferencia porcentual

## 📦 Dependencias

Asegúrate de tener instaladas las siguientes dependencias:

```bash
pip install -r requirements.txt
```

Las dependencias necesarias son:
- `django>=5.2.8`
- `openpyxl>=3.1.2` (para generar Excel)
- `python-dateutil>=2.8.2` (para cálculos de fechas)

## 🐛 Troubleshooting

### El email no se envía

1. Verifica la configuración SMTP en settings.py
2. Revisa los logs en la consola del servidor
3. Asegúrate de que el firewall permite conexiones SMTP

### El comando no se encuentra

```bash
python manage.py help enviar_informe_combustible
```

Si no aparece, verifica que el archivo esté en `api/management/commands/enviar_informe_combustible.py`

### Error de importación de dateutil

```bash
pip install python-dateutil
```

## 📝 Notas

- El informe se genera de forma **asíncrona** cuando se usa el endpoint API (usa threading)
- Cuando se usa el comando de management, se ejecuta de forma **síncrona**
- Los datos se calculan en tiempo real al momento de generar el informe
- Solo se incluyen equipos con `activo=True` en la base de datos
- **Los tanques están excluidos** del análisis (equipos cuyo tipo_movil contenga "tanque")
- **Solo combustibles** (GasOil, Nafta, Diesel) se usan para cálculos de consumo y eficiencia
- **Aceites y lubricantes** aparecen en el detalle de cargas solo como referencia
- Solo se muestran equipos que tuvieron consumo en el período analizado

### Tipos de Combustible

**Usados en cálculos:**
- GasOil / Gas Oil
- Nafta
- Diesel

**Solo referencia (NO en cálculos):**
- Aceite Hidráulico
- Aceite de Motor (15W40, etc.)
- Lubricantes
- Otros aceites

## 🔗 Endpoints Relacionados

- `POST /api/informe-combustible/enviar/` - Enviar informe por email
- `GET /api/combustible/data/` - Datos de combustible
- `GET /api/combustible/kpis/` - KPIs de combustible
- `GET /api/combustible/por-equipo/` - Consumo por equipo

## 👥 Autor

Sistema desarrollado para FGPY - Gestión de Producción y Combustible
