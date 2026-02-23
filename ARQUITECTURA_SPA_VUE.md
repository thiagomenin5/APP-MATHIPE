# Arquitectura: SPA Vue.js como frontend en app.graficamathipe.com.ar

## Objetivo

Que **https://app.graficamathipe.com.ar/** sirva tu SPA Vue (estilo Twist Print) y **no** el Desk ni la web por defecto de ERPNext. ERPNext queda como backend (headless) vía API.

---

## Estructura de carpetas (final)

```
apps/mathipe_ui/
├── mathipe_ui/                    # Paquete Python de la app
│   ├── __init__.py                # Patch para servir SPA en /
│   ├── hooks.py
│   ├── spa_serve.py               # Lógica que sirve index.html en /
│   ├── public/
│   │   └── spa/                   # Build de Vue (index.html + assets/)
│   │       ├── index.html
│   │       └── assets/
│   ├── ...
│   └── www/                       # (opcional) estáticos
├── frontend/                      # Proyecto Vue 3 + Vite + Tailwind
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   └── Dashboard.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   └── api/
│   │       └── frappe.js          # Cliente API + login
│   └── ...
└── ...
```

---

## Flujo

1. **Producción:** Usuario entra a `app.graficamathipe.com.ar/` → el servidor (patch en `get_response`) devuelve `mathipe_ui/public/spa/index.html` → el navegador carga Vue y los assets desde `/assets/mathipe_ui/spa/`.
2. **Desarrollo:** `npm run dev` en `frontend/` con proxy a tu sitio → mismo dominio, sin CORS.
3. **Login:** La SPA llama a `/api/method/login` con usuario/contraseña; el backend Frappe devuelve cookie de sesión; el resto de llamadas usan esa sesión.

---

## Rutas SPA

El patch considera estas rutas como “de la SPA” y devuelve `index.html` (para Vue Router en modo history):

- `/`
- `/login`
- `/dashboard`
- `/cotizador`
- Cualquier ruta bajo `/app/` que prefieras delegar a la SPA (opcional).

El resto (por ejemplo `/api/`, `/assets/`, `/files/`) lo sigue resolviendo Frappe.
