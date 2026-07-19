# Checklist de seguridad

Relevamiento inicial del sistema FGPY. Usar este documento como lista viva: marcar avances, agregar fecha/responsable si hace falta y volver a verificar cada punto despues de los cambios.

## Prioridad alta

- [x] Quitar `@csrf_exempt` de endpoints que usan cookies de sesion y modifican estado.
  - Archivos: `backend/api/views.py`
  - Casos detectados: login, logout, perfil, cambio de password, envio de informes.
  - Verificacion: desplegado en VPS el 2026-05-24. `GET /api/csrf/` responde y setea cookie `csrftoken`.

- [x] Implementar manejo CSRF en el frontend.
  - Archivos: `frontend/src/auth.js`, `frontend/src/views/Profile.vue`, `frontend/src/components/FilterSidebar.vue` y otros `fetch` con metodos no seguros.
  - Accion sugerida: obtener cookie CSRF desde Django y enviar `X-CSRFToken` en requests mutantes.
  - Verificacion: `npm run build` local OK. En navegador integrado, login invalido devuelve `Invalid credentials` sin errores de consola, confirmando que el flujo CSRF no bloquea el POST. Pendiente prueba con usuario real: login exitoso, logout, perfil, password y envio de informes.

- [ ] Endurecer configuracion productiva de Django.
  - Archivo: `backend/backend/settings.py`
  - Accion sugerida: `DJANGO_DEBUG=False` por defecto o fallar si no esta definido en produccion.
  - Agregar/activar: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY` segun estrategia de frontend, `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`.
  - Verificacion: `manage.py check --deploy` sin warnings criticos.

- [ ] Rotar y proteger secretos.
  - Archivo detectado: `backend/.env`
  - Accion sugerida: confirmar que no este versionado, rotar `DJANGO_SECRET_KEY`, credenciales SMTP y credenciales de DB si alguna vez se compartieron.
  - Verificacion: `.env` queda fuera del repositorio y solo existen ejemplos sin secretos reales.

- [x] Agregar `.gitignore` del proyecto.
  - Incluir: `.env`, `db.sqlite3`, `__pycache__/`, `*.pyc`, `frontend/node_modules/`, `frontend/dist/`, logs y archivos temporales.
  - Verificacion: aplicado localmente y en VPS el 2026-05-24. Pendiente confirmar estado Git si el proyecto se versiona en otra ruta.

- [ ] Revisar exposicion del servidor de desarrollo.
  - Archivo: `activa_backend.ps1`
  - Riesgo: `runserver 0.0.0.0:8000` expone el backend en la red local.
  - Accion sugerida: usar `127.0.0.1:8000` para desarrollo local o documentar cuando sea necesario exponerlo.
  - Verificacion: el backend no queda accesible desde otros equipos salvo decision explicita.

## Prioridad media

- [ ] Aplicar validadores de password de Django en cambio de contrasena.
  - Archivo: `backend/api/views.py`
  - Riesgo: hoy se valida solo largo minimo de 6 caracteres.
  - Accion sugerida: usar `django.contrib.auth.password_validation.validate_password`.
  - Verificacion: passwords comunes/debiles se rechazan igual que en el admin de Django.

- [ ] Evitar devolver errores internos al cliente.
  - Archivo: `backend/api/views.py`
  - Casos detectados: respuestas con `error: str(e)`.
  - Accion sugerida: loguear detalle internamente y devolver mensajes genericos.
  - Verificacion: ante fallo, la API no expone paths, queries, credenciales ni mensajes internos.

- [ ] Reemplazar `print` y tracebacks por logging estructurado.
  - Archivo: `backend/api/views.py`
  - Accion sugerida: usar `logging.getLogger(__name__)` y niveles `info`, `warning`, `exception`.
  - Verificacion: logs utiles para operar, sin filtrar datos sensibles innecesarios.

- [ ] Limitar envio de emails e informes.
  - Archivo: `backend/api/views.py`
  - Riesgo: cualquier usuario autenticado puede disparar emails a destinos arbitrarios.
  - Accion sugerida: permisos por rol, allowlist de dominios/destinatarios o confirmacion administrativa segun negocio.
  - Verificacion: usuarios sin permiso no pueden enviar informes.

- [ ] Agregar rate limiting a login y endpoints costosos.
  - Casos: `/api/login/`, endpoints de export Excel, envio de informes.
  - Accion sugerida: `django-ratelimit`, middleware/proxy o control por usuario/IP.
  - Verificacion: intentos repetidos quedan bloqueados o ralentizados.

- [ ] Escapar datos al generar HTML manual.
  - Archivo: `backend/api/views.py`
  - Riesgo: informes HTML interpolan datos de DB como equipo, observaciones, remitos y combustible.
  - Accion sugerida: usar templates de Django con autoescape o `django.utils.html.escape`.
  - Verificacion: valores con `<script>` se muestran como texto, no se ejecutan en navegador/email.

- [ ] Revisar permisos de acceso a datos.
  - Archivo: `backend/api/views.py`
  - Riesgo: `@login_required` permite a cualquier usuario autenticado consultar todas las unidades/equipos/reportes.
  - Accion sugerida: definir autorizacion por rol, unidad de negocio o grupo.
  - Verificacion: un usuario solo ve datos autorizados.

- [ ] Eliminar endpoints duplicados o ambiguos.
  - Archivo: `backend/api/views.py`
  - Caso detectado: `api_enviar_informe_email` aparece definido dos veces.
  - Accion sugerida: conservar una sola implementacion y una sola ruta clara.
  - Verificacion: tests de URL confirman que se invoca la funcion esperada.

## Prioridad baja / higiene

- [ ] Normalizar codificacion de archivos.
  - Sintoma: textos con caracteres mojibake como `ProducciÃ³n`.
  - Accion sugerida: convertir archivos a UTF-8 y revisar mensajes visibles.
  - Verificacion: acentos y simbolos se ven correctamente.

- [ ] Revisar configuracion de Vite para desarrollo.
  - Archivo: `frontend/vite.config.js`
  - Riesgos: `host: true`, `fs.strict: false`, proxy `secure: false`.
  - Accion sugerida: dejar valores abiertos solo para desarrollo y documentar alternativas seguras.
  - Verificacion: produccion no depende de esa configuracion laxa.

- [ ] Ordenar dependencias y auditoria.
  - Backend: `backend/requirements.txt`
  - Frontend: `frontend/package.json`, `frontend/pnpm-lock.yaml`
  - Accion sugerida: instalar tooling disponible y correr `pip-audit`/`safety` y `pnpm audit`.
  - Verificacion: vulnerabilidades conocidas quedan documentadas o corregidas.

- [ ] Separar archivos generados del repositorio.
  - Detectados: `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `backend/db.sqlite3`.
  - Accion sugerida: ignorar artefactos y limpiar del control de versiones si corresponde.
  - Verificacion: el repo queda reproducible desde dependencias y build.

