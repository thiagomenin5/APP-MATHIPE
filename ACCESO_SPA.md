# Acceso a la SPA (estilo Twist / tu ERP)

## Comportamiento deseado

- **Al entrar a** `https://app.graficamathipe.com.ar/` **deberías:**
  1. Ver la **pantalla de login de la SPA** (Gráfica Mathipe), no la de Frappe.
  2. Tras iniciar sesión, entrar **directo al Dashboard** de la SPA (Panel de Control, órdenes recientes, etc.).

Eso se consigue con el patch que sirve la SPA en `/` y `/login` y con el redirect post-login a `/dashboard`.

## Las dos interfaces en el mismo dominio

### 1. SPA Vue (mathipe_ui) — tu ERP estilo Twist

- **URLs:** `/`, `/login`, `/dashboard`, `/orden/:id`, etc.
- **Menú:** "Gráfica Mathipe" (Dashboard, Producción, Cotizador, Inventario, Compras, Configuración).
- **Aquí están** el Panel de Control, el detalle de orden con archivos e "Iniciar Producción" / "Marcar Terminado".

### 2. Frappe Desk (ERPNext estándar)

- **URLs:** `/app`, `/app/mathipe`, etc.
- **Menú:** Proyectos, Órdenes, Facturas, Mi Cuenta, etc.
- Si hacés clic en la app **MATHIPE** en el Desk, se redirige a `/dashboard` (SPA).

## Cómo usar

1. **Entrá a** `https://app.graficamathipe.com.ar/` (solo la raíz, sin `/app`).
2. Si no estás logueado, verás el **login de la SPA** (no el de Frappe).
3. Después de iniciar sesión irás al **Dashboard** de la SPA.
4. Desde "Órdenes recientes", un clic en una fila te lleva al **Detalle de orden** (`/orden/:id`).

## Si en la raíz ves el login de Frappe

Puede pasar si el patch de la SPA no se aplica (por ejemplo la app no está en `installed_apps` o el build de la SPA no está en `public/spa/`). Revisá:

- Que `mathipe_ui` esté instalada en el bench.
- Que hayas hecho `npm run build` en `frontend/` y que exista `mathipe_ui/public/spa/index.html`.

## Resumen de URLs

| Objetivo              | URL                                   |
|-----------------------|----------------------------------------|
| Entrar al ERP (SPA)   | `https://app.graficamathipe.com.ar/`   |
| Dashboard             | `/dashboard`                           |
| Detalle de orden      | `/orden/NOMBRE-ORDEN`                  |
| Desk estándar         | `/app`                                 |
