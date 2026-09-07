from __future__ import annotations

"""Banco de ángulos. Cada entrada es un mensaje distinto, no un parafraseo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Angle:
    id: str
    category: str
    template: str
    objective: str
    headline: str
    support: str
    body: str
    format_hint: str = "post"


ANGLES: tuple[Angle, ...] = (
    Angle(
        "edu-os",
        "educate",
        "educate",
        "educar",
        "Una empresa no se opera con 14 herramientas sueltas",
        "Globus concentra CRM, inventario, tickets y WhatsApp en un sistema.",
        "Las PyME no fallan por falta de apps. Fallan porque cada área vive en un archivo distinto. Globus es el sistema operativo: un tenant, módulos enchufables, una sola operación.",
    ),
    Angle(
        "edu-modules",
        "educate",
        "educate",
        "educar",
        "El core no conoce tu vertical. El módulo sí.",
        "Arquitectura modular: CRM, inventario, ventas, tickets.",
        "Globus no es un ERP rígido. El core sostiene tenants, permisos y eventos. Tú activas los módulos que el negocio necesita. Empieza chico. Crece sin rehacer el sistema.",
    ),
    Angle(
        "edu-whatsapp",
        "educate",
        "tip",
        "educar",
        "WhatsApp no es un CRM. Tratarlo como tal te cuesta ventas.",
        "El hilo se pierde. El follow-up también.",
        "Si la conversación comercial vive solo en el celular de alguien, no hay pipeline. Globus conecta WhatsApp con la operación: contacto, trato, ticket, siguiente paso.",
    ),
    Angle(
        "edu-auto",
        "educate",
        "tip",
        "educar",
        "Automatizar no es pegarle un Zap a cada hueco",
        "Eventos de dominio. Reglas. Un solo sistema.",
        "La automatización útil nace de lo que ya ocurrió en el negocio: trato ganado, stock bajo, ticket cerrado. Globus emite esos eventos. El resto deja de ser parche.",
    ),
    Angle(
        "edu-ia",
        "educate",
        "educate",
        "educar",
        "IA aplicada es útil cuando conoce tu operación",
        "No un chat suelto. Un módulo sobre tus datos.",
        "Un asistente que no ve CRM ni tickets inventa. En Globus la IA entra como módulo del sistema, no como pestaña decorativa.",
    ),
    Angle(
        "prob-excel",
        "problem",
        "problem_solution",
        "mostrar problema",
        "Si tu operación cabe en una hoja, todavía no tienes operación",
        "Excel aguanta hasta que un cliente, un SKU o un vendedor se cae.",
        "La hoja de cálculo no tiene tenant, no tiene permisos, no tiene historial comercial. El día que dos personas editan la misma fila, ya perdiste. Globus corta eso de raíz.",
    ),
    Angle(
        "prob-followup",
        "problem",
        "problem_solution",
        "mostrar problema",
        "El follow-up que vive en la cabeza del vendedor no existe",
        "Sin pipeline no hay pronóstico. Sin pronóstico no hay empresa.",
        "Cotizaciones en WhatsApp, acuerdos en el aire, el cierre 'la próxima semana'. Globus pone el trato en un pipeline y la siguiente acción en el sistema.",
    ),
    Angle(
        "prob-stock",
        "problem",
        "compare",
        "mostrar problema",
        "Vender lo que no tienes es tan caro como no vender",
        "Inventario desconectado de ventas es pérdida silenciosa.",
        "Si el comercial promete y el almacén no se enteró, pagas en devoluciones y reputación. Globus une ventas e inventario en la misma operación.",
    ),
    Angle(
        "prob-tickets",
        "problem",
        "problem_solution",
        "mostrar problema",
        "El cliente no espera a que alguien recuerde su caso",
        "Soporte sin ticket es amnesia institucional.",
        "Un mensaje, tres reenvíos, nadie dueño. Globus convierte eso en ticket con estado, responsable y historial.",
    ),
    Angle(
        "cap-crm",
        "capability",
        "service_ad",
        "demostrar capacidad",
        "CRM que sí alimenta ventas, no un directorio bonito",
        "Contactos, tratos, actividades. Multi-tenant desde el día uno.",
        "Globus CRM no es una libreta. Es el frente comercial del sistema operativo: pipeline, seguimiento y base para automatizar.",
    ),
    Angle(
        "cap-inventory",
        "capability",
        "service_ad",
        "demostrar capacidad",
        "Inventario con la misma disciplina que tus ventas",
        "Productos, movimientos, compras. Un solo tenant.",
        "Cuando el stock vive en Globus, ventas deja de prometer a ciegas y compras deja de adivinar.",
    ),
    Angle(
        "cap-tenant",
        "capability",
        "institutional",
        "demostrar capacidad",
        "Multi-tenant de verdad. No un filtro improvisado.",
        "Cada empresa aislada. Cada módulo con permisos.",
        "Globus nació para operar varias organizaciones sin mezclar datos. Eso no se pega después. Se diseña desde el core.",
    ),
    Angle(
        "use-sales",
        "use_case",
        "use_case",
        "caso de uso",
        "Del primer mensaje a la propuesta, sin perder el hilo",
        "WhatsApp + CRM + propuesta comercial.",
        "Llega el prospecto. Se crea el contacto. Se abre el trato. Se genera la propuesta. El comercial no reconstruye la historia cada lunes.",
    ),
    Angle(
        "use-ops",
        "use_case",
        "use_case",
        "caso de uso",
        "Operación de campo que no depende de un grupo de WhatsApp",
        "Tickets y field service con dueño y estado.",
        "Una orden en la calle necesita responsable, evidencia y cierre. Globus lo registra. El grupo familiar deja de ser el sistema.",
    ),
    Angle(
        "use-onboard",
        "use_case",
        "benefit",
        "caso de uso",
        "Onboarding que termina en propuesta, no en un tour vacío",
        "El destino comercial es /crear-propuesta.",
        "Globus no te enseña pantallas para lucirse. Te lleva a armar la operación y pedir la propuesta. Eso es el producto.",
    ),
    Angle(
        "com-os",
        "commercial",
        "service_ad",
        "vender",
        "Deja de apilar software. Pon un sistema.",
        "Globus: el sistema operativo de tu empresa.",
        "CRM, inventario, tickets, WhatsApp e IA en un producto. Configúralo una vez. Opera todos los días. El siguiente paso es crear tu propuesta.",
    ),
    Angle(
        "com-start",
        "commercial",
        "promo",
        "vender",
        "Empieza con lo que hoy te duele. Agrega el resto después.",
        "Módulos enchufables. Sin rehacer la base.",
        "No tienes que comprar el universo el día uno. Activas CRM o inventario o tickets. El core ya está listo para crecer.",
    ),
    Angle(
        "com-cost",
        "commercial",
        "benefit",
        "vender",
        "El costo real no es la suscripción. Es el desorden.",
        "Horas, errores, ventas que no se cierran.",
        "Cada herramienta suelta cobra en contexto perdido. Globus reduce esa fricción y te deja un destino claro: crear propuesta y operar.",
    ),
    Angle(
        "cta-proposal",
        "cta",
        "cta",
        "convertir",
        "Crea tu propuesta. Hoy.",
        "El flujo comercial de Globus empieza en /crear-propuesta.",
        "Si tu empresa ya no cabe en Excel y WhatsApp, no necesitas otro tutorial. Necesitas un sistema. Entra, arma la propuesta y empieza.",
    ),
    Angle(
        "cta-operate",
        "cta",
        "cta",
        "convertir",
        "Pasa de chat improvisado a operación",
        "Un tenant. Módulos. Un destino comercial.",
        "Globus existe para que vendas y operes en el mismo lugar. El CTA no es 'síguenos'. Es crear tu propuesta.",
    ),
)


CATEGORY_TO_ANGLES = {}
for _a in ANGLES:
    CATEGORY_TO_ANGLES.setdefault(_a.category, []).append(_a)