- [ ] Agregar pruebas de seguridad basicas.
  - Casos sugeridos: CSRF requerido, usuario no autenticado recibe 302/401, password debil rechazado, usuario sin permiso no puede enviar informe.
  - Avance: agregados tests Django para CSRF en login/perfil y tests frontend para helpers `getCookie`, `ensureCsrfToken` y `csrfFetch`.
  - Verificacion: `npm test` OK, `npm run build` OK. Backend OK local con `O:\envs\fgpy` y `DJANGO_SETTINGS_MODULE=backend.test_settings`.

## Verificaciones pendientes del relevamiento

- [ ] Ejecutar `python manage.py check --deploy`.
  - Nota: no se pudo ejecutar en esta maquina porque el Python/venv configurado no estaba disponible.

- [ ] Ejecutar auditoria de dependencias frontend.
  - Nota: `npm audit` no aplica porque no hay `package-lock.json`; el proyecto usa `pnpm-lock.yaml`, pero `pnpm` no estaba instalado.

- [ ] Confirmar si existe repositorio Git en otra carpeta.
  - Nota: `O:\django\fgpy` no aparece como repositorio Git en esta sesion.

## Propuesta de orden de trabajo

1. Proteger secretos y `.gitignore`.
2. Corregir CSRF backend/frontend.
3. Endurecer settings productivos y correr `check --deploy`.
4. Mejorar password validation, errores y logging.
5. Revisar permisos por rol/unidad y limites de envio/exportacion.
6. Limpiar artefactos, dependencias y pruebas automatizadas.
