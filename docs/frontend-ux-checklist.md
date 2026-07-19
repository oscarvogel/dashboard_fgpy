# Checklist de mejoras UX del frontend

Auditoría realizada sobre el frontend Vue/Vite en `frontend`, validando el login con Browser en `http://localhost:5180` y complementando con revisión de código.

## Correcciones prioritarias

- [x] Corregir textos con encoding roto en componentes y vistas.
  - Se corrigieron mojibakes en `src/views/Login.vue`, `src/components/NavBar.vue`, `src/components/FilterSidebar.vue`, `src/views/Dashboard.vue`, `src/views/Produccion.vue`, `src/views/Profile.vue` y `src/assets/index.css`.

- [x] Asociar labels con sus controles mediante `for` e `id`.
  - Aplicado en login, filtros, reporte de producción y perfil.
  - Verificado en Browser: `Usuario` y `Contraseña` del login resuelven por label.

- [x] Normalizar errores de login con mensajes amigables.
  - Se evita mostrar errores técnicos como `Method Not Allowed`.

- [x] Agregar estados visibles de error en dashboard y combustible.
  - Se agregó alerta visible en resumen/dashboard.
  - Se agregó alerta visible y estados de carga/sin datos en combustible.

- [x] Revisar navegación superior para mobile.
  - Se ajustó el `NavBar` para permitir wrapping y distribución vertical en pantallas chicas.
  - Pendiente opcional: convertirlo en menú colapsable si el número de rutas crece.

## Formularios y filtros

- [x] Definir comportamiento consistente para filtros.
  - Estado actual: se mantiene aplicación manual con `Aplicar Filtros`.
  - Se agregó una nota visible en el panel de filtros: los cambios se aplican al presionar `Aplicar Filtros`.

- [x] Mejorar estados disabled en selects dependientes.
  - Se agregaron placeholders como `Seleccione una unidad primero`.

- [x] Agregar estilos de foco consistentes.
  - Aplicado en login, filtros, reporte de producción, perfil y botones principales modificados.

- [x] Validar fechas antes de consultar.
  - Se valida que `Fecha Desde` no sea posterior a `Fecha Hasta` en el panel de filtros.

## Tablas, gráficos y datos

- [x] Diferenciar visualmente `No hay datos` de `No se pudo cargar`.
  - Aplicado en combustible y dashboard.
  - Producción ya contaba con error visible en consulta/exportación.

- [x] Revisar textos abreviados en acciones de tabla.
  - En producción se cambió `Comb.` y `Prod.` por `Combustible` y `Producción`.

- [x] Agregar encabezados o resumen de filtros activos en reportes.
  - Ayuda a entender qué período/unidad se está viendo antes de exportar.
  - Se agregó resumen visible en el reporte de producción.

- [x] Confirmar que tablas anchas sean cómodas en mobile.
  - Mantener scroll horizontal, pero considerar columnas fijas o una vista resumida.
  - Se agregó ayuda visible en mobile para tablas con scroll horizontal.

- [x] Revisar paginación en mobile.
  - Botones `Anterior`, números y `Siguiente` pueden ocupar demasiado ancho.
  - Se ajustó la paginación del resumen para apilarse y envolver botones en pantallas chicas.

## Accesibilidad

- [x] Agregar nombres accesibles correctos a botones icon-only.
  - Aplicado a mostrar/ocultar contraseña y cerrar modal/detalle.

- [x] Marcar errores de formulario con `role="alert"` o estado equivalente.
  - Aplicado en login, filtros, producción, combustible y modal de email.

- [x] Agregar `aria-current` o clases visibles para ruta activa en el navbar.
  - Facilita orientación del usuario.
  - Se agregaron clases visibles para la ruta activa en el navbar.

- [x] Revisar contraste de textos secundarios.
  - Especialmente grises en fondos claros y verdes sobre verde.
  - Se subieron textos secundarios clave de `text-gray-500` a `text-gray-600/700` en filtros y KPIs.

## Consistencia visual

- [x] Unificar acentos y ortografía del producto.
  - Se corrigió a UTF-8 con acentos visibles correctamente.

- [x] Unificar estilo de cards, sombras y bordes.
  - Login, filtros, KPIs y tablas usan variantes parecidas pero no siempre consistentes.
  - Se agregaron clases compartidas `fg-card`, `fg-panel-accent` y variantes de acento para normalizar bordes, radios y sombras.

- [x] Revisar tamaños de botones y densidad.
  - Reportes operativos pueden beneficiarse de controles compactos, pero con buen área clicable.
  - Se agregaron clases compartidas `fg-btn`, `fg-btn-sm` y variantes por intención para mantener altura, foco y espaciado consistentes.

## Verificación sugerida

- [x] Ejecutar `npm run build`.
- [x] Probar login en desktop.
- [x] Probar login en mobile.
- [x] Probar navegación interna con una sesión válida.
- [x] Probar estados: carga, sin datos, error de backend y sesión vencida.
  - [x] Sin datos: verificado en local con API mock vacía; el resumen muestra un aviso claro.
  - [x] Sesión vencida: verificado en local con `/api/user/` devolviendo `401`; redirige a login con `next=/resumen`.
  - [x] Error de backend: verificado en local con `/api/produccion/data/` devolviendo `500`; el resumen muestra alerta y los gráficos dejan de mostrar carga.
  - [x] Carga: verificado en local con backend lento; muestra `Cargando datos del resumen...` y luego reemplaza el estado por los datos.
- [x] Probar exportación a Excel y modal de email.
  - Verificado en producción con sesión válida: endpoints de Excel de producción, reporte de producción y combustible responden `200` con archivo `.xlsx`.
  - Verificado en Browser: el modal de email abre correctamente y valida email inválido sin enviar el informe.

## Smoke final en producción

- [x] Sesión persistente y navegación principal.
  - Verificado en Browser: `/resumen`, `/`, `/combustible` y `/profile` cargan con sesión válida y sin redirección inesperada al login.
- [x] Exportación Excel.
  - Verificado por endpoint autenticado: producción y combustible responden `200` con archivo `.xlsx`.
- [x] Modal de email.
  - Verificado en Browser con email inválido: muestra `El formato del correo electrónico no es válido` y no se envía informe.
- [x] Pulido visual desplegado.
  - Verificado en producción: Resumen, Producción y Perfil muestran cards, inputs y botones consistentes.
- [x] Mobile smoke final.
  - Verificado manualmente por el usuario: la experiencia mobile funciona correctamente.


