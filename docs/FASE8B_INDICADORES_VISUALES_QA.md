# Fase 8B – Indicadores visuales avanzados: checklist QA visual

## Objetivo
Comprobar que las señales visuales de urgencia y margen se aplican correctamente en las filas del Dashboard Operativo (solo UI, sin cambios de backend).

---

## Helpers (lógica)

- [ ] **H1** `isOverdue(delivery_date)`: devuelve `true` cuando la fecha de entrega es **anterior a hoy** (solo fecha, sin hora).
- [ ] **H2** `isDueToday(delivery_date)`: devuelve `true` cuando la fecha de entrega es **hoy**.
- [ ] **H3** `isLowMargin(margin_pct)`: devuelve `true` cuando el margen es **&lt; 15** (porcentaje).
- [ ] **H4** `isNegativeMargin(margin_pct)`: devuelve `true` cuando el margen es **&lt; 0** (porcentaje).

---

## Estilos por condición

### 1. Fila vencida (overdue)

- [ ] **V1** Si la OT tiene `delivery_date` en el pasado, la **fila** muestra **borde izquierdo rojo grueso** (`border-l-4 border-red-500`).
- [ ] **V2** Comportamiento correcto en las **cuatro tablas**: Urgentes, Alertas críticas, Esperando aprobación, Tercerización vencida.

### 2. Fila entrega hoy (due today)

- [ ] **V3** Si la OT tiene `delivery_date` = hoy, la **fila** tiene **fondo naranja claro** (`bg-orange-50`).
- [ ] **V4** No se aplica si la fila es overdue (ambas condiciones pueden coexistir; se ven borde rojo + fondo naranja si aplica, o solo el que corresponda).

### 3. Margen bajo (&lt; 15 %)

- [ ] **V5** En la tabla **Urgentes**, la celda de **Margen %** muestra el número en **rojo y negrita** (`text-red-500 font-semibold`) cuando el margen es &lt; 15.
- [ ] **V6** Cuando el margen es ≥ 15, se mantienen los colores existentes (ámbar/verde según `marginClass`).

### 4. Margen negativo (&lt; 0)

- [ ] **V7** Si el margen es negativo, la **fila** tiene **fondo rojo muy claro** (`bg-red-50`).
- [ ] **V8** Comportamiento en las cuatro tablas cuando existan OTs con margen negativo.

### 5. Alertas peligro (danger &gt; 0)

- [ ] **V9** Cuando `alerts_summary.danger > 0`, se muestra el **ícono AlertTriangle** (lucide) en **rojo** y con **animate-pulse**.
- [ ] **V10** En **Urgentes**: ícono junto al badge de estado (sustituye o complementa el punto rojo; según implementación es ícono con pulse).
- [ ] **V11** En **Alertas críticas**: ícono junto al texto de la alerta en la columna "Alerta".
- [ ] **V12** En **Esperando aprobación**: ícono en la celda "Tiempo / Alerta" cuando hay danger.
- [ ] **V13** En **Tercerización vencida**: ícono junto al estado cuando hay danger.

---

## Resumen visual

| Condición              | Dónde        | Clase / efecto                          |
|------------------------|-------------|-----------------------------------------|
| Overdue                | Fila `<tr>` | `border-l-4 border-red-500`             |
| Due today              | Fila `<tr>` | `bg-orange-50`                          |
| Margen &lt; 15         | Celda margen| `text-red-500 font-semibold`            |
| Margen &lt; 0          | Fila `<tr>` | `bg-red-50`                             |
| alerts_summary.danger &gt; 0 | Celda estado/alerta | Ícono AlertTriangle `text-red-500 animate-pulse` |

---

## Lista de clases Tailwind usadas (Fase 8B)

- **Borde:** `border-l-4`, `border-red-500`
- **Fondo:** `bg-orange-50`, `bg-red-50`
- **Texto:** `text-red-500`, `font-semibold`
- **Ícono alerta:** `text-red-500`, `animate-pulse`, `h-4 w-4`, `shrink-0`
- **Layout ícono+texto:** `inline-flex`, `items-center`, `gap-1`

*(Las clases ya existentes en las tablas —p. ej. `hover:bg-*`, `transition-colors`, `cursor-pointer`— no se listan aquí.)*

---

## Sin cambios de backend

- [ ] **B1** No se han modificado endpoints ni lógica de API.
- [ ] **B2** Los datos de fila (`delivery_date`, `gross_margin_pct`, `alerts_summary`) siguen viniendo del backend actual; solo se usan en el frontend para decidir las clases y el ícono.
