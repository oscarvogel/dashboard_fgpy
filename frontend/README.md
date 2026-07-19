# Frontend (Vue 3 + Vite + TailwindCSS)

Instrucciones rápidas para desarrollar y construir el frontend.

Requisitos:
- Node.js y npm instalados en el sistema.

Comandos (PowerShell):

```powershell
Set-Location -Path 'O:\django\fgpy\frontend'
npm install       # instalar dependencias (si aún no se hizo)
npm run dev       # iniciar servidor de desarrollo (Vite) — típico: http://localhost:5173
npm run build     # crear build para producción
npm run preview   # servir build localmente
```

Notas:
- El proyecto usa Vite + Vue 3 y TailwindCSS (PostCSS). Los estilos globales están en `src/assets/index.css`.
- Si ves problemas con versiones de paquetes, ejecuta `npm audit` y `npm audit fix` o revisa `package.json`.

Backend address (dev vs production):

- Development: Vite proxeará llamadas a `/api/*` al backend. El proxy por defecto apunta a `http://localhost:8000`. Si tu backend corre en otra dirección (por ejemplo porque lo arrancas con `0.0.0.0:8000`), puedes exportar `BACKEND_URL` antes de iniciar Vite:

```powershell
Set-Location -Path 'O:\django\fgpy\frontend'
$env:BACKEND_URL = 'http://localhost:8000'
npm run dev
```

- Production: configura la variable Vite `VITE_API_BASE` para que apunte al host real del backend (por ejemplo `https://api.example.com/api`). Puedes definirla en un archivo `.env.production` o pasarla en tiempo de build.

Ejemplo `.env.production` (archivo en `frontend/`):

```
VITE_API_BASE=https://api.example.com/api
```

El frontend usa `VITE_API_BASE` para construir las URLs de API. Si `VITE_API_BASE` está vacío, usa `/api` por defecto (habitual con proxy en dev).
