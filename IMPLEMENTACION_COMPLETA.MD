Responde siempre en español.
No uses Frappe Desk: todo por APIs whitelisted en mathipe_ui/api.py.
Work Order es la fuente de verdad operativa; Sales Order es documento comercial.
No romper funcionalidades existentes.
Evitar refactors masivos: cambios pequeños y verificables.
Mantener UI coherente con Tailwind actual.


# ERP MATHIPE – MASTER PLAN
Versión 1.0
Proyecto interno Gráfica Mathipe

---

# 1. VISIÓN GENERAL

ERP Mathipe es un sistema integral para imprentas basado en el modelo operativo de Twist Print.

Su objetivo es digitalizar completamente:

- Cotizaciones manuales
- Seguimiento verbal
- Producción en papel
- Control de terceros
- Aprobaciones informales
- Gestión dispersa de clientes

El sistema debe convertirse en la herramienta diaria central de la empresa.

---

# 2. FILOSOFÍA DEL SISTEMA

El ERP no gira en torno a la Sales Order.
Gira en torno a la WORK ORDER.

Sales Order = documento comercial.
Work Order = documento operativo central.

El flujo es:

Cotización → Work Order → Diseño → Aprobación → Producción → Entrega → Cobro → Análisis

---

# 3. ARQUITECTURA GENERAL

Frontend:
Vue 3 + Tailwind + SPA

Backend:
Frappe + APIs whitelisted

DocTypes custom:

- Mathipe Quote
- Mathipe Quote Item
- Mathipe Product Recipe
- Mathipe Recipe Component
- Mathipe Work Order
- Mathipe Attachment

---

# 4. FASES DE IMPLEMENTACIÓN

FASE 1 – Núcleo Operativo  
FASE 2 – Flujo Completo y Tercerización  
FASE 3 – Cliente 360 y Análisis  
FASE 4 – Optimización y Escalabilidad  

Cada fase tiene su documento específico.

---

# 5. OBJETIVO FINAL

ERP robusto, modular y escalable que:

- Sea superior a Twist Print
- No dependa de Frappe Desk
- Sea completamente operable desde la SPA
- Permita crecimiento futuro (multi-sucursal, automatizaciones, BI)
