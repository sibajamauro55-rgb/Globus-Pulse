# Validación del flujo (2026-09-07)

Ejecutado con `python3 scripts/validate_flow.py`.

Destinos del run: `webhook` (HTTP real a un servidor local), `web` y `linkedin` sin credenciales.

| # | Criterio | Resultado |
|---|---|---|
| 1 | Se configura GLOBUS / campaña `always-on-globus` | PASS |
| 2 | Se genera una campaña | PASS |
| 3 | Se genera contenido | PASS |
| 4 | Se genera al menos una pieza visual real (PNG 1920×1080) | PASS |
| 5 | Se crea el job de publicación | PASS |
| 6 | Publisher real cuando hay destino (webhook 201 + `external_id`) | PASS |
| — | LinkedIn queda `blocked` sin credenciales (no fingido) | PASS |
| — | Web queda `blocked` sin endpoint; payload staged | PASS |
| — | CTA apunta a `/crear-propuesta` | PASS |
| 7 | Jobs idempotentes (republicar no duplica el POST) | PASS |
| 8 | Estados: jobs `published`/`blocked`, pieza `published` | PASS |
| 9 | Un publisher que explota no tumba el ciclo | PASS |
| 10 | El sistema vuelve a ejecutar el ciclo | PASS |

**13/13 pass.**
