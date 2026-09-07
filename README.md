# Globus-Pulse

Máquina interna de marketing y publicación de **Globus**.

No es un módulo de Globus-Core. No es SaaS para clientes. No toca Globus-Core-Web.

Propósito único:

1. Conocer la marca Globus
2. Generar contenido comercial nuevo
3. Renderizar la pieza visual con plantillas consistentes
4. Validar
5. Calendarizar
6. Publicar en los adaptadores configurados
7. Registrar el resultado
8. Repetir

CTA canónico: `https://globus.app/crear-propuesta`

## Qué está implementado

- Perfil de marca en `config/brand.yaml` (Ink / Paper / Meridian, GIS 1.0 como referencia)
- Banco de ángulos distintos (educación, problema, capacidad, caso, comercial, CTA)
- Plantillas visuales reutilizables (Pillow)
- Scripts de video corto (beats/escenas, sin FFmpeg en v1)
- Calendario interno y cola de jobs
- Estados: `draft → generated → approved → scheduled → publishing → published | failed | blocked`
- Jobs idempotentes (`piece_id + platform` único, CAS a `publishing`)
- Adaptadores:
  - `webhook` — publicación HTTP real
  - `web` — adaptador del sitio (HTTP si hay endpoint; si no, stage en `outbound/web/` y job `blocked`)
  - `x` — API real con OAuth 1.0a cuando hay credenciales
  - `linkedin` — Posts API real cuando hay token + URN
  - `instagram` / `facebook` — Graph API, bloqueados hasta tener credenciales
- Worker APScheduler + CLI + API mínima de operación
- Docker

## Qué no es

- No modifica Globus-Core, Core-Web, Content Module, Marketing, Automations, Ecosystem ni Guard.
- No reutiliza el Content Engine de Core como dependencia.
- No simula `published` cuando faltan credenciales: el job queda `blocked` con motivo.

## Cómo se ejecuta

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# completar credenciales de las redes que sí se van a publicar

PYTHONPATH=src python -m pulse init
PYTHONPATH=src python -m pulse run
PYTHONPATH=src python -m pulse status
PYTHONPATH=src python -m pulse worker    # ciclo continuo cada 6 horas
PYTHONPATH=src python -m pulse serve     # API en :8088
```

Docker:

```bash
docker compose up --build
```

Validación del flujo:

```bash
PYTHONPATH=src python scripts/validate_flow.py
```

## Credenciales

| Plataforma | Variables | Estado sin credenciales |
|---|---|---|
| Webhook | `WEBHOOK_URL`, `WEBHOOK_TOKEN` | `blocked` |
| X | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | `blocked` |
| LinkedIn | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN` | `blocked` |
| Instagram | `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ID` + `public_asset_url` | `blocked` |
| Facebook | `META_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID` | `blocked` |
| Sitio Globus | `WEB_PUBLISH_ENDPOINT`, `WEB_PUBLISH_TOKEN` | `blocked` + JSON en `outbound/web/` |

`ENABLED_PLATFORMS` controla qué adaptadores entran a la cola.

## Crecimiento previsto (no implementado de golpe)

Carruseles, flyers extra, videos renderizados, más campañas, reutilización inteligente. La frontera está en `Publisher`, `Frame`, `Angle` y `templates/`.
