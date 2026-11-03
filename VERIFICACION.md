# Cómo verifico mi entrega

Primero configuro PostgreSQL y ejecuto las migraciones. Después inicio la API y abro Swagger en /docs.

1. Me registro e inicio sesión en /api/v1/auth/token.
2. Consulto mi perfil y compruebo que una ruta de administración rechaza mi rol user.
3. Con un editor creo un post publicado y con otro usuario agrego un comentario.
4. Abro /api/v1/ws/client con el token del autor y verifico la notificación.
5. Consulto /api/v1/notifications y marco la notificación como leída.
6. Subo un PNG o JPEG al post, lo descargo y pruebo un archivo de tipo incorrecto y uno de más de 5 MB.
7. Descargo /api/v1/posts/export y compruebo que incluye solo posts visibles para mi usuario.
8. Hago más de 30 peticiones por minuto desde la misma IP y compruebo el 429 con Retry-After.
9. Reviso var/outbox.log y var/analytics.log.
10. Detengo el servidor y compruebo que se cierre el pool.
