# Build y despliegue – SPA Vue (Mathipe UI)

## Estructura ya creada

- **Frontend:** `apps/mathipe_ui/frontend/` (Vue 3 + Vite + Tailwind).
- **Build de salida:** `apps/mathipe_ui/mathipe_ui/public/spa/` (index.html + assets/).
- **Enrutamiento:** Al entrar en `app.graficamathipe.com.ar/` el patch en `mathipe_ui/spa_serve.py` sirve ese `index.html`; los estáticos se piden a `/assets/mathipe_ui/spa/`.

---

## Desarrollo local

```bash
cd /home/frappe/frappe-bench/apps/mathipe_ui/frontend
npm install
npm run dev
```

- Abre **http://localhost:5173**. El proxy de Vite redirige `/api`, `/assets` y `/files` a `https://app.graficamathipe.com.ar`, así que el login y la API funcionan sin CORS.
- Para probar contra un backend local: en `vite.config.js` cambia `target` del proxy a `http://localhost:8000` (o la URL de tu bench).

---

## Build para producción

```bash
cd /home/frappe/frappe-bench/apps/mathipe_ui/frontend
npm install
npm run build
```

- Esto escribe en `mathipe_ui/public/spa/` (index.html y carpeta assets/).
- No hace falta correr `bench build` solo por la SPA: los archivos en `public/` se sirven desde la app. Si en tu instalación usas `bench build` para otros assets, puedes seguir usándolo; la SPA ya está en `public/spa/`.

---

## Despliegue en el servidor

1. **Subir código** (incluido `frontend/`) al servidor, o clonar/actualizar el repo en el bench.
2. **En el servidor, compilar la SPA:**
   ```bash
   cd /home/frappe/frappe-bench/apps/mathipe_ui/frontend
   npm ci
   npm run build
   ```
3. **Reiniciar el proceso que sirve la web** (p. ej. bench o gunicorn/supervisor), para que cargue el patch que sirve la SPA en `/`.
4. **Comprobar:** Abrir `https://app.graficamathipe.com.ar/` y ver la pantalla de login de la SPA; tras iniciar sesión, que cargue el Dashboard.

---

## Si la raíz no muestra la SPA

- Confirma que existe `mathipe_ui/public/spa/index.html` (generado por `npm run build`).
- Confirma que la app `mathipe_ui` está instalada y que su `__init__.py` carga el patch (`mathipe_ui.spa_serve.patch_website_serve`).
- En sitios multitenant, que estés entrando al sitio correcto (el que tiene la app instalada).

---

## Resumen de comandos (servidor)

```bash
# Build de la SPA (una vez o tras cambios en el frontend)
cd /home/frappe/frappe-bench/apps/mathipe_ui/frontend && npm ci && npm run build

# Reiniciar bench (ejemplo)
cd /home/frappe/frappe-bench && bench restart
```
