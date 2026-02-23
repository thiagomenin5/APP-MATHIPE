# FASE 2 – FLUJO COMPLETO Y TERCERIZACIÓN

Objetivo:
Completar el flujo operativo real de imprenta.

---

# 1. VISTO BUENO FORMAL

Estados:

- New
- Design
- WaitingApproval
- Approved

Debe permitir:
- Pedir aprobación
- Registrar OK
- Historial

---

# 2. PRODUCCIÓN REAL

Estados:

- Approved
- Outsourcing
- Production
- Done

Tablero basado en Work Order.

---

# 3. TERCERIZACIÓN POR ÍTEM

Campos por ítem:

- is_outsourced
- supplier
- outsource_status

Estados:

- PendingVendor
- Sent
- Received
- Done

No puede avanzar a producción interna hasta "Received".

---

# 4. HISTORIAL DE CAMBIOS

Cada cambio de estado debe registrar:

- usuario
- fecha
- comentario opcional

---

# 5. RETROCESO DE ESTADO RESTRINGIDO POR ROL

- **Retrocesos** (volver un paso atrás en el flujo) y **Cancelar** (estado Cancelled) solo están permitidos para usuarios con rol **System Manager** o **Gerencia**.
- Usuarios sin esos roles no pueden retroceder ni cancelar; si lo intentan, el backend responde: *"No tienes permisos para retroceder estados. Solicita a Gerencia."*
- La UI solo muestra en el dropdown los estados válidos para el usuario actual; por tanto, los usuarios normales no ven la opción de retroceso ni Cancelled.
- Todo retroceso o cancelación ejecutado por un usuario con rol override se registra en **Mathipe WO Status Log** con un comentario automático con prefijo `OVERRIDE:` (ej.: *"OVERRIDE: retroceso autorizado por rol (user=...)"*). Si el usuario envía comentario, se prefija `OVERRIDE:` a ese texto.

## Comportamiento de Cancelled

- El estado **Cancelled** solo puede ser elegido por usuarios con rol **System Manager** o **Gerencia**.
- Se considera una acción de override (igual que el retroceso) y se registra en el log con comentario `OVERRIDE:`.
