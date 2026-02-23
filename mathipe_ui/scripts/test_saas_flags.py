"""
Tests SAAS: feature flags, branding y gating de módulos.

Uso:
    bench --site [site] migrate
    bench --site [site] execute mathipe_ui.scripts.test_saas_flags.run_tests

Verifica:
    - get_financial_dashboard bloquea si finanzas no habilitado (plan Basic sin enabled_modules).
    - Con plan Internal se permite get_financial_dashboard.
    - get_branding devuelve defaults (display_name) si no existe o no está configurado.
"""

import frappe

OK = "  [OK]"
FAIL = "  [FAIL]"


def _check(label, condition, detail=""):
    status = OK if condition else FAIL
    msg = f"{status} {label}"
    if detail:
        msg += f"  → {detail}"
    print(msg)
    return condition


def run_tests():
    frappe.set_user("Administrator")
    errors = []

    print("\n=== TEST SAAS FLAGS / BRANDING ===\n")

    from mathipe_ui.api import (
        get_branding,
        get_financial_dashboard,
        get_subscription_context,
        feature_enabled,
    )

    # Guardar estado original de Mathipe Settings para restaurar al final
    if not frappe.db.exists("DocType", "Mathipe Settings"):
        print(f"{FAIL} Mathipe Settings no existe. Ejecutar migrate primero.")
        return

    doc = frappe.get_single("Mathipe Settings")
    # Campos SAAS se agregan por Custom Field (patch add_saas_branding_and_subscription)
    if not hasattr(doc, "subscription_plan") and not hasattr(doc, "subscription_status"):
        print(f"{FAIL} Mathipe Settings sin campos SAAS. Ejecutar: bench --site [site] migrate")
        return

    saved_plan = getattr(doc, "subscription_plan", None) or ""
    saved_status = getattr(doc, "subscription_status", None) or ""
    saved_modules = getattr(doc, "enabled_modules", None) or ""

    try:
        # ── 1) get_branding devuelve defaults ─────────────────────────────────
        branding = get_branding()
        if not _check("get_branding devuelve dict", isinstance(branding, dict), str(type(branding))):
            errors.append("get_branding no es dict")
        if branding and not _check("get_branding tiene display_name", "display_name" in branding):
            errors.append("get_branding sin display_name")
        if branding and not _check("get_branding display_name no vacío", (branding.get("display_name") or "").strip()):
            errors.append("display_name vacío (default esperado: APP Mathipe)")
        print("  get_branding:", branding.get("display_name"), branding.get("logo_url"))

        # ── 2) Plan Basic, status Active, sin enabled_modules → finanzas bloqueado ─
        doc.subscription_plan = "Basic"
        doc.subscription_status = "Active"
        doc.enabled_modules = ""
        doc.flags.ignore_permissions = True
        doc.save()
        frappe.db.commit()
        frappe.clear_cache()

        ctx = get_subscription_context()
        if not _check("get_subscription_context Basic/Active", ctx.get("plan") == "Basic" and ctx.get("status") == "Active"):
            errors.append("subscription_context no refleja Basic/Active")

        if not _check("feature_enabled('finanzas') False con Basic sin módulos", not feature_enabled("finanzas")):
            errors.append("feature_enabled finanzas debería ser False para Basic sin enabled_modules")

        try:
            get_financial_dashboard()
            if not _check("get_financial_dashboard bloqueado con Basic", False, "debería haber lanzado"):
                errors.append("get_financial_dashboard no bloqueó con plan Basic sin finanzas")
        except (frappe.PermissionError, Exception) as e:
            msg = str(e) if e else ""
            if _check("get_financial_dashboard lanza con mensaje plan", "plan" in msg.lower() or "Finanzas" in msg or "PermissionError" in msg):
                pass
            else:
                errors.append("get_financial_dashboard lanzó pero mensaje inesperado: " + msg[:80])

        # ── 3) Plan Internal → todo permitido ───────────────────────────────
        doc.subscription_plan = "Internal"
        doc.subscription_status = "Active"
        doc.enabled_modules = ""
        doc.flags.ignore_permissions = True
        doc.save()
        frappe.db.commit()
        frappe.clear_cache()

        if not _check("feature_enabled('finanzas') True con Internal", feature_enabled("finanzas")):
            errors.append("feature_enabled finanzas debería ser True para Internal")

        try:
            out = get_financial_dashboard()
            if not _check("get_financial_dashboard OK con Internal", isinstance(out, dict) and "total_revenue" in out):
                errors.append("get_financial_dashboard no devolvió dict con total_revenue")
        except Exception as e:
            if not _check("get_financial_dashboard sin excepción con Internal", False, str(e)):
                errors.append("get_financial_dashboard lanzó con Internal: " + str(e)[:80])

    finally:
        # Restaurar estado original
        doc = frappe.get_single("Mathipe Settings")
        doc.subscription_plan = saved_plan or "Internal"
        doc.subscription_status = saved_status or "Active"
        doc.enabled_modules = saved_modules
        doc.flags.ignore_permissions = True
        doc.save()
        frappe.db.commit()
        frappe.clear_cache()

    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests SAAS pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()
