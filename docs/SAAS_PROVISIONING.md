# Provisioning de un nuevo tenant (SAAS multisite)

Cada **tenant = un Site** de Frappe (multisite). No se agrega campo "empresa" a DocTypes; todo lo visible de marca/empresa sale de **Mathipe Settings** por site.

## Pasos para crear un nuevo tenant

### 1. Crear el site

```bash
bench new-site <tenant>
```

Ejemplo: `bench new-site cliente2.graficamathipe.com.ar`

### 2. Instalar la app en el site

```bash
bench --site <tenant> install-app mathipe_ui
```

### 3. Migrar (incluye patches de SAAS: branding y suscripción)

```bash
bench --site <tenant> migrate
```

### 4. Seed de datos base (roles, Settings con defaults, branding)

```bash
bench --site <tenant> execute mathipe_ui.scripts.seed_base_data.run
```

Con opcionales (nombre visible, email de soporte, cliente demo):

```bash
bench --site <tenant> execute mathipe_ui.scripts.seed_base_data.run --kwargs '{"site_defaults": {"company_display_name": "Mi Empresa", "support_email": "soporte@miempresa.com", "create_demo_customer": true}}'
```

### 5. Crear usuario administrador del tenant

```bash
bench --site <tenant> add-user <email> --first-name <Nombre> --last-name <Apellido> --password <contraseña> --user-type "System User" --admin
```

O desde la consola:

```bash
bench --site <tenant> console
```

```python
frappe.get_doc({
    "doctype": "User",
    "email": "admin@tenant.com",
    "first_name": "Admin",
    "last_name": "Tenant",
    "user_type": "System User",
    "send_welcome_email": 0,
}).insert()
frappe.db.commit()
```

Luego asignar contraseña y rol System Manager desde el Desk o `bench set-password <email> <password>`.

---

## Resumen de comandos

| Paso | Comando |
|------|--------|
| Crear site | `bench new-site <tenant>` |
| Instalar app | `bench --site <tenant> install-app mathipe_ui` |
| Migrar | `bench --site <tenant> migrate` |
| Seed base | `bench --site <tenant> execute mathipe_ui.scripts.seed_base_data.run` |
| Usuario admin | `bench --site <tenant> add-user ...` o consola |

---

## Configuración por tenant (Mathipe Settings)

- **Branding:** `company_display_name`, `company_legal_name`, `logo`, `primary_color`, `support_email`, `timezone`, `currency`.
- **Planes (sin cobros):** `subscription_plan` (Internal / Basic / Pro / Enterprise), `subscription_status` (Active / Trial / Suspended), `trial_ends_on`, `enabled_modules` (lista separada por comas: Finanzas, Analitica, Alertas, Tercerizacion).

Con **Internal** todo está habilitado. Con otros planes, si `enabled_modules` tiene valores se usa como override; si está vacío, Pro/Enterprise tienen todos los módulos gated habilitados.
