# Despliegue seguro

Esta recuperación no se desplegó. Producción vive históricamente en
`/var/www/html/django/fgpy`, el servicio es `dashboard_fgpy.service` y el
dominio es `dashboard.forestalparaguay.com`.

Antes de un despliegue futuro:

1. confirmar acceso, inventario y salud sin escribir;
2. construir y probar backend y frontend en staging;
3. crear un respaldo fechado fuera del árbol publicado, excluyendo `.env`,
   bases y datos privados del paquete de código;
4. copiar a un directorio staging y verificar hashes;
5. conservar `.env` y datos en el servidor, nunca en Git;
6. ejecutar `manage.py check --deploy` con el entorno de producción;
7. cambiar la versión mediante un enlace o movimiento atómico;
8. reiniciar una sola vez `dashboard_fgpy.service`;
9. verificar servicio, API, HTML y assets;
10. volver atómicamente a la versión anterior y reiniciar una vez si falla.

No se incluye un script que ejecute automáticamente estos pasos: requiere
confirmación humana, acceso restaurado al alias SSH y conocimiento del layout
actual verificado en el servidor.
