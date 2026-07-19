# Dashboard FGPY

Código fuente recuperado del sistema publicado en
`https://dashboard.forestalparaguay.com`.

## Arquitectura

- `backend/`: Django, API y comandos de informes.
- `frontend/`: Vue 3 + Vite, con fuente en `src/`.
- `deploy/`: procedimiento operativo seguro, sin despliegue automático.
- `docs/`: inventario de recuperación y documentación funcional.
- `scripts/`: ejecución local e inventario remoto de solo lectura.

El frontend consume rutas `/api`; Vite las redirige al backend durante el
desarrollo. En producción nginx sirve el build compilado y deriva la API a
Django. La ruta histórica es `/var/www/html/django/fgpy` y el servicio es
`dashboard_fgpy.service`.

## Instalación local

Copiar `.env.example` a `backend/.env` y reemplazar solo los valores locales.
El archivo real nunca se versiona.

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
Copy-Item .env.example backend\.env
Push-Location backend
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py runserver
Pop-Location
```

En otra terminal:

```powershell
Push-Location frontend
pnpm install --frozen-lockfile
pnpm dev
Pop-Location
```

## Variables

`.env.example` enumera Django, base de datos, correo y proxy frontend con
valores ficticios. SQLite es el valor local. Producción usa su configuración
privada fuera de Git.

## Tests y build

```powershell
Push-Location backend
.\.venv\Scripts\python manage.py test --settings=backend.test_settings
Pop-Location

Push-Location frontend
pnpm test
pnpm build
Pop-Location
```

`frontend/dist` es un artefacto generado: puede compararse por hashes con lo
publicado, pero no sustituye a `frontend/src` ni se versiona.

## Código, build y datos

El código fuente permite mantener y reconstruir el sistema. El build contiene
JavaScript/CSS compilado para nginx. Las bases, `.env`, logs y multimedia son
datos/configuración privados y no pertenecen al repositorio.

## Producción, despliegue y rollback

No se modificó producción durante esta recuperación. El procedimiento con
staging, respaldo, cambio atómico, una única recarga y rollback está en
`deploy/README.md`. Antes de usarlo hay que restaurar/verificar el acceso
`fasa_195`, inventariar el servidor y comparar la versión candidata.

Véase `docs/recovery-inventory.md` para procedencia, exclusiones y pendientes.
