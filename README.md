# Pulse API — Mi entrega de la semana 10

Amplié mi API de la semana 9 con WebSockets, notificaciones persistentes, tareas en segundo plano, imágenes y exportación CSV. Conservo PostgreSQL, SQLAlchemy asíncrono, Alembic, JWT, refresh tokens, roles, validaciones y reglas de propiedad.

## Cómo la ejecuto

Uso Python 3.12 o superior y PostgreSQL. Creo la base con el esquema de la semana 7 y configuro DATABASE_URL y JWT_SECRET en .env a partir de .env.example.

```powershell
uv sync
Copy-Item .env.example .env
uv run alembic stamp 001_baseline
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Si parto de la base de la semana 9, ejecuto solamente upgrade head: conservo su revisión actual.

Abro /docs para probar las rutas. Ahora todos los recursos están bajo /api/v1 y el login de Swagger apunta a /api/v1/auth/token.

## Qué incorporé

Organizo los routers mediante un router padre. Valido el JWT y el usuario antes de aceptar el WebSocket en /api/v1/ws/notifications. Al comentar guardo una notificación para el autor, la envío a sus conexiones abiertas y registro un email simulado. Al registrarme guardo un evento de analytics.

Subo imágenes JPEG o PNG de hasta 5 MB, verifico MIME y firma, y guardo cada archivo con UUID. Sirvo la imagen mediante FileResponse y exporto los posts visibles como CSV con StreamingResponse.

En el lifespan creo var/uploads, verifico la base y cierro el pool al finalizar. Limito las peticiones a 30 por minuto por IP y el login a 5. Agrego trazabilidad y convierto los errores inesperados en una respuesta JSON sin detalles internos.

## Rutas nuevas

| Método | Ruta |
|---|---|
| GET | /api/v1/notifications |
| PUT | /api/v1/notifications/{id}/read |
| POST y GET | /api/v1/posts/{id}/image |
| GET | /api/v1/posts/export |
| WS | /api/v1/ws/notifications |
| GET | /api/v1/ws/client |

Sigo el recorrido de VERIFICACION.md para comprobar la integración. Uso un solo worker: las conexiones WebSocket y el rate limiter viven en memoria. Los avisos persisten en PostgreSQL; el email es una simulación local. Las tareas en segundo plano no son una cola durable.
