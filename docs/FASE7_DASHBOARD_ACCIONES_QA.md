# Checklist QA — Fase 7 Acciones rápidas desde Dashboard

Validación manual de las acciones rápidas en las listas del Control Center.

## 1. Botón "Actualizar"

- [ ] En el header del dashboard hay un botón **"Actualizar"** que recarga todo el dashboard (KPIs y listas) sin recargar la página.
- [ ] Al hacer clic se muestra indicador de carga y luego los datos se actualizan.

## 2. Esperando aprobación

- [ ] Cada fila tiene botón **Aprobar** y **Rechazar** y dropdown **Asignar a**.
- [ ] Al hacer clic en **Aprobar** se abre un modal de confirmación ("¿Aprobar la OT …?"). Al confirmar, la acción se ejecuta y la fila desaparece de la lista (o se actualiza el estado). Toast verde "OT aprobada.".
- [ ] Al hacer clic en **Rechazar** se abre modal ("¿Devolver la OT … a Diseño?"). Al confirmar, la fila desaparece o se actualiza. Toast "Devolvida a Diseño.".
- [ ] Al elegir un usuario en **Asignar a**, se asigna sin modal. Toast "Asignación actualizada.". Solo se actualiza esa fila (no se recarga todo el dashboard).
- [ ] Si hay error de backend, se muestra toast rojo con el mensaje.

## 3. Tercerización vencida

- [ ] Cada fila tiene **Marcar recibido**, enlace **Ver orden** y **Asignar a**.
- [ ] **Marcar recibido**: al hacer clic se marca el ítem tercerizado en estado "Sent" como "Received". La fila puede desaparecer de la lista. Toast "Marcado como recibido.".
- [ ] **Ver orden**: lleva a `/orden/:id` sin ejecutar acción (enlace).
- [ ] **Asignar a**: mismo comportamiento que en otras secciones.

## 4. Urgentes

- [ ] Si el estado es **Approved**, se muestra botón **Iniciar** (producción). Modal de confirmación; al confirmar, el estado pasa a Production y la fila se actualiza. Toast "Producción iniciada.".
- [ ] Si el estado es **Production**, se muestra botón **Finalizar**. Modal; al confirmar, estado pasa a Done. Toast "OT finalizada.".
- [ ] **Asignar a** en cada fila con el mismo comportamiento que arriba.

## 5. Alertas críticas

- [ ] Cada fila tiene solo **Asignar a** (dropdown). Clic en la fila lleva a la orden.

## 6. UX general

- [ ] Al ejecutar una acción (Aprobar, Asignar, etc.) solo se actualiza la fila afectada o se quita de la lista; no se recarga todo el dashboard.
- [ ] Mientras se ejecuta la acción se muestra un spinner pequeño en la fila (o en el botón).
- [ ] Si el backend devuelve error, se muestra toast rojo con el mensaje y no se cambia la fila.
- [ ] Clic en la fila (OT/cliente, fecha, estado, margen) sigue llevando a `/orden/:id`. Los botones y el dropdown no disparan navegación (stop propagation).

## 7. Tests automatizados

- [ ] Ejecutar:  
  `bench --site [site] execute mathipe_ui.scripts.test_dashboard_actions.run_tests`  
  y comprobar que todos pasan (estado Production, outsource Received, asignación persistida; respuestas con work_order_id, new_status, alerts_summary).

---

**Comando de tests**

```bash
bench --site [site] execute mathipe_ui.scripts.test_dashboard_actions.run_tests
```
