# Inventario de recuperación

Fecha del diagnóstico: 2026-07-19.

## Orígenes

- `O:\django\fgpy`: fuente elegida para backend, frontend, tests y documentos.
- `O:\FGPY\web`: copia incompleta con dependencias/artefactos frontend; no usada.
- GitHub `oscarvogel/dashboard_fgpy`: repositorio vacío al iniciar.
- Producción `/var/www/html/django/fgpy`: no inventariada por SSH porque el alias
  `fasa_195` no está configurado en esta estación.
- Sitio público: respondió HTTP 200 y permitió verificar el build publicado.

## Recuperado

- backend Django, configuración, API, comandos, modelos no gestionados y tests;
- frontend Vue/Vite completo (`src`, configuración, lockfile y test);
- documentación funcional y de seguridad;
- ejemplos de entorno reescritos con valores ficticios;
- inventario remoto de solo lectura y procedimiento de despliegue/rollback.

## Excluido

- `.env`, credenciales y configuración efectiva;
- `db.sqlite3`, dumps, medios, logs y datos productivos;
- `node_modules`, `dist`, cachés y temporales;
- ZIP y directorios históricos de `deploy/`;
- scripts históricos que modificaban producción o reiniciaban el servicio.

## Faltante o pendiente

- inventario y hashes del código remoto por falta del alias SSH;
- unidad systemd y configuración nginx efectivas;
- confirmación remota de migraciones (localmente solo existe `__init__.py`);
- comparación del backend local contra producción.

Los modelos de negocio locales usan `managed = False`, por lo que no crean las
tablas productivas mediante migraciones Django.

## Validación local

- Django 5.2.16: `manage.py check` sin observaciones.
- Backend: 9 de 9 tests aprobados con SQLite en memoria.
- Frontend: instalación congelada con `pnpm`, 9 de 9 tests aprobados.
- Vite 5.4.21: build aprobado con ocho archivos.
- Los ocho archivos generados coinciden exactamente en tamaño y SHA-256 con
  los ocho archivos publicados por el dominio.

Por limitaciones de enlaces simbólicos en la unidad de red `O:`, los entornos
de validación se instalaron en una carpeta temporal local de `C:` usando el
código y lockfile del repositorio. No se usó el `.env` recuperado.
