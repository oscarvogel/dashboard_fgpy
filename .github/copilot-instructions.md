# FGPY project quick context

## Architecture overview
- Two main apps: Django backend in backend/ and Vue 3 frontend in frontend/.
- Backend routes are mounted at /api in [backend/backend/urls.py](backend/backend/urls.py). Endpoints live in function-based views in [backend/api/views.py](backend/api/views.py) and are wired in [backend/api/urls.py](backend/api/urls.py).
- Data model classes in [backend/api/models.py](backend/api/models.py) map to existing database tables with `managed = False` (no Django migrations). Many views filter by query params (e.g., `fecha_desde`, `fecha_hasta`, `unidad_negocio_id`, `tipo_operacion_id`, `equipo_id`, `empleado_id`).
- The backend uses session auth with `api_login`/`api_logout` and `login_required` decorators; several endpoints are `@csrf_exempt` for API use.

## Key flows & integrations
- Production KPIs and detail endpoints compute hours as `hr_fin - hr_inicio` and aggregate with `Sum`/`ExpressionWrapper` (see `api_produccion_*` in [backend/api/views.py](backend/api/views.py)).
- Fuel data endpoints aggregate `MovimientoCombustible.egreso` and can filter by related production via `idtabla` (see `api_combustible_*` in [backend/api/views.py](backend/api/views.py)).
- Excel exports use openpyxl (production + fuel exports in [backend/api/views.py](backend/api/views.py)).
- Email reports: HTML report generation in `generar_informe_html` and async sending via thread (`enviar_informe_email_thread`) in [backend/api/views.py](backend/api/views.py). SMTP settings are environment-driven in [backend/backend/settings.py](backend/backend/settings.py).

## Developer workflows
- Backend dev server is started by the PowerShell script [activa_backend.ps1](activa_backend.ps1), which activates a venv and runs `python manage.py runserver 0.0.0.0:8000` from backend/.
- Frontend (Vite + Vue 3 + Tailwind): commands and proxy behavior are documented in [frontend/README.md](frontend/README.md). Vite proxies `/api/*` to `BACKEND_URL` (default http://localhost:8000); production uses `VITE_API_BASE`.

## Configuration & conventions
- Backend config loads `.env` in backend/ and supports DB selection via `DB_ENGINE` + `DB_*` variables (see [backend/backend/settings.py](backend/backend/settings.py)). Default DB is SQLite at backend/db.sqlite3.
- If using MySQL and `pymysql` is installed, settings auto-install it as MySQLdb.
- Avoid creating new migrations for the existing tables unless explicitly converting a model away from `managed = False`.
- Keep API responses JSON-only (see patterns in [backend/api/views.py](backend/api/views.py)); lists are returned as `{ "data": [...] }` or `{ "detalle": [...] }` with pagination metadata when applicable.