# Filtro por Operador (Operador / Empleado)

Resumen
- Se agregó la funcionalidad para seleccionar un "Operador" (empleado) en los filtros del tablero.
- Al seleccionar una `Unidad de Negocio`, el frontend solicita los operadores que trabajaron en esa unidad (en el rango de fechas seleccionado) y poblá el select de Operador.
- El filtro `empleado_id` se envía a todos los endpoints relevantes para filtrar gráficos, KPIs, tablas y exportes.

Archivos modificados
- backend/api/views.py
  - Nuevo endpoint: `api_operadores_por_unidad` (ruta: `/api/produccion/operadores/`).
  - Se agregó soporte de query param `empleado_id` en los endpoints:
    - `produccion/data/` (agrega filtrado por `empleado_id`)
    - `produccion/kpis/`
    - `produccion/detalle/`
    - `produccion/export-excel/`
    - `combustible/data/`
    - `combustible/kpis/`
    - `combustible/detalle/`
    - `combustible/export-excel/`
    - `combustible/consumo-por-hora/` (se propaga `empleado_id` donde aplica)

- backend/api/urls.py
  - Ruta añadida: `path('produccion/operadores/', views.api_operadores_por_unidad, name='api_operadores_por_unidad')`

- frontend/src/components/FilterSidebar.vue
  - Añadido `select` para `Operador`.
  - Nuevo campo en `filters`: `empleado_id`.
  - Nueva función `loadOperadores()` que consulta `/api/produccion/operadores/?unidad_negocio_id=<id>&fecha_desde=...&fecha_hasta=...`.
  - Al cambiar la `Unidad de Negocio`, se reinician filtros dependientes (`tipo_operacion_id`, `equipo_id`, `empleado_id`) y se cargan `tiposOperacion`, `equipos` y `operadores`.

- frontend/src/views/Dashboard.vue
  - Todas las peticiones que construyen `URLSearchParams` ahora incluyen `empleado_id` cuando está presente en los filtros. Esto permite filtrar gráficas, KPIs, tablas y exportes por operador.

Detalles del endpoint de operadores
- URL: `/api/produccion/operadores/`
- Query params:
  - `unidad_negocio_id` (requerido para devolver operadores; si no se envía, devuelve `[]`)
  - `fecha_desde` (opcional)
  - `fecha_hasta` (opcional)
- Respuesta (JSON):
  - `{ "operadores": [ {"id": <empleado_id>, "nombre": "Empleado <id>"}, ... ] }

Notas y limitaciones
- Actualmente no existe un modelo `Empleado` en el backend. Por eso el endpoint devuelve `nombre` generado como `Empleado <id>` basado en `empleado_id` encontrados en `tablero_produccion`.
- Si dispones de una tabla/tabla de empleados con nombres reales, puedo actualizar `api_operadores_por_unidad` para hacer join y devolver `nombre` real. Indícame:
  - El nombre del modelo o tabla (por ejemplo `Empleado`, `usuarios`)
  - Nombre de la columna `id` y de la columna con el nombre (`nombre`, `full_name`, `first_name/last_name`, etc.)

Cómo probar (rápido)
1. Arrancar backend (desde `o:\django\fgpy\backend`):

```powershell
python manage.py runserver
```

2. Arrancar frontend (desde `o:\django\fgpy\frontend`):

```powershell
npm install
npm run dev
```

3. En el Dashboard:
- Selecciona un rango de fechas.
- Selecciona una `Unidad de Negocio` — el select `Operador` debe poblarse automáticamente.
- Selecciona un `Operador` y pulsa `Aplicar Filtros`.
- Verifica que las gráficas, KPIs y tablas se actualizan según el operador seleccionado.

Posibles mejoras
- Integrar la tabla real de empleados para mostrar nombres legibles.
- Añadir caché frontend para operadores por unidad para evitar consultar repetidamente.
- Soporte multi-select de operadores (si se necesita filtrar por varios operadores a la vez).

Contacto
- Si quieres que integre nombres reales de operadores, proporciona el esquema de la tabla o autorizame a revisar la base de datos para detectar la tabla correspondiente.
