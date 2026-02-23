# Fase 8 – Quick View lateral: checklist manual de prueba

## Objetivo
Verificar que el panel lateral (drawer) de resumen rápido de OT funciona correctamente desde el Dashboard Operativo, sin romper la navegación a la vista completa de orden.

---

## 1. Apertura del Quick View

- [ ] **1.1** En Dashboard Operativo, hacer clic en una **fila** de la tabla "Urgente (entrega hoy)" → se abre el drawer por la derecha con el detalle de esa OT.
- [ ] **1.2** Hacer clic en una fila de "Alertas críticas" → se abre el Quick View con la OT correcta.
- [ ] **1.3** Hacer clic en una fila de "Pendientes de aprobación" → se abre el Quick View.
- [ ] **1.4** Hacer clic en una fila de "Subcontratación vencida" → se abre el Quick View.
- [ ] **1.5** El drawer muestra: Cliente, Entrega, Estado (badge), Margen %, Alertas (resumen), ítems (lista compacta), usuarios asignados, último cambio de estado.

---

## 2. Cierre del Quick View

- [ ] **2.1** Botón **X** (arriba derecha) cierra el drawer.
- [ ] **2.2** Clic en el **overlay** (fondo oscuro) cierra el drawer.
- [ ] **2.3** Tras cerrar, el dashboard sigue visible sin recargar; las tablas no se refrescan innecesariamente.

---

## 3. Acciones en celdas (sin abrir Quick View)

- [ ] **3.1** En "Urgente", el botón **Iniciar** (o acciones en columna derecha) ejecuta la acción **sin** abrir el drawer (gracias a `@click.stop`).
- [ ] **3.2** En "Alertas críticas", el desplegable de asignación no abre el drawer al hacer clic.
- [ ] **3.3** En "Pendientes de aprobación", los botones **Aprobar** / **Rechazar** no abren el drawer.
- [ ] **3.4** En "Subcontratación vencida", el botón **Marcar recibido** no abre el drawer.

---

## 4. Botones dentro del Quick View

- [ ] **4.1** Si la OT está en **Waiting Approval**: aparece botón **Aprobar**; al pulsarlo se ejecuta la acción y el detalle se actualiza (o se cierra según implementación).
- [ ] **4.2** Si la OT está **Approved**: aparece **Iniciar producción**; al pulsarlo la acción se ejecuta.
- [ ] **4.3** Si la OT está **Production**: aparece **Finalizar**; al pulsarlo la acción se ejecuta.
- [ ] **4.4** Botón **Ver detalle completo** cierra el drawer y navega a `/orden/:sales_order` (vista OrderDetail). La ruta corresponde al `sales_order` de la OT mostrada.

---

## 5. Navegación a orden completa

- [ ] **5.1** Desde el Quick View, **Ver detalle completo** lleva a la misma orden que se vería yendo desde el listado a "Ver orden" (no se pierde la navegación original a `/orden/:id`).
- [ ] **5.2** Si se accede a `/orden/:id` por URL directa o por otro enlace, la vista OrderDetail sigue funcionando con normalidad.

---

## 6. UX y rendimiento

- [ ] **6.1** El drawer entra con animación **slide-in** desde la derecha (Tailwind/transition).
- [ ] **6.2** Hay **scroll interno** dentro del contenido del drawer cuando hay muchos ítems o texto.
- [ ] **6.3** Al abrir el Quick View **no** se recarga todo el dashboard: solo se hace fetch de `get_work_order_details(work_order_id)` para esa OT.
- [ ] **6.4** Con el drawer abierto, no hay parpadeos ni recarga de las tablas del dashboard.

---

## 7. Estados de carga y error

- [ ] **7.1** Mientras se cargan los datos del detalle, se muestra un estado de carga (spinner o skeleton) en el drawer.
- [ ] **7.2** Si el detalle falla (ej. OT inexistente o error de red), se muestra un mensaje de error en el drawer y se puede cerrar con X o overlay.

---

## Resumen

- **Quick View:** `frontend/src/components/QuickViewWorkOrder.vue`
- **Dashboard:** `frontend/src/views/DashboardOperativo.vue` (estado `quickViewId`, `quickViewVisible`, clic en fila → `openQuickView(row)`).
- **Navegación original:** Conservada mediante el botón "Ver detalle completo" dentro del Quick View (`router.push('/orden/' + sales_order)`).
