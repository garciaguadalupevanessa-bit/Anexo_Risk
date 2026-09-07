# Seguridad del Repositorio

## Autenticación de cuenta GitHub

- **2FA activado** en la cuenta de GitHub que posee el repositorio.
- No almacenar credenciales de GitHub en archivos del proyecto.

## Protección del repositorio

- Repositorio **privado** durante desarrollo.
- `main` protegida: no force push, no borrado accidental.
- Pull request obligatorio para cambios en `main` (cuando sea posible).
- Status checks antes de merge (CI debe pasar).

## Secretos

### Reglas
- **Nunca** commitar `.env`, API keys, tokens, passwords, JWT secrets.
- **Nunca** poner secretos en README, screenshots, logs, o documentación pública.
- **Nunca** introducir secretos en el historial Git.

### Variables requeridas
| Variable | Propósito | Generación |
|----------|-----------|------------|
| `JWT_SECRET_KEY` | Firmado de tokens JWT | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ANEXO_ADMIN_KEY` | Autenticación de admin | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `NASA_FIRMS_API_KEY` | API NASA FIRMS | https://firms.modaps.eosdis.nasa.gov/api/area/ |
| `AEMET_API_KEY` | API AEMET | https://opendata.aemet.es/ |

### Configuración del backend
- `JWT_SECRET_KEY` y `ANEXO_ADMIN_KEY` son **requeridas**.
- Si faltan, el servidor falla al iniciar con un mensaje claro.
- No existen valores por defecto inseguros.

## Auditoría de secretos

### Herramientas
- `git grep` para buscar patrones en archivos trackeados.
- GitHub secret scanning (si está disponible).
- Revisión manual de `.env.example` y config files.

### Resultado de auditoría (2026-09-07)
- **No se encontraron secretos** en archivos trackeados ni en el historial Git.
- Todas las API keys usan `os.getenv()` sin valores hardcoded.
- `.env` correctamente gitignored, nunca commitado.

## Datos personales

- No almacenar datos personales de ciudadanos en el repositorio.
- No almacenar documentos de identidad.
- No almacenar información privada de voluntarios.
- Los datos de ejemplo en `db/seed.py` son fixtures anonimizados.

## CI/CD

- `pytest` y `ruff` se ejecutan en cada push/PR.
- Security checks opcionales: `bandit`, `gitleaks`.
- No introducir herramientas que añadan complejidad sin beneficio real.

## Contacto

Para reportar vulnerabilidades de seguridad, contactar directamente al maintainer.
