# Checklist QA — Base SAAS (multi-tenant por multisite)

Validación visual y funcional después de implementar la base SAAS.

## 1. Branding (logo / nombre)

- [ ] **Sidebar:** La cabecera del sidebar muestra el **nombre visible** configurado en Mathipe Settings (Company Display Name), no "App Mathipe" hardcodeado.
- [ ] **Sidebar:** Si hay **logo** subido en Mathipe Settings, se muestra en la cabecera del sidebar en lugar del icono por defecto.
- [ ] **Login:** La pantalla de login muestra el mismo **nombre visible** (no "Gráfica Mathipe").
- [ ] **Título de la página:** Tras cargar la app (MainLayout), `document.title` coincide con el nombre visible del tenant.
- [ ] **index.html:** El título por defecto es "APP Mathipe" (o el que corresponda si se personaliza en build).

## 2. Sidebar y módulos por plan

- [ ] Con **plan Internal** (Mathipe Settings): se ven en el sidebar **Finanzas**, **Alertas** y **Analítica** bajo Administración.
- [ ] Con **plan Basic** y **enabled_modules** vacío: **Finanzas**, **Alertas** y **Analítica** no aparecen en el sidebar (o según lógica: Basic sin override = no módulos premium).
- [ ] Con **plan Basic** y **enabled_modules** = "Finanzas, Alertas": solo Finanzas y Alertas visibles en el sidebar; Analítica no.
- [ ] **Subscription context** se carga al abrir la app (sin errores en consola).

## 3. Bloqueo de módulos por URL

- [ ] Con un plan que **no** incluye Finanzas: al ir directamente a `/admin/finanzas` se muestra la pantalla **"No disponible en tu plan"** con mensaje "Tu plan no incluye Finanzas." y botón "Ir al Dashboard".
- [ ] Con un plan que **no** incluye Alertas: al ir a `/admin/alertas` se muestra "No disponible en tu plan".
- [ ] Con un plan que **no** incluye Analítica: al ir a `/admin/analitica` se muestra "No disponible en tu plan".
- [ ] Con **plan Internal**: las tres rutas cargan normal (Finanzas, Alertas, Analítica).

## 4. Backend (opcional desde consola)

- [ ] `get_branding()` devuelve `display_name`, `logo_url`, `primary_color`, etc. (por defecto "APP Mathipe" si no hay doc/config).
- [ ] Con plan Basic y sin "Finanzas" en enabled_modules: llamar a `get_financial_dashboard` (p. ej. desde la SPA) devuelve error **"Tu plan no incluye Finanzas."** (403/PermissionError).
- [ ] Con plan Internal: `get_financial_dashboard`, `get_alerts_board`, `get_profitability_breakdown` responden sin error.

## 5. Compatibilidad con el site actual

- [ ] El **site actual** (tenant existente) sigue funcionando: migrar y ejecutar el patch no rompe nada.
- [ ] Si en el site actual no existía Company Display Name, se muestra el default "APP Mathipe".
- [ ] Si no se configuró subscription_plan, el default es **Internal** (todo habilitado).

---

**Comandos útiles**

```bash
# Migrar (aplica patch SAAS)
bench --site [site] migrate

# Tests automatizados SAAS
bench --site [site] execute mathipe_ui.scripts.test_saas_flags.run_tests

# Seed para nuevo tenant
bench --site [site] execute mathipe_ui.scripts.seed_base_data.run
```

Ver **SAAS_PROVISIONING.md** para pasos completos de provisioning de un nuevo tenant.
