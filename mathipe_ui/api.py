# Copyright (c) 2025, Mathipe UI and contributors
# API whitelisted para el dashboard y la SPA.

from __future__ import unicode_literals

from datetime import date, timedelta

import frappe


def _escape_like(s):
    """Escapa % _ \ para usar en LIKE y evitar patrones que matcheen todo."""
    if not s:
        return ""
    return (s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_"))


def _empty_dashboard():
    return {
        "sales_total": 0,
        "orders_pending": 0,
        "orders_in_production": 0,
        "recent_orders": [],
    }


@frappe.whitelist()
def get_session_data():
    """Devuelve user y csrf_token para la SPA (llamar con GET; no requiere CSRF)."""
    return {
        "user": frappe.session.user if frappe.session else None,
        "csrf_token": frappe.sessions.get_csrf_token() if getattr(frappe.local, "session", None) else None,
    }


@frappe.whitelist()
def get_dashboard_data():
    """Devuelve KPIs reales y últimas órdenes para el dashboard."""
    if not frappe.db.table_exists("Sales Order"):
        return _empty_dashboard()

    today = date.today()
    first_day = today.replace(day=1)

    # Ventas del mes: suma grand_total, mes actual, excluir canceladas
    sales_total = 0
    try:
        sales_total = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabSales Order`
            WHERE status != 'Cancelled' AND status != 'Closed'
              AND transaction_date >= %(first)s AND transaction_date <= %(today)s
        """, {"first": first_day, "today": today}, as_dict=False)[0][0] or 0
        sales_total = float(sales_total)
    except Exception:
        pass

    # En cola: Draft o To Deliver, sin tag "En Producción" ni "Terminado"
    orders_pending = 0
    orders_in_production = 0
    has_user_tags = frappe.db.has_column("Sales Order", "_user_tags")
    if has_user_tags:
        try:
            orders_pending = frappe.db.sql("""
                SELECT COUNT(*)
                FROM `tabSales Order`
                WHERE status IN ('Draft', 'To Deliver')
                  AND (COALESCE(_user_tags, '') NOT LIKE %(tag_prod)s AND COALESCE(_user_tags, '') NOT LIKE %(tag_term)s)
            """, {"tag_prod": "%En Producción%", "tag_term": "%Terminado%"}, as_dict=False)[0][0] or 0
            orders_in_production = frappe.db.sql("""
                SELECT COUNT(*)
                FROM `tabSales Order`
                WHERE _user_tags LIKE %(tag_prod)s
            """, {"tag_prod": "%En Producción%"}, as_dict=False)[0][0] or 0
        except Exception:
            pass
    else:
        try:
            orders_pending = frappe.db.count(
                "Sales Order",
                filters={"status": ["in", ["Draft", "To Deliver"]]},
            )
        except Exception:
            pass

    # Últimas 5 órdenes (cualquier status no cancelado)
    recent_orders = []
    try:
        recent = frappe.get_all(
            "Sales Order",
            fields=["name", "customer", "customer_name", "grand_total", "status"],
            filters={"status": ["not in", ["Cancelled", "Closed"]]},
            order_by="modified desc",
            limit=5,
        )
        for r in recent:
            recent_orders.append({
                "name": r.get("name") or "",
                "customer_name": (r.get("customer_name") or r.get("customer") or "").strip(),
                "grand_total": float(r.get("grand_total") or 0),
                "status": (r.get("status") or "").strip(),
            })
    except Exception:
        pass

    return {
        "sales_total": sales_total,
        "orders_pending": int(orders_pending),
        "orders_in_production": int(orders_in_production),
        "recent_orders": recent_orders,
    }


@frappe.whitelist()
def get_order_details(order_id):
    """Devuelve orden, ítems y archivos adjuntos de una Sales Order para la vista del operario."""
    if not order_id:
        frappe.throw("order_id es requerido")

    try:
        so = frappe.get_doc("Sales Order", order_id)
    except frappe.DoesNotExistError:
        frappe.throw("Orden no encontrada")

    order = {
        "name": so.name,
        "customer": so.customer or "",
        "customer_name": so.customer_name or so.customer or "",
        "delivery_date": so.delivery_date.strftime("%Y-%m-%d") if so.delivery_date else "",
        "status": so.status or "",
        "grand_total": float(so.grand_total or 0),
    }

    # Tags (para saber si está en producción / terminado)
    tags = []
    if frappe.db.has_column("Sales Order", "_user_tags") and getattr(so, "_user_tags", None):
        tags = [t.strip() for t in (so._user_tags or "").split(",") if t.strip()]

    items = []
    for row in getattr(so, "items", []) or []:
        items.append({
            "item_code": row.get("item_code") or "",
            "description": row.get("description") or row.get("item_name") or "",
            "qty": float(row.get("qty") or 0),
            "uom": row.get("uom") or "",
        })

    attachments = []
    try:
        file_list = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Sales Order",
                "attached_to_name": order_id,
            },
            fields=["name", "file_name", "file_url"],
            order_by="creation desc",
        )
        for f in file_list or []:
            attachments.append({
                "name": f.get("name") or "",
                "file_name": f.get("file_name") or "",
                "file_url": f.get("file_url") or "",
            })
    except Exception:
        pass

    return {
        "order": order,
        "items": items,
        "files": attachments,
        "attachments": attachments,
        "tags": tags,
    }


@frappe.whitelist()
def update_order_workflow(order_id, action):
    """Actualiza el estado de la orden según la acción del operario (iniciar / terminar producción)."""
    if not order_id or not action:
        frappe.throw("order_id y action son requeridos")

    try:
        so = frappe.get_doc("Sales Order", order_id)
    except frappe.DoesNotExistError:
        frappe.throw("Orden no encontrada")

    current = (so.status or "").strip()
    action = (action or "").strip().lower()

    if action == "start_production":
        if current in ("Completed", "Delivered", "Closed", "Cancelled"):
            frappe.throw("La orden ya está finalizada o cerrada.")
        frappe.db.set_value("Sales Order", order_id, "status", "To Deliver")
        frappe.db.commit()
        return {
            "status": "To Deliver",
            "message": "Producción iniciada.",
        }
    if action == "finish_production":
        if current in ("Draft", "Cancelled", "Closed"):
            frappe.throw("No se puede marcar como terminada esta orden.")
        frappe.db.set_value("Sales Order", order_id, "status", "Completed")
        frappe.db.commit()
        return {
            "status": "Completed",
            "message": "Orden marcada como terminada.",
        }

    frappe.throw("Acción no válida. Use start_production o finish_production.")


def _build_items_summary(order_names):
    """Construye un resumen de ítems por orden: 'Tarjetas x1000' o 'Item1 x qty, Item2 x qty'."""
    if not order_names:
        return {}
    try:
        rows = frappe.get_all(
            "Sales Order Item",
            filters={"parent": ["in", list(order_names)]},
            fields=["parent", "item_name", "item_code", "qty"],
            order_by="idx",
        )
    except Exception:
        return {n: "" for n in order_names}
    summary = {}
    for r in rows:
        parent = r.get("parent")
        if parent not in summary:
            summary[parent] = []
        name = (r.get("item_name") or r.get("item_code") or "").strip() or "Ítem"
        qty = int(r.get("qty") or 0)
        summary[parent].append("{0} x{1}".format(name, qty))
    out = {}
    for n in order_names:
        parts = summary.get(n) or []
        out[n] = ", ".join(parts[:3]) if parts else ""
        if len(parts) > 3:
            out[n] += " (+{0})".format(len(parts) - 3)
    return out


def _items_preview_for_orders(order_names):
    """Devuelve para cada orden un string con el primer ítem (ej: '100 Tarjetas...')."""
    if not order_names:
        return {}
    try:
        rows = frappe.get_all(
            "Sales Order Item",
            filters={"parent": ["in", list(order_names)]},
            fields=["parent", "item_name", "item_code", "qty"],
            order_by="idx",
        )
    except Exception:
        return {n: "" for n in order_names}
    # Primer ítem por parent
    first = {}
    for r in rows:
        parent = r.get("parent")
        if parent not in first:
            name = (r.get("item_name") or r.get("item_code") or "").strip() or "Ítem"
            qty = int(r.get("qty") or 0)
            first[parent] = "{0} x{1}".format(name, qty)
    return {n: first.get(n, "") for n in order_names}


def _item_summary_for_board(order_names):
    """Descripción del primer ítem para el tablero: description si existe, sino 'ItemName x Qty'."""
    if not order_names:
        return {}
    fields = ["parent", "item_name", "item_code", "qty"]
    if frappe.db.has_column("Sales Order Item", "description"):
        fields.append("description")
    try:
        rows = frappe.get_all(
            "Sales Order Item",
            filters={"parent": ["in", list(order_names)]},
            fields=fields,
            order_by="idx",
        )
    except Exception:
        return {n: "" for n in order_names}
    first = {}
    for r in rows:
        parent = r.get("parent")
        if parent not in first:
            desc = (r.get("description") or "").strip() if r.get("description") else None
            if desc:
                first[parent] = desc
            else:
                name = (r.get("item_name") or r.get("item_code") or "").strip() or "Ítem"
                qty = int(r.get("qty") or 0)
                first[parent] = "{0} x{1}".format(name, qty)
    return {n: first.get(n, "") for n in order_names}


def _time_since(dt):
    """Devuelve texto tipo 'hace 2 días', 'hoy', 'hace 1 semana'."""
    if not dt:
        return ""
    from frappe.utils import now_datetime, getdate
    from datetime import datetime
    if hasattr(dt, "date"):
        d = dt.date() if hasattr(dt, "date") else dt
    else:
        d = getdate(dt)
    today = getdate()
    delta = (today - d).days
    if delta == 0:
        return "Hoy"
    if delta == 1:
        return "Ayer"
    if delta == 2:
        return "Hace 2 días"
    if delta < 7:
        return "Hace {0} días".format(delta)
    if delta < 14:
        return "Hace 1 semana"
    if delta < 30:
        return "Hace {0} semanas".format(delta // 7)
    if delta < 60:
        return "Hace 1 mes"
    return "Hace {0} meses".format(delta // 30)


@frappe.whitelist()
def get_sales_orders_list(status=None, search_term=None):
    """Listado de Sales Orders para la vista Orden de trabajo. Filtros opcionales: status, search_term."""
    if not frappe.db.table_exists("Sales Order"):
        return []

    status = (status or "").strip()
    search_term = (search_term or "").strip()

    filters = {}
    if status == "Pendientes":
        filters["status"] = ["in", ["Draft", "Submitted", "To Bill", "To Deliver", "Partially Delivered"]]
    elif status == "Completados":
        filters["status"] = ["in", ["Delivered", "Completed"]]
    # "Todos" o vacío: sin filtro por status (incluye todos salvo que quieras excluir Cancelled)

    or_filters = []
    if search_term:
        or_filters = [
            ["name", "like", "%" + _escape_like(search_term) + "%"],
            ["customer_name", "like", "%" + _escape_like(search_term) + "%"],
        ]

    fields = ["name", "customer", "customer_name", "grand_total", "transaction_date", "delivery_date", "status"]
    if frappe.db.has_column("Sales Order", "workflow_state"):
        fields.append("workflow_state")

    try:
        orders = frappe.get_all(
            "Sales Order",
            filters=filters,
            or_filters=or_filters if or_filters else None,
            fields=fields,
            order_by="modified desc",
            limit=500,
        )
    except Exception:
        return []

    order_names = [o.get("name") for o in orders if o.get("name")]
    items_preview = _items_preview_for_orders(order_names) if order_names else {}

    result = []
    for o in orders:
        name = o.get("name")
        if not name:
            continue
        transaction_date = o.get("transaction_date")
        delivery_date = o.get("delivery_date")
        result.append({
            "name": name,
            "customer_name": (o.get("customer_name") or o.get("customer") or "").strip(),
            "grand_total": float(o.get("grand_total") or 0),
            "transaction_date": transaction_date.strftime("%Y-%m-%d") if transaction_date else "",
            "delivery_date": delivery_date.strftime("%Y-%m-%d") if delivery_date else "",
            "status": (o.get("status") or "").strip(),
            "workflow_state": (o.get("workflow_state") or "").strip() if o.get("workflow_state") else "",
            "items_preview": items_preview.get(name, ""),
        })
    return result


PRODUCTION_TAG_IN_PROGRESS = "En Producción"
PRODUCTION_TAG_COMPLETED = "Terminado"

# Tags del flujo Visto Bueno (Preimpresión/Diseño)
DESIGN_TAG_IN_DESIGN = "En Diseño"
DESIGN_TAG_WAIT_OK = "Esperando OK"
DESIGN_TAG_APPROVED = "Visto Bueno"


def _get_production_column_for_so(user_tags_str):
    """Determina columna: Terminado -> completed, En Producción -> in_progress, Visto Bueno -> pending. Sin Visto Bueno no entra en pending."""
    tags = [t.strip() for t in (user_tags_str or "").split(",") if t.strip()]
    if PRODUCTION_TAG_COMPLETED in tags:
        return "completed"
    if PRODUCTION_TAG_IN_PROGRESS in tags:
        return "in_progress"
    if DESIGN_TAG_APPROVED in tags:
        return "pending"
    return None


@frappe.whitelist()
def get_production_board():
    """Tablero Kanban: órdenes agrupadas por tags (Pending, En Producción, Terminado).
    Excluye canceladas. Tarjetas con name, customer_name, delivery_date, item_summary, time_since."""
    if not frappe.db.table_exists("Sales Order"):
        return {"pending": [], "in_progress": [], "completed": []}

    fields = ["name", "customer_name", "delivery_date", "creation", "transaction_date"]
    if frappe.db.has_column("Sales Order", "_user_tags"):
        fields.append("_user_tags")
    try:
        orders = frappe.get_all(
            "Sales Order",
            filters={"status": ["not in", ["Cancelled", "Closed"]]},
            fields=fields,
            order_by="delivery_date asc",
            limit=200,
        )
    except Exception:
        return {"pending": [], "in_progress": [], "completed": []}

    order_names = [o.get("name") for o in orders if o.get("name")]
    item_summary_map = _item_summary_for_board(order_names) if order_names else {}

    pending = []
    in_progress = []
    completed = []
    for o in orders:
        name = o.get("name")
        if not name:
            continue
        user_tags = o.get("_user_tags") or ""
        column = _get_production_column_for_so(user_tags)
        if column is None:
            continue
        delivery = o.get("delivery_date")
        creation = o.get("creation") or o.get("transaction_date")
        card = {
            "name": name,
            "customer_name": (o.get("customer_name") or "").strip(),
            "delivery_date": delivery.strftime("%Y-%m-%d") if delivery else "",
            "item_summary": item_summary_map.get(name, ""),
            "time_since": _time_since(creation),
        }
        if column == "completed":
            completed.append(card)
        elif column == "in_progress":
            in_progress.append(card)
        else:
            pending.append(card)

    return {
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
    }


def _design_column_for_so(user_tags_str):
    """Columna del tablero de diseño: approved, working o inbox."""
    tags = [t.strip() for t in (user_tags_str or "").split(",") if t.strip()]
    if DESIGN_TAG_APPROVED in tags and PRODUCTION_TAG_IN_PROGRESS not in tags and PRODUCTION_TAG_COMPLETED not in tags:
        return "approved"
    if DESIGN_TAG_IN_DESIGN in tags or DESIGN_TAG_WAIT_OK in tags:
        return "working"
    return "inbox"


@frappe.whitelist()
def get_design_board():
    """Tablero Kanban Diseño: inbox (nuevos), working (En Diseño/Esperando OK), approved (Visto Bueno, sin producción)."""
    if not frappe.db.table_exists("Sales Order"):
        return {"inbox": [], "working": [], "approved": []}

    fields = ["name", "customer_name", "delivery_date", "creation", "transaction_date"]
    if frappe.db.has_column("Sales Order", "_user_tags"):
        fields.append("_user_tags")
    try:
        orders = frappe.get_all(
            "Sales Order",
            filters={"status": ["not in", ["Cancelled", "Closed"]]},
            fields=fields,
            order_by="delivery_date asc",
            limit=200,
        )
    except Exception:
        return {"inbox": [], "working": [], "approved": []}

    order_names = [o.get("name") for o in orders if o.get("name")]
    item_summary_map = _item_summary_for_board(order_names) if order_names else {}

    inbox = []
    working = []
    approved = []
    for o in orders:
        name = o.get("name")
        if not name:
            continue
        user_tags = o.get("_user_tags") or ""
        column = _design_column_for_so(user_tags)
        delivery = o.get("delivery_date")
        creation = o.get("creation") or o.get("transaction_date")
        card = {
            "name": name,
            "customer_name": (o.get("customer_name") or "").strip(),
            "delivery_date": delivery.strftime("%Y-%m-%d") if delivery else "",
            "item_summary": item_summary_map.get(name, ""),
            "time_since": _time_since(creation),
        }
        if column == "approved":
            approved.append(card)
        elif column == "working":
            working.append(card)
        else:
            inbox.append(card)

    return {"inbox": inbox, "working": working, "approved": approved}


@frappe.whitelist()
def update_design_status(order_id, action):
    """Acciones: start_design -> En Diseño; wait_client -> Esperando OK; approve -> Visto Bueno + comentario."""
    action = (action or "").strip().lower()
    if action not in ("start_design", "wait_client", "approve"):
        frappe.throw("action debe ser 'start_design', 'wait_client' o 'approve'")
    if not order_id:
        frappe.throw("order_id es requerido")
    try:
        so = frappe.get_doc("Sales Order", order_id)
    except frappe.DoesNotExistError:
        frappe.throw("Orden no encontrada")

    if action == "start_design":
        so.remove_tag(DESIGN_TAG_WAIT_OK)
        so.remove_tag(DESIGN_TAG_APPROVED)
        so.add_tag(DESIGN_TAG_IN_DESIGN)
    elif action == "wait_client":
        so.remove_tag(DESIGN_TAG_IN_DESIGN)
        so.add_tag(DESIGN_TAG_WAIT_OK)
    else:
        so.remove_tag(DESIGN_TAG_IN_DESIGN)
        so.remove_tag(DESIGN_TAG_WAIT_OK)
        so.add_tag(DESIGN_TAG_APPROVED)
        so.add_comment("Info", "Visto Bueno Aprobado. Listo para Taller.")

    so.flags.ignore_validate_update_after_submit = True
    so.save()
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def update_production_status(order_id, action):
    """Mueve una orden en el tablero: action='start' -> En Producción, action='finish' -> Terminado."""
    action = (action or "").strip().lower()
    if action not in ("start", "finish"):
        frappe.throw("action debe ser 'start' o 'finish'")
    if not order_id:
        frappe.throw("order_id es requerido")
    try:
        so = frappe.get_doc("Sales Order", order_id)
    except frappe.DoesNotExistError:
        frappe.throw("Orden no encontrada")

    if action == "start":
        so.remove_tag(PRODUCTION_TAG_COMPLETED)
        so.add_tag(PRODUCTION_TAG_IN_PROGRESS)
        so.add_comment("Info", "Producción Iniciada")
    else:
        so.remove_tag(PRODUCTION_TAG_IN_PROGRESS)
        so.add_tag(PRODUCTION_TAG_COMPLETED)
        so.add_comment("Info", "Producción Finalizada")

    so.flags.ignore_validate_update_after_submit = True
    so.save()
    frappe.db.commit()
    return {"ok": True}


# ----- Cotizador paramétrico (Twist Print) -----

def _print_material_doctype():
    return "Mathipe Print Material"

def _print_product_doctype():
    return "Mathipe Print Product"


@frappe.whitelist()
def get_print_materials():
    """Lista de materiales/sustratos para el cotizador paramétrico."""
    if not frappe.db.table_exists(_print_material_doctype()):
        return []
    try:
        rows = frappe.get_all(
            _print_material_doctype(),
            fields=["name", "material_name", "cost_per_sheet", "category"],
            order_by="material_name",
        )
        return [
            {
                "id": r.get("name"),
                "material_name": r.get("material_name") or r.get("name"),
                "cost_per_sheet": float(r.get("cost_per_sheet") or 0),
                "category": r.get("category") or "",
            }
            for r in (rows or [])
        ]
    except Exception:
        return []


@frappe.whitelist()
def get_all_print_products():
    """Lista todos los Mathipe Print Product para el ABM (Catálogo)."""
    if not frappe.db.table_exists(_print_product_doctype()):
        return []
    try:
        rows = frappe.get_all(
            _print_product_doctype(),
            fields=["name", "product_name", "base_setup_cost", "print_cost_per_side"],
            order_by="product_name",
        )
        return [
            {
                "name": r.get("name") or "",
                "product_name": (r.get("product_name") or r.get("name") or "").strip(),
                "base_setup_cost": float(r.get("base_setup_cost") or 0),
                "print_cost_per_side": float(r.get("print_cost_per_side") or 0),
            }
            for r in (rows or [])
        ]
    except Exception:
        return []


@frappe.whitelist()
def save_print_product(name=None, product_name=None, base_setup_cost=None, print_cost_per_side=None):
    """Crea o actualiza un Mathipe Print Product. name vacío = crear nuevo."""
    doctype = _print_product_doctype()
    if not frappe.db.table_exists(doctype):
        frappe.throw("El DocType de productos no existe")
    product_name = (product_name or "").strip()
    if not product_name:
        frappe.throw("El nombre del producto es requerido")
    try:
        base_setup_cost = float(base_setup_cost) if base_setup_cost not in (None, "") else 0
    except (TypeError, ValueError):
        base_setup_cost = 0
    try:
        print_cost_per_side = float(print_cost_per_side) if print_cost_per_side not in (None, "") else 0
    except (TypeError, ValueError):
        print_cost_per_side = 0

    if not name or not (str(name).strip()):
        doc = frappe.get_doc({
            "doctype": doctype,
            "product_name": product_name,
            "base_setup_cost": base_setup_cost,
            "print_cost_per_side": print_cost_per_side,
        })
        doc.insert()
        frappe.db.commit()
        return {"name": doc.name, "created": True}
    if not frappe.db.exists(doctype, name):
        frappe.throw("Producto no encontrado")
    doc = frappe.get_doc(doctype, name)
    doc.product_name = product_name
    doc.base_setup_cost = base_setup_cost
    doc.print_cost_per_side = print_cost_per_side
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "created": False}


@frappe.whitelist()
def delete_print_product(name):
    """Elimina un Mathipe Print Product por nombre."""
    name = (name or "").strip()
    if not name:
        frappe.throw("El nombre del producto es requerido")
    if not frappe.db.exists(_print_product_doctype(), name):
        frappe.throw("Producto no encontrado")
    frappe.delete_doc(_print_product_doctype(), name)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def get_print_products():
    """Lista de productos base (Tarjetas, Flyers, etc.) para el cotizador paramétrico."""
    if not frappe.db.table_exists(_print_product_doctype()):
        return []
    try:
        rows = frappe.get_all(
            _print_product_doctype(),
            fields=["name", "product_name", "base_setup_cost", "print_cost_per_side"],
            order_by="product_name",
        )
        return [
            {
                "id": r.get("name"),
                "product_name": r.get("product_name") or r.get("name"),
                "base_setup_cost": float(r.get("base_setup_cost") or 0),
                "print_cost_per_side": float(r.get("print_cost_per_side") or 0),
            }
            for r in (rows or [])
        ]
    except Exception:
        return []


@frappe.whitelist()
def get_inventory_materials():
    """Listado de materiales de impresión para la vista Inventario. Incluye stock_quantity dummy (0)."""
    if not frappe.db.table_exists(_print_material_doctype()):
        return []
    fields = ["name", "material_name", "category", "cost_per_sheet"]
    if frappe.db.has_column(_print_material_doctype(), "description"):
        fields.append("description")
    try:
        rows = frappe.get_all(
            _print_material_doctype(),
            fields=fields,
            order_by="material_name",
        )
    except Exception:
        return []
    out = []
    for r in (rows or []):
        out.append({
            "name": r.get("name") or "",
            "material_name": (r.get("material_name") or r.get("name") or "").strip(),
            "category": (r.get("category") or "").strip(),
            "cost_per_sheet": float(r.get("cost_per_sheet") or 0),
            "description": (r.get("description") or "").strip() if r.get("description") else "",
            "stock_quantity": 0,
        })
    return out


@frappe.whitelist()
def update_material_cost(material_name, new_cost):
    """Actualiza el costo por hoja de un Mathipe Print Material."""
    material_name = (material_name or "").strip()
    if not material_name:
        frappe.throw("material_name es requerido")
    try:
        new_cost = float(new_cost)
    except (TypeError, ValueError):
        frappe.throw("new_cost debe ser un número")
    if not frappe.db.table_exists(_print_material_doctype()):
        frappe.throw("El DocType de materiales no existe")
    if not frappe.db.exists(_print_material_doctype(), material_name):
        frappe.throw("Material no encontrado")
    doc = frappe.get_doc(_print_material_doctype(), material_name)
    doc.cost_per_sheet = new_cost
    doc.flags.ignore_validate_update_after_submit = True
    doc.save()
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def calculate_print_quote(product_id, material_id, qty, sides=1, width=None, height=None):
    """Calcula cotización paramétrica: material + impresión + puesta en máquina. Margen sugerido x2.5."""
    product_id = (product_id or "").strip()
    material_id = (material_id or "").strip()
    qty = int(float(qty or 0))
    sides = int(float(sides or 1))
    if sides not in (1, 2):
        sides = 1
    width = float(width or 0)
    height = float(height or 0)

    cost_per_sheet = 0.0
    if material_id and frappe.db.table_exists(_print_material_doctype()):
        try:
            val = frappe.db.get_value(
                _print_material_doctype(),
                material_id,
                "cost_per_sheet",
            )
            cost_per_sheet = float(val or 0)
        except Exception:
            pass

    base_setup_cost = 0.0
    print_cost_per_side = 0.0
    if product_id and frappe.db.table_exists(_print_product_doctype()):
        try:
            doc = frappe.db.get_value(
                _print_product_doctype(),
                product_id,
                ["base_setup_cost", "print_cost_per_side"],
                as_dict=True,
            )
            if doc:
                base_setup_cost = float(doc.get("base_setup_cost") or 0)
                print_cost_per_side = float(doc.get("print_cost_per_side") or 0)
        except Exception:
            pass

    # 1 unidad = 1 hoja (simplificado)
    material_cost = cost_per_sheet * qty
    print_cost = print_cost_per_side * sides * qty
    setup_cost = base_setup_cost
    total_cost = material_cost + print_cost + setup_cost
    suggested_price = total_cost * 2.5

    return {
        "material_cost": round(material_cost, 2),
        "print_cost": round(print_cost, 2),
        "setup_cost": round(setup_cost, 2),
        "total_cost": round(total_cost, 2),
        "suggested_price": round(suggested_price, 2),
        "unit_price": round(suggested_price / qty, 2) if qty else 0,
    }


# ----- Cotizador Twist Print (Mathipe Quote + 3 lógicas) -----

def _quote_product_type(item_code):
    """Obtiene product_type para un Item: custom field mathipe_product_type o 'Fixed'."""
    if not item_code or not frappe.db.exists("Item", item_code):
        return "Fixed"
    if frappe.db.has_column("Item", "mathipe_product_type"):
        t = frappe.db.get_value("Item", item_code, "mathipe_product_type")
        if t and t.strip() in ("Fixed", "Area", "Recipe"):
            return t.strip()
    return "Fixed"


@frappe.whitelist()
def get_quote_products_catalog():
    """Lista productos para cotizar: Item (is_sales_item) con tipo Fixed/Area/Recipe y opcional recipe."""
    if not frappe.db.table_exists("Item"):
        return []
    try:
        items = frappe.get_all(
            "Item",
            filters={"is_sales_item": 1, "disabled": 0},
            fields=["name", "item_name", "description", "stock_uom"],
            order_by="item_name",
            limit=200,
        )
    except Exception:
        return []
    out = []
    for r in (items or []):
        item_code = r.get("name")
        product_type = _quote_product_type(item_code)
        recipe_name = None
        if product_type == "Recipe" and frappe.db.table_exists("Mathipe Product Recipe"):
            recipe_name = frappe.db.get_value("Mathipe Product Recipe", {"product_link": item_code}, "name")
        out.append({
            "item_code": item_code,
            "item_name": (r.get("item_name") or item_code or "").strip(),
            "product_type": product_type,
            "description": (r.get("description") or "")[:200],
            "uom": r.get("stock_uom") or "Unit",
            "recipe_name": recipe_name,
        })
    return out


def _recipe_cost_breakdown(item_code, qty, width_mm, height_mm, margin_pct=None):
    """Calcula costo total y líneas a partir de Mathipe Product Recipe. width/height en mm."""
    if not frappe.db.table_exists("Mathipe Product Recipe") or not frappe.db.table_exists("Mathipe Recipe Component"):
        return {"cost_lines": [], "cost_total": 0, "sale_total": 0, "margin_pct": margin_pct or 0}
    recipe = frappe.db.get_value("Mathipe Product Recipe", {"product_link": item_code}, "name")
    if not recipe:
        return {"cost_lines": [], "cost_total": 0, "sale_total": 0, "margin_pct": margin_pct or 0}
    default_margin = frappe.db.get_value("Mathipe Product Recipe", recipe, "default_margin_pct") or 0
    if margin_pct is None:
        margin_pct = float(default_margin)
    area_m2 = (float(width_mm or 0) / 1000.0) * (float(height_mm or 0) / 1000.0) * float(qty or 0)
    components = frappe.get_all(
        "Mathipe Recipe Component",
        filters={"recipe_link": recipe},
        fields=["component_type", "item_code_or_material", "costing_mode", "qty_per_unit", "qty_per_m2", "hours", "sheet_size_w", "sheet_size_h", "waste_pct", "unit_cost_override"],
    )
    cost_lines = []
    cost_total = 0.0
    for c in (components or []):
        mode = (c.get("costing_mode") or "").strip()
        unit_cost = float(c.get("unit_cost_override") or 0)
        if not unit_cost and c.get("item_code_or_material"):
            unit_cost = float(frappe.db.get_value("Item", c.get("item_code_or_material"), "standard_rate") or 0)
        line_cost = 0.0
        desc = ""
        if mode == "PerUnit":
            qpu = float(c.get("qty_per_unit") or 0)
            line_cost = qty * qpu * unit_cost
            desc = f"Por unidad: {qty} x {qpu} x {unit_cost}"
        elif mode == "PerM2":
            qpm = float(c.get("qty_per_m2") or 0)
            line_cost = area_m2 * qpm * unit_cost
            desc = f"Por m²: {area_m2:.4f} x {qpm} x {unit_cost}"
        elif mode == "PerSheet":
            sw = float(c.get("sheet_size_w") or 0) / 1000.0
            sh = float(c.get("sheet_size_h") or 0) / 1000.0
            if sw > 0 and sh > 0:
                sheet_area = sw * sh
                unit_area = (float(width_mm or 0) / 1000.0) * (float(height_mm or 0) / 1000.0)
                if unit_area <= 0:
                    unit_area = sheet_area
                raw_waste = max(0.0, min(100.0, float(c.get("waste_pct") or 0)))
                waste = 1 + raw_waste / 100.0
                sheets = max(1, int((qty * unit_area / sheet_area) * waste) + 1)
                line_cost = sheets * unit_cost
                desc = f"Planchas: {sheets} x {unit_cost}"
        elif mode == "PerHour":
            h = float(c.get("hours") or 0)
            line_cost = h * unit_cost
            desc = f"Horas: {h} x {unit_cost}"
        elif mode == "PerJob":
            line_cost = unit_cost
            desc = f"Por trabajo: {unit_cost}"
        if line_cost > 0 or unit_cost > 0:
            cost_lines.append({"description": desc or mode, "amount": round(line_cost, 2)})
            cost_total += line_cost
    sale_total = cost_total * (1 + float(margin_pct) / 100.0) if cost_total > 0 else 0
    return {
        "cost_lines": cost_lines,
        "cost_total": round(cost_total, 2),
        "sale_total": round(sale_total, 2),
        "margin_pct": round(margin_pct, 2),
        "computed_fields": {"area_m2": round(area_m2, 4), "qty": qty, "width_mm": width_mm, "height_mm": height_mm},
    }


def _calculate_quote_item_internal(payload):
    """Versión interna: payload ya es dict. Devuelve cost_lines, cost_total, sale_total, margin_pct, area_total, computed_fields."""
    p = payload or {}
    product_type = (p.get("product_type") or "Fixed").strip()
    product = (p.get("product") or p.get("item_code") or "").strip()
    qty = float(p.get("qty") or 0)
    width = float(p.get("width") or 0)
    height = float(p.get("height") or 0)
    if qty <= 0:
        return {"cost_lines": [], "cost_total": 0, "sale_total": 0, "margin_pct": 0, "area_total": 0, "computed_fields": {}}

    if product_type == "Fixed":
        unit_price = float(p.get("unit_price") or 0)
        sale_total = qty * unit_price
        return {
            "cost_lines": [{"description": "Precio fijo por unidad", "amount": round(sale_total, 2)}],
            "cost_total": 0,
            "sale_total": round(sale_total, 2),
            "margin_pct": 0,
            "area_total": 0,
            "computed_fields": {"qty": qty, "unit_price": unit_price},
        }
    if product_type == "Area":
        area_total = (width / 1000.0) * (height / 1000.0) * qty
        price_per_m2 = float(p.get("price_per_m2") or p.get("unit_price") or 0)
        sale_total = area_total * price_per_m2
        return {
            "cost_lines": [{"description": f"m² x precio/m²: {area_total:.4f} x {price_per_m2}", "amount": round(sale_total, 2)}],
            "cost_total": 0,
            "sale_total": round(sale_total, 2),
            "margin_pct": 0,
            "area_total": round(area_total, 4),
            "computed_fields": {"qty": qty, "width_mm": width, "height_mm": height, "price_per_m2": price_per_m2},
        }
    # Recipe
    margin_pct = p.get("margin_pct")
    if margin_pct is not None:
        margin_pct = float(margin_pct)
    out = _recipe_cost_breakdown(product, qty, width, height, margin_pct)
    out["area_total"] = out.get("computed_fields", {}).get("area_m2", 0)
    return out


@frappe.whitelist()
def calculate_quote_item(payload=None, **kwargs):
    """Calcula un ítem de cotización. payload: product_type, product (item_code), qty, width?, height?, unit_price?, price_per_m2?, margin_pct?.
    Acepta payload como dict o los campos como kwargs (p. ej. desde el frontend que envía { product_type, product, qty, ... })."""
    if payload is None and kwargs:
        payload = kwargs
    if isinstance(payload, str):
        import json
        payload = json.loads(payload) if payload else {}
    if not isinstance(payload, dict):
        payload = {}
    return _calculate_quote_item_internal(payload)


# ── Fase 11B: Cálculo desde Mathipe Product Template ─────────────────────────

BREAKDOWN_VERSION = 1


def _calc_template_breakdown(template_doc, qty, width, height, margin_pct_override=None):
    """Fuente única de verdad: calcula costo y venta desde Product Template.
    width/height en mm (como en Quote Item). Retorna cost_lines, cost_total, sale_total, margin_pct, area_total, breakdown_json."""
    import json as _json
    qty = float(qty or 0)
    width = float(width or 0)
    height = float(height or 0)
    if qty <= 0:
        return {
            "cost_lines": [], "cost_total": 0, "sale_total": 0, "margin_pct": 0,
            "area_total": 0, "breakdown_json": "", "breakdown_version": BREAKDOWN_VERSION,
            "unit_price": 0, "estimated_cost_total": 0,
        }
    # area_m2 total: (mm->m) (width/1000)*(height/1000)*qty
    area_m2 = (width / 1000.0) * (height / 1000.0) * qty
    area_m2 = round(area_m2, 6)
    costing_mode = (template_doc.get("costing_mode") or "Manual").strip()
    margin_pct = float(margin_pct_override if margin_pct_override is not None else template_doc.get("default_margin_pct") or 30)
    cost_lines = []
    cost_total = 0.0

    # Manual: solo base manual
    if costing_mode == "Manual":
        cost_total = float(template_doc.get("manual_base_cost") or 0) * qty
        cost_lines.append({
            "label": "Costo base manual",
            "type": "Manual",
            "qty": qty,
            "unit_cost": float(template_doc.get("manual_base_cost") or 0),
            "line_total": round(cost_total, 2),
        })
        sale_total = float(template_doc.get("manual_base_price") or 0) * qty
        if margin_pct and cost_total > 0:
            sale_total = round(cost_total * (1 + margin_pct / 100.0), 2)
        else:
            sale_total = round(sale_total, 2)
        unit_price = sale_total / qty if qty else 0
        out = {
            "cost_lines": cost_lines,
            "cost_total": round(cost_total, 2),
            "sale_total": sale_total,
            "margin_pct": round(margin_pct, 2),
            "area_total": area_m2,
            "unit_price": round(unit_price, 2),
            "estimated_cost_total": round(cost_total, 2),
        }
        out["breakdown_json"] = _json.dumps({
            "cost_lines": cost_lines,
            "inputs": {"qty": qty, "width": width, "height": height, "margin_pct": margin_pct},
            "template_id": template_doc.get("name"),
            "version": BREAKDOWN_VERSION,
        }, ensure_ascii=False)
        out["breakdown_version"] = BREAKDOWN_VERSION
        return out

    # Automatic / Hybrid: recorrer components
    if costing_mode == "Hybrid":
        cost_total = float(template_doc.get("manual_base_cost") or 0) * qty
        cost_lines.append({
            "label": "Base manual",
            "type": "Fixed",
            "qty": qty,
            "unit_cost": float(template_doc.get("manual_base_cost") or 0),
            "line_total": round(cost_total, 2),
        })

    components = getattr(template_doc, "components", None) or []
    for comp in components:
        ctype = (comp.get("component_type") or "").strip()
        qty_mode = (comp.get("qty_mode") or "PerJob").strip()
        qty_val = float(comp.get("qty_value") or 0)
        waste = float(comp.get("waste_pct") or 0) / 100.0
        if qty_mode == "PerJob":
            qty_calc = 1.0
        elif qty_mode == "PerUnit":
            qty_calc = qty
        elif qty_mode == "PerM2":
            qty_calc = area_m2
        else:
            qty_calc = qty  # PerSheet tratado como qty
        qty_calc = qty_calc * (1.0 + waste)
        line_total = 0.0
        label = ""
        unit_cost = 0.0
        if ctype == "Material" and comp.get("ref_material"):
            mat = frappe.db.get_value(
                "Mathipe Material", comp.get("ref_material"),
                ["cost_per_unit", "material_name"], as_dict=True
            )
            if mat:
                unit_cost = float(mat.get("cost_per_unit") or 0)
                line_total = unit_cost * qty_calc
                label = (mat.get("material_name") or comp.get("ref_material"))[:80]
        elif ctype == "Operation" and comp.get("ref_operation"):
            op = frappe.get_doc("Mathipe Operation", comp.get("ref_operation"))
            omode = (op.get("costing_mode") or "Fixed").strip()
            if omode == "Fixed":
                line_total = float(op.get("cost_fixed") or 0)
                unit_cost = line_total
                qty_calc = 1
            elif omode == "PerUnit":
                unit_cost = float(op.get("cost_per_unit") or 0)
                line_total = unit_cost * qty_calc
            elif omode == "AreaBased":
                unit_cost = float(op.get("cost_per_unit") or 0)
                line_total = unit_cost * area_m2
                qty_calc = area_m2
            else:
                minutes = float(op.get("time_minutes_per_unit") or 0) * qty_calc
                machine_name = op.get("default_machine")
                rate = 0.0
                if machine_name:
                    rate = float(frappe.db.get_value("Mathipe Machine", machine_name, "cost_per_hour") or 0)
                line_total = (minutes / 60.0) * rate
                unit_cost = (minutes / 60.0) * rate / qty_calc if qty_calc else 0
            label = (op.get("operation_name") or comp.get("ref_operation"))[:80]
        elif ctype == "MachineTime" and comp.get("ref_machine"):
            machine_name = comp.get("ref_machine")
            cost_per_hour = float(frappe.db.get_value("Mathipe Machine", machine_name, "cost_per_hour") or 0)
            minutes = qty_val * qty_calc
            line_total = (minutes / 60.0) * cost_per_hour
            unit_cost = cost_per_hour / 60.0 * qty_val if qty_val else 0
            label = (frappe.db.get_value("Mathipe Machine", machine_name, "machine_name") or machine_name)[:80]
        elif ctype == "Fixed":
            line_total = float(qty_val or 0)
            unit_cost = line_total
            qty_calc = 1
            label = comp.get("notes") or "Costo fijo"
        if label and line_total is not None:
            cost_lines.append({
                "label": label,
                "type": ctype or "Fixed",
                "qty": round(qty_calc, 4),
                "unit_cost": round(unit_cost, 4),
                "line_total": round(line_total, 2),
            })
            cost_total += line_total

    sale_total = cost_total * (1 + margin_pct / 100.0) if cost_total else 0
    sale_total = round(sale_total, 2)
    cost_total = round(cost_total, 2)
    unit_price = sale_total / qty if qty else 0
    out = {
        "cost_lines": cost_lines,
        "cost_total": cost_total,
        "sale_total": sale_total,
        "margin_pct": round(margin_pct, 2),
        "area_total": area_m2,
        "unit_price": round(unit_price, 2),
        "estimated_cost_total": cost_total,
    }
    out["breakdown_json"] = _json.dumps({
        "cost_lines": cost_lines,
        "inputs": {"qty": qty, "width": width, "height": height, "margin_pct": margin_pct},
        "template_id": template_doc.get("name"),
        "version": BREAKDOWN_VERSION,
    }, ensure_ascii=False)
    out["breakdown_version"] = BREAKDOWN_VERSION
    return out


@frappe.whitelist()
def calculate_quote_item_from_template(payload):
    """Calcula ítem desde Mathipe Product Template. payload: product_template, qty, width?, height?, margin_pct?.
    Retorna unit_price, sale_total, estimated_cost_total, cost_lines, breakdown_json, breakdown_version."""
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("product_template") or "").strip()
    if not name:
        frappe.throw("product_template es requerido")
    if not frappe.db.exists("Mathipe Product Template", name):
        frappe.throw("Plantilla de producto no encontrada")
    template_doc = frappe.get_doc("Mathipe Product Template", name)
    qty = float(payload.get("qty") or 0)
    width = float(payload.get("width") or 0)
    height = float(payload.get("height") or 0)
    margin_pct = payload.get("margin_pct")
    if margin_pct is not None:
        margin_pct = float(margin_pct)
    return _calc_template_breakdown(template_doc, qty, width, height, margin_pct)


@frappe.whitelist()
def create_quote(customer, delivery_date, items, notes=None):
    """Crea Mathipe Quote con ítems. items = lista de { product_type, product, qty, width?, height?, unit_price?, price_per_m2?, margin_pct?, description? }."""
    if not frappe.has_permission("Mathipe Quote", "create"):
        frappe.throw("Sin permiso para crear cotización")
    customer = (customer or "").strip()
    if not customer:
        frappe.throw("Cliente es requerido")
    delivery_date = (delivery_date or "").strip()
    if not delivery_date:
        frappe.throw("Fecha de entrega es requerida")
    if not frappe.db.exists("Customer", customer):
        frappe.throw("Cliente no encontrado")
    items = items if isinstance(items, (list, tuple)) else frappe.parse_json(items)
    if not items or not isinstance(items, (list, tuple)):
        frappe.throw("Debe haber al menos un ítem")

    if not frappe.db.table_exists("Mathipe Quote"):
        frappe.throw("El DocType Mathipe Quote no existe. Ejecute: bench --site [site] migrate")

    import json as _json

    currency = frappe.db.get_value("Company", frappe.defaults.get_default_company(), "default_currency") or "ARS"
    doc = frappe.get_doc({
        "doctype": "Mathipe Quote",
        "customer": customer,
        "delivery_date": delivery_date,
        "status": "Draft",
        "notes": (notes or "")[:5000],
        "currency": currency,
    })
    for idx, row in enumerate(items, start=1):
        product_template = (row.get("product_template") or "").strip()
        if product_template:
            if not frappe.db.exists("Mathipe Product Template", product_template):
                frappe.throw(f"Ítem {idx}: plantilla de producto '{product_template}' no encontrada")
            template_doc = frappe.get_doc("Mathipe Product Template", product_template)
            route_template = (template_doc.get("default_route_template") or "").strip() or None
            template_costing_mode = (template_doc.get("costing_mode") or "")[:64]
            qty = float(row.get("qty") or 0)
            if qty <= 0:
                frappe.throw(f"Ítem {idx}: la cantidad debe ser mayor a 0")
            width = float(row.get("width") or 0)
            height = float(row.get("height") or 0)
            breakdown_json_str = (row.get("breakdown_json") or "").strip()
            sale_total = float(row.get("sale_total") or 0)
            cost_total = float(row.get("cost_total") or 0)
            unit_price = float(row.get("unit_price") or 0)
            area_total = float(row.get("area_total") or 0)
            margin_pct = float(row.get("margin_pct") or 0)
            if not breakdown_json_str and product_template:
                calc = _calc_template_breakdown(
                    template_doc, qty, width, height,
                    float(row.get("margin_pct")) if row.get("margin_pct") is not None else None,
                )
                sale_total = calc.get("sale_total") or 0
                cost_total = calc.get("cost_total") or 0
                unit_price = calc.get("unit_price") or 0
                area_total = calc.get("area_total") or 0
                margin_pct = calc.get("margin_pct") or 0
                breakdown_json_str = calc.get("breakdown_json") or _json.dumps(calc.get("cost_lines") or [], ensure_ascii=False)
            item_row = {
                "product_type": "Fixed",
                "product": None,
                "qty": qty,
                "width": width or None,
                "height": height or None,
                "unit_price": unit_price,
                "area_total": area_total,
                "sale_total": sale_total,
                "cost_total": cost_total,
                "margin_pct": margin_pct,
                "description": (row.get("description") or template_doc.get("product_name") or "")[:500],
                "breakdown_json": breakdown_json_str[:50000] if breakdown_json_str else "",
            }
            if frappe.db.column_exists("Mathipe Quote Item", "breakdown_version"):
                item_row["breakdown_version"] = BREAKDOWN_VERSION
            if frappe.db.column_exists("Mathipe Quote Item", "product_template"):
                item_row["product_template"] = product_template
            if frappe.db.column_exists("Mathipe Quote Item", "template_costing_mode"):
                item_row["template_costing_mode"] = template_costing_mode
            if frappe.db.column_exists("Mathipe Quote Item", "margin_pct_override"):
                item_row["margin_pct_override"] = row.get("margin_pct_override")
            if frappe.db.column_exists("Mathipe Quote Item", "route_template"):
                item_row["route_template"] = route_template
            doc.append("items", item_row)
            continue
        product_type = (row.get("product_type") or "Fixed").strip()
        product = (row.get("product") or row.get("item_code") or "").strip()
        qty = float(row.get("qty") or 0)
        if qty <= 0:
            frappe.throw(f"Ítem {idx}: la cantidad debe ser mayor a 0")
        width = float(row.get("width") or 0)
        height = float(row.get("height") or 0)
        if product_type == "Area" and (width <= 0 or height <= 0):
            frappe.throw(f"Ítem {idx} (Area): ancho y alto deben ser mayores a 0")
        if product_type == "Recipe" and product and frappe.db.table_exists("Mathipe Product Recipe"):
            recipe_name = frappe.db.get_value("Mathipe Product Recipe", {"product_link": product}, "name")
            if recipe_name and frappe.db.get_value("Mathipe Product Recipe", recipe_name, "allow_dimensions"):
                if width <= 0 or height <= 0:
                    frappe.throw(f"Ítem {idx} (Recipe): este producto requiere ancho y alto mayores a 0")
        unit_price = float(row.get("unit_price") or 0)
        price_per_m2 = float(row.get("price_per_m2") or 0)
        margin_pct = float(row.get("margin_pct") or 0)
        payload = {"product_type": product_type, "product": product, "qty": qty, "width": width, "height": height, "unit_price": unit_price, "price_per_m2": price_per_m2, "margin_pct": margin_pct}
        calc = _calculate_quote_item_internal(payload)
        item_row = {
            "product_type": product_type,
            "product": product or None,
            "qty": qty,
            "width": width or None,
            "height": height or None,
            "unit_price": unit_price or (calc.get("sale_total", 0) / qty if qty else 0),
            "area_total": calc.get("area_total") or 0,
            "sale_total": calc.get("sale_total") or 0,
            "cost_total": calc.get("cost_total") or 0,
            "margin_pct": calc.get("margin_pct") or 0,
            "description": (row.get("description") or "")[:500],
            "breakdown_json": _json.dumps(calc.get("cost_lines") or [], ensure_ascii=False),
        }
        if frappe.db.column_exists("Mathipe Quote Item", "breakdown_version"):
            item_row["breakdown_version"] = 1
        doc.append("items", item_row)
    if not doc.items:
        frappe.throw("Ningún ítem válido (cantidad > 0)")
    doc.insert()
    frappe.db.commit()
    return {"name": doc.name, "message": "Cotización creada"}


@frappe.whitelist()
def get_quote(quote_id):
    """Retorna el detalle de una cotización con ítems y breakdown persistido."""
    import json as _json
    quote_id = (quote_id or "").strip()
    if not frappe.db.exists("Mathipe Quote", quote_id):
        frappe.throw("Cotización no encontrada")
    if not frappe.has_permission("Mathipe Quote", "read"):
        frappe.throw("Sin permiso de lectura en Mathipe Quote")
    doc = frappe.get_doc("Mathipe Quote", quote_id)
    items = []
    for row in (doc.items or []):
        breakdown = []
        try:
            raw = getattr(row, "breakdown_json", None) or ""
            if raw:
                breakdown = _json.loads(raw)
        except Exception:
            breakdown = []
        item_out = {
            "name": row.name,
            "product_type": row.product_type or "Fixed",
            "product": row.product or "",
            "description": row.description or "",
            "qty": float(row.qty or 0),
            "width": float(row.width or 0),
            "height": float(row.height or 0),
            "unit_price": float(row.unit_price or 0),
            "area_total": float(row.area_total or 0),
            "sale_total": float(row.sale_total or 0),
            "cost_total": float(row.cost_total or 0),
            "margin_pct": float(row.margin_pct or 0),
            "is_outsourcing": bool(row.is_outsourcing),
            "vendor": row.vendor or "",
            "cost_lines": breakdown,
        }
        if hasattr(row, "breakdown_version") and row.breakdown_version is not None:
            item_out["breakdown_version"] = int(row.breakdown_version)
        if hasattr(row, "product_template") and row.product_template:
            item_out["product_template"] = row.product_template
        if hasattr(row, "template_costing_mode") and row.template_costing_mode:
            item_out["template_costing_mode"] = row.template_costing_mode
        if hasattr(row, "margin_pct_override") and row.margin_pct_override is not None:
            item_out["margin_pct_override"] = float(row.margin_pct_override)
        if hasattr(row, "route_template") and row.route_template:
            item_out["route_template"] = row.route_template
        items.append(item_out)
    out = {
        "name": doc.name,
        "customer": doc.customer,
        "delivery_date": str(doc.delivery_date) if doc.delivery_date else None,
        "status": doc.status,
        "notes": doc.notes or "",
        "currency": doc.currency or "ARS",
        "cost_total": float(doc.cost_total or 0),
        "sale_total": float(doc.sale_total or 0),
        "margin_pct": float(doc.margin_pct or 0),
        "items": items,
    }
    if hasattr(doc, "sales_order") and doc.sales_order:
        out["sales_order"] = doc.sales_order
    return out


def _get_so_by_mathipe_quote(quote_id):
    """Busca Sales Order por link mathipe_quote si existe el campo; si no, por remarks."""
    if frappe.db.column_exists("Sales Order", "mathipe_quote"):
        so_name = frappe.db.get_value("Sales Order", {"mathipe_quote": quote_id}, "name")
        if so_name:
            return so_name
    existing = frappe.db.sql(
        "SELECT name FROM `tabSales Order` WHERE remarks LIKE %(pattern)s LIMIT 1",
        {"pattern": f"%[Cotización: {quote_id}]%"},
        as_dict=True,
    )
    return existing[0].name if existing else None


def _quote_row_to_wo_item(row):
    """Construye dict para un WO Item desde un Quote Item (nuevo ítem). Incluye quote_item y campos sync; defaults operativos."""
    qty = float(row.get("qty") or 0)
    is_out = bool(row.get("is_outsourcing"))
    return {
        "quote_item": (row.get("name") or "").strip() or None,
        "item_code": (row.get("product") or "").strip() or None,
        "description": ((row.get("description") or "").strip() or (row.get("product") or "Ítem"))[:2000],
        "product_type": (row.get("product_type") or "").strip() or None,
        "qty": qty,
        "width": float(row.get("width") or 0) or None,
        "height": float(row.get("height") or 0) or None,
        "area_total": float(row.get("area_total") or 0) or None,
        "cost_total": float(row.get("cost_total") or 0) or None,
        "sale_total": float(row.get("sale_total") or 0) or None,
        "uom": "Unit",
        "source": "Quote",
        "breakdown_version": int(row.get("breakdown_version") or 0) or None,
        "breakdown_json": (row.get("breakdown_json") or "").strip()[:20000] or None,
        "is_outsourced": 1 if is_out else 0,
        "supplier": (row.get("vendor") or "").strip() or None,
        "outsource_status": "PendingVendor" if is_out else "",
    }


def _sync_wo_items_from_quote(wo_name, quote_id):
    """Sincroniza WO Items desde Quote: 1:1 por quote_item. Actualiza solo campos sync; no pisa is_outsourced, supplier, outsource_*."""
    if not wo_name or not quote_id:
        return
    if not frappe.db.exists("Mathipe Work Order", wo_name) or not frappe.db.exists("Mathipe Quote", quote_id):
        return
    quote = frappe.get_doc("Mathipe Quote", quote_id)
    doc = frappe.get_doc("Mathipe Work Order", wo_name)
    if not getattr(doc, "items", None) or not quote.items:
        return
    # Mapa WO item por quote_item (clave única)
    wo_by_quote = {}
    for r in doc.items:
        qi = (r.get("quote_item") or "").strip()
        if qi:
            wo_by_quote[qi] = r
    # Por cada Quote Item: actualizar existente o agregar nuevo
    for row in quote.items:
        qi = (row.get("name") or "").strip()
        if not qi:
            continue
        if qi in wo_by_quote:
            wi = wo_by_quote[qi]
            # Solo campos sync (no operativos)
            wi.set("description", ((row.get("description") or "").strip() or (row.get("product") or "Ítem"))[:2000])
            wi.set("product_type", (row.get("product_type") or "").strip() or None)
            wi.set("qty", float(row.get("qty") or 0))
            wi.set("width", float(row.get("width") or 0) or None)
            wi.set("height", float(row.get("height") or 0) or None)
            wi.set("area_total", float(row.get("area_total") or 0) or None)
            wi.set("cost_total", float(row.get("cost_total") or 0) or None)
            wi.set("sale_total", float(row.get("sale_total") or 0) or None)
            wi.set("item_code", (row.get("product") or "").strip() or None)
            wi.set("breakdown_version", int(row.get("breakdown_version") or 0) or None)
            wi.set("breakdown_json", (row.get("breakdown_json") or "").strip()[:20000] or None)
        else:
            doc.append("items", _quote_row_to_wo_item(row))
    doc.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def convert_quote_to_sales_order(quote_id):
    """Convierte Mathipe Quote en Sales Order draft + Work Order. Idempotente: si ya fue convertida, retorna referencias existentes."""
    quote_id = (quote_id or "").strip()
    if not quote_id:
        frappe.throw("quote_id es requerido")
    if not frappe.db.exists("Mathipe Quote", quote_id):
        frappe.throw("Cotización no encontrada")

    if not frappe.has_permission("Mathipe Quote", "read"):
        frappe.throw("Sin permiso de lectura en Mathipe Quote")
    quote = frappe.get_doc("Mathipe Quote", quote_id)

    # Idempotencia: buscar SO por link estable (mathipe_quote) o por remarks
    so_name = _get_so_by_mathipe_quote(quote_id)
    if so_name:
        wo_name = frappe.db.get_value("Mathipe Work Order", {"sales_order": so_name}, "name")
        if wo_name:
            _sync_wo_items_from_quote(wo_name, quote_id)
        return {
            "name": so_name,
            "work_order": wo_name,
            "message": "Cotización ya convertida",
            "already_converted": True,
        }

    # Solo Draft o Accepted pueden convertirse; Rejected no
    if quote.status == "Rejected":
        frappe.throw("No se puede convertir una cotización rechazada")
    if quote.status not in ("Draft", "Accepted"):
        frappe.throw(f"Estado '{quote.status}' no permite conversión. Use Draft o Accepted.")

    if not frappe.has_permission("Sales Order", "create"):
        frappe.throw("Sin permiso para crear Sales Order")
    if not frappe.has_permission("Mathipe Quote", "write"):
        frappe.throw("Sin permiso para actualizar la cotización")

    customer = quote.customer
    delivery_date = quote.delivery_date
    if not customer:
        frappe.throw("La cotización no tiene cliente")
    customer_id = _resolve_customer(customer)
    if not customer_id:
        frappe.throw("Cliente no encontrado")

    so = frappe.new_doc("Sales Order")
    so.customer = customer_id
    so.delivery_date = delivery_date
    so.remarks = (so.remarks or "") + f" [Cotización: {quote_id}]"
    if frappe.db.column_exists("Sales Order", "mathipe_quote"):
        so.mathipe_quote = quote_id
    for row in quote.items:
        qty = float(row.get("qty") or 0)
        if qty <= 0:
            frappe.throw("Todos los ítems deben tener cantidad mayor a 0")
        item_code = row.get("product") or "COTIZACION-IMPRESION"
        if not frappe.db.exists("Item", item_code):
            item_code = "COTIZACION-IMPRESION"
        rate = float(row.get("sale_total") or 0)
        if rate <= 0:
            rate = float(row.get("unit_price") or 0)
        desc_parts = [row.get("description") or ""]
        if row.get("product_type") == "Area" and (row.get("width") or row.get("height")):
            desc_parts.append(f"{row.get('width')}x{row.get('height')} mm, {row.get('area_total') or 0:.2f} m²")
        if row.get("product_type") == "Recipe":
            desc_parts.append("(Receta)")
        description = " | ".join(filter(None, desc_parts))[:500] or f"Qty: {qty}"
        so.append("items", {"item_code": item_code, "qty": qty, "rate": rate, "description": description})
    if not so.items:
        frappe.throw("La cotización no tiene ítems válidos")
    so.insert()
    frappe.db.commit()
    quote.status = "Converted"
    if frappe.db.column_exists("Mathipe Quote", "sales_order"):
        quote.sales_order = so.name
    quote.flags.ignore_validate_update_after_submit = True
    quote.save()
    frappe.db.commit()

    # Crear Work Order vinculada (con dedup por sales_order)
    wo_name = None
    try:
        existing_wo = frappe.db.get_value("Mathipe Work Order", {"sales_order": so.name}, "name")
        if existing_wo:
            wo_name = existing_wo
        else:
            wo = frappe.new_doc("Mathipe Work Order")
            wo.sales_order = so.name
            wo.customer = so.customer
            wo.customer_name = frappe.db.get_value("Customer", so.customer, "customer_name") or so.customer
            wo.delivery_date = so.delivery_date
            wo.status = "New"
            # Poblar ítems desde Quote 1:1 con quote_item (fuente de verdad)
            if getattr(wo, "items", None) is not None and quote.items:
                for row in quote.items:
                    wo.append("items", _quote_row_to_wo_item(row))
            if frappe.has_permission("Mathipe Work Order", "create"):
                wo.insert()
            else:
                wo.insert(ignore_permissions=True)
            frappe.db.commit()
            wo_name = wo.name
            route_template = None
            if frappe.db.column_exists("Mathipe Quote Item", "route_template"):
                for row in quote.items:
                    rt = (getattr(row, "route_template", None) or "").strip()
                    if rt and frappe.db.exists("Mathipe Route Template", rt):
                        route_template = rt
                        break
            if wo_name and route_template:
                try:
                    init_wo_stages_from_template(wo_name, template_key=route_template)
                except Exception as _e2:
                    frappe.log_error(message=str(_e2), title="convert_quote_to_sales_order: init_wo_stages")
    except Exception as _e:
        frappe.log_error(message=str(_e), title="convert_quote_to_sales_order: error creando WO")

    return {"name": so.name, "work_order": wo_name, "message": "Orden creada"}


@frappe.whitelist()
def search_customers(txt):
    """Busca clientes por nombre o ID (contiene el texto, no solo prefijo)."""
    txt = (txt or "").strip()[:80]
    if not txt or len(txt) < 2:
        return []
    # Contiene: LIKE '%txt%' para que "palabra" encuentre "Razón palabra algo"
    like_contains = "%" + _escape_like(txt) + "%"
    try:
        rows = frappe.db.sql("""
            SELECT name, customer_name
            FROM `tabCustomer`
            WHERE disabled = 0
              AND (name LIKE %(term)s OR customer_name LIKE %(term)s)
            ORDER BY customer_name
            LIMIT 20
        """, {"term": like_contains}, as_dict=True)
        return [{"name": r.name, "customer_name": r.get("customer_name") or r.name} for r in (rows or [])]
    except Exception:
        return []


@frappe.whitelist()
def get_all_customers(search_term=""):
    """Lista clientes (Customer) para el directorio. Opcional filtro por search_term en name o customer_name."""
    if not frappe.db.table_exists("Customer"):
        return []
    search_term = (search_term or "").strip()
    filters = {}
    or_filters = None
    if search_term:
        term = "%" + _escape_like(search_term) + "%"
        or_filters = [
            ["name", "like", term],
            ["customer_name", "like", term],
        ]
    try:
        rows = frappe.get_all(
            "Customer",
            filters=filters,
            or_filters=or_filters,
            fields=["name", "customer_name", "customer_group", "territory"],
            order_by="modified desc",
            limit=50,
        )
        return [
            {
                "name": r.get("name") or "",
                "customer_name": (r.get("customer_name") or r.get("name") or "").strip(),
                "customer_group": (r.get("customer_group") or "").strip(),
                "territory": (r.get("territory") or "").strip(),
            }
            for r in (rows or [])
        ]
    except Exception:
        return []


# Grupo y territorio únicos para todos los clientes del proyecto (se crean en Desk si no existen)
MATHIPE_CUSTOMER_GROUP = "Clientes"
MATHIPE_TERRITORY = "General"


def _ensure_customer_group_and_territory():
    """Crea el Grupo de Clientes y el Territorio por defecto si no existen (para uso en Desk y en la app)."""
    if not frappe.db.exists("Customer Group", MATHIPE_CUSTOMER_GROUP):
        frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": MATHIPE_CUSTOMER_GROUP,
            "is_group": 1,
            "parent_customer_group": "",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    if not frappe.db.exists("Territory", MATHIPE_TERRITORY):
        frappe.get_doc({
            "doctype": "Territory",
            "territory_name": MATHIPE_TERRITORY,
            "is_group": 1,
            "parent_territory": "",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def _default_customer_group():
    """Grupo de Cliente Prueba, o 'Clientes' (creado si no existe), o el primero disponible en DB."""
    row = frappe.db.get_value(
        "Customer",
        {"customer_name": "Cliente Prueba"},
        ["customer_group", "territory"],
        as_dict=True,
    )
    if row and row.get("customer_group") and frappe.db.exists("Customer Group", row.get("customer_group")):
        return row.get("customer_group")
    if frappe.db.exists("Customer Group", MATHIPE_CUSTOMER_GROUP):
        return MATHIPE_CUSTOMER_GROUP
    _ensure_customer_group_and_territory()
    if frappe.db.exists("Customer Group", MATHIPE_CUSTOMER_GROUP):
        return MATHIPE_CUSTOMER_GROUP
    names = frappe.get_all("Customer Group", fields=["name"], limit=1, order_by="name asc")
    if names:
        return names[0].name
    return None


def _default_territory():
    """Territorio de Cliente Prueba, o 'General' (creado si no existe), o el primero disponible en DB."""
    row = frappe.db.get_value(
        "Customer",
        {"customer_name": "Cliente Prueba"},
        ["customer_group", "territory"],
        as_dict=True,
    )
    if row and row.get("territory") and frappe.db.exists("Territory", row.get("territory")):
        return row.get("territory")
    if frappe.db.exists("Territory", MATHIPE_TERRITORY):
        return MATHIPE_TERRITORY
    _ensure_customer_group_and_territory()
    if frappe.db.exists("Territory", MATHIPE_TERRITORY):
        return MATHIPE_TERRITORY
    names = frappe.get_all("Territory", fields=["name"], limit=1, order_by="name asc")
    if names:
        return names[0].name
    return None


@frappe.whitelist()
def create_simple_customer(customer_name, customer_group="", territory=""):
    """Crea un Customer con datos mínimos. Retorna {ok: True, name} o {ok: False, error}."""
    customer_name = (customer_name or "").strip()
    if not customer_name:
        return {"ok": False, "error": "El nombre del cliente es requerido."}
    customer_group = (customer_group or "").strip() or _default_customer_group()
    territory = (territory or "").strip() or _default_territory()
    if not customer_group or not territory:
        return {
            "ok": False,
            "error": "No hay Grupo de Clientes o Territorio configurado. Ejecute en la consola: mathipe_ui.api.ensure_customer_group_and_territory() o créelos desde Ventas en el Desk.",
        }
    try:
        doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Company",
            "customer_group": customer_group,
            "territory": territory,
        })
        doc.insert()
        frappe.db.commit()
        return {"ok": True, "name": doc.name}
    except Exception as e:
        frappe.db.rollback()
        return {"ok": False, "error": str(e) or "Error al crear el cliente."}


@frappe.whitelist()
def ensure_customer_group_and_territory():
    """Crea en el Desk el Grupo 'Clientes' y el Territorio 'General' si no existen. Útil para centralizar todos los clientes."""
    _ensure_customer_group_and_territory()
    return {"ok": True, "customer_group": MATHIPE_CUSTOMER_GROUP, "territory": MATHIPE_TERRITORY}


@frappe.whitelist()
def get_sale_items(txt):
    """Busca ítems de venta por prefijo (usa índice, evita timeout)."""
    txt = (txt or "").strip()[:80]
    if not txt:
        return []
    like_prefix = _escape_like(txt) + "%"
    try:
        rows = frappe.db.sql("""
            SELECT item_code, item_name, stock_uom, standard_rate
            FROM `tabItem`
            WHERE is_sales_item = 1 AND disabled = 0
              AND (item_code LIKE %(prefix)s OR item_name LIKE %(prefix)s)
            ORDER BY item_name
            LIMIT 20
        """, {"prefix": like_prefix}, as_dict=True)
        out = []
        for r in rows or []:
            out.append({
                "item_code": r.get("item_code") or "",
                "item_name": r.get("item_name") or "",
                "stock_uom": r.get("stock_uom") or "",
                "standard_rate": float(r.get("standard_rate") or 0),
            })
        return out
    except Exception:
        return []


def _resolve_customer(customer_id_or_name):
    """Devuelve el ID de cliente si existe (por name o por customer_name exacto). No crea clientes nuevos."""
    customer_id_or_name = (customer_id_or_name or "").strip()[:140]
    if not customer_id_or_name:
        return None
    if frappe.db.exists("Customer", customer_id_or_name):
        return customer_id_or_name
    try:
        found = frappe.get_all(
            "Customer",
            filters={"customer_name": customer_id_or_name, "disabled": 0},
            fields=["name"],
            limit=1,
        )
        if found:
            return found[0].name
    except Exception:
        pass
    return None


@frappe.whitelist()
def create_quick_order(customer, items, delivery_date, remarks=None):
    """Crea una Sales Order en Draft. customer=ID o nombre (debe existir).
    delivery_date=YYYY-MM-DD, items=list of {item_code, qty, rate}. remarks=nota interna."""
    try:
        customer = (customer or "").strip()
        if not customer:
            frappe.throw("El cliente es requerido.")
        items = items if isinstance(items, (list, tuple)) else frappe.parse_json(items)
        if not items or not isinstance(items, (list, tuple)):
            frappe.throw("Debe haber al menos un ítem.")
        delivery_date = (delivery_date or "").strip()
        if not delivery_date:
            frappe.throw("La fecha de entrega es requerida.")
        remarks = (remarks or "").strip()[:5000]

        customer_id = _resolve_customer(customer)
        if not customer_id:
            frappe.throw(
                "Cliente no encontrado. Seleccioná uno de la lista del buscador o creá el cliente desde el escritorio de ERPNext."
            )

        so = frappe.new_doc("Sales Order")
        so.customer = customer_id
        so.delivery_date = delivery_date
        if remarks:
            if hasattr(so, "remarks"):
                so.remarks = remarks
            else:
                try:
                    so.terms = (so.terms or "") + "\n[Nota de taller] " + remarks
                except Exception:
                    pass
        for row in items:
            item_code = (row.get("item_code") or "").strip()
            if not item_code:
                continue
            qty = float(row.get("qty") or 0)
            if qty <= 0:
                continue
            rate = float(row.get("rate") or 0)
            item_row = {"item_code": item_code, "qty": qty, "rate": rate}
            if row.get("description"):
                item_row["description"] = (row.get("description") or "")[:500]
            so.append("items", item_row)
        if not so.items:
            frappe.throw("Debe haber al menos un ítem con cantidad mayor a cero.")
        so.insert()
        frappe.db.commit()
        return {"name": so.name}
    except frappe.ValidationError:
        raise
    except frappe.DoesNotExistError:
        raise
    except Exception as e:
        frappe.log_error(message=str(e), title="create_quick_order error")
        frappe.throw("Error al crear la orden: " + (str(e) or "error desconocido"))


# ----- Panel de Cobros (Cuentas por Cobrar) -----

@frappe.whitelist()
def get_pending_collections():
    """Lista de Sales Order con saldo pendiente (advance_paid < grand_total). Campos: name, customer_name, grand_total, advance_paid, status, pending_amount."""
    if not frappe.db.table_exists("Sales Order"):
        return []
    try:
        orders = frappe.get_all(
            "Sales Order",
            filters={"status": ["not in", ["Cancelled", "Closed"]]},
            fields=["name", "customer_name", "grand_total", "advance_paid", "status", "transaction_date"],
            order_by="transaction_date desc",
            limit=200,
        )
    except Exception:
        return []
    result = []
    for o in orders:
        grand_total = float(o.get("grand_total") or 0)
        advance_paid = float(o.get("advance_paid") or 0)
        if advance_paid >= grand_total:
            continue
        pending_amount = grand_total - advance_paid
        result.append({
            "name": o.get("name"),
            "customer_name": (o.get("customer_name") or "").strip(),
            "grand_total": grand_total,
            "advance_paid": advance_paid,
            "pending_amount": pending_amount,
            "status": (o.get("status") or "").strip(),
        })
    return result


def _resolve_bank_account_for_mode(mode_of_payment, company):
    """Devuelve la cuenta (bank/cash) para cobros. Usa Mode of Payment, luego ERPNext get_default_bank_cash_account, luego cualquier Cash/Bank."""
    if mode_of_payment and frappe.db.exists("Mode of Payment", mode_of_payment):
        account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account",
        )
        if account:
            return account
    for row in frappe.get_all(
        "Mode of Payment Account",
        filters={"company": company},
        fields=["parent", "default_account"],
        limit=10,
    ):
        if row.get("default_account"):
            return row.get("default_account")
    # Usar la misma lógica que el Desk (Journal Entry) para cuenta por defecto
    try:
        from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
        for acc_type in ("Cash", "Bank"):
            details = get_default_bank_cash_account(company, account_type=acc_type)
            if details and details.get("account"):
                return details.get("account")
    except Exception:
        pass
    # Fallback directo: Company defaults
    account = frappe.get_cached_value("Company", company, "default_cash_account")
    if account:
        return account
    account = frappe.get_cached_value("Company", company, "default_bank_account")
    if account:
        return account
    # Cualquier cuenta Cash o Bank de la compañía (por si no hay una sola y el default no está seteado)
    for acc in frappe.get_all(
        "Account",
        filters={"company": company, "account_type": "Cash", "is_group": 0},
        fields=["name"],
        limit=1,
    ):
        if acc.get("name"):
            return acc.get("name")
    for acc in frappe.get_all(
        "Account",
        filters={"company": company, "account_type": "Bank", "is_group": 0},
        fields=["name"],
        limit=1,
    ):
        if acc.get("name"):
            return acc.get("name")
    # Último recurso: ignorar permisos por si el usuario no tiene permiso de lectura en Account
    for acc_type in ("Cash", "Bank"):
        for acc in frappe.get_all(
            "Account",
            filters={"company": company, "account_type": acc_type, "is_group": 0},
            fields=["name"],
            limit=1,
            ignore_permissions=True,
        ):
            if acc.get("name"):
                return acc.get("name")
    return None


@frappe.whitelist()
def register_payment(order_id, paid_amount, mode_of_payment):
    """Crea y envía un Payment Entry contra la Sales Order. paid_amount y mode_of_payment son obligatorios."""
    order_id = (order_id or "").strip()
    if not order_id:
        frappe.throw("order_id es requerido")
    try:
        paid_amount = float(paid_amount or 0)
    except (TypeError, ValueError):
        frappe.throw("paid_amount debe ser un número mayor a cero")
    if paid_amount <= 0:
        frappe.throw("paid_amount debe ser mayor a cero")
    mode_of_payment = (mode_of_payment or "").strip() or "Efectivo"

    try:
        so = frappe.get_doc("Sales Order", order_id)
    except frappe.DoesNotExistError:
        frappe.throw("Orden no encontrada")

    if so.status in ("Cancelled", "Closed"):
        frappe.throw("No se puede cobrar una orden cancelada o cerrada")

    company = so.company
    bank_account = _resolve_bank_account_for_mode(mode_of_payment, company)
    if not bank_account:
        frappe.throw(
            "No hay cuenta de Caja o Banco para cobros. En el Desk: 1) Contabilidad → Plan de cuentas (crear al menos una cuenta tipo Caja o Banco para su compañía). 2) Configuración → Compañía → Cuentas por defecto → asigne Cuenta de caja."
        )

    try:
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    except ImportError:
        frappe.throw("Módulo de cuentas no disponible")

    pe = get_payment_entry("Sales Order", order_id, party_amount=paid_amount, bank_account=bank_account)
    pe.mode_of_payment = mode_of_payment
    if not pe.paid_to or pe.paid_to != bank_account:
        pe.paid_to = bank_account
        acc = frappe.db.get_value(
            "Account", bank_account, ["account_currency", "account_type"], as_dict=True
        )
        if acc:
            pe.paid_to_account_currency = acc.get("account_currency")
            pe.paid_to_account_type = acc.get("account_type")
    pe.flags.ignore_validate_update_after_submit = True
    pe.insert()
    pe.submit()
    frappe.db.commit()
    return {"ok": True, "message": "Pago registrado correctamente.", "payment_entry": pe.name}


# ─────────────────────────────────────────────────────────────────────────────
# MATHIPE WORK ORDER APIs
# ─────────────────────────────────────────────────────────────────────────────
# Work Order: flujo de estados (Fase 2 Sprint A)
WO_STATUS_FLOW = (
    "New",
    "Design",
    "WaitingApproval",
    "Approved",
    "Production",
    "Done",
    "Delivered",
)
WO_STATUS_SPECIAL = ("Cancelled",)  # Solo roles override pueden cancelar (ver OVERRIDE_ROLES)
ALLOW_ONE_STEP_BACK = True  # Retroceso permitido solo a usuarios con OVERRIDE_ROLES
OVERRIDE_ROLES = ("System Manager", "Gerencia")  # Roles que pueden retroceder estado y cancelar


def _user_has_override_role(user=None):
    """True si el usuario tiene alguno de los roles que permiten retroceso y cancelar."""
    if not user:
        user = frappe.session.user
    if not user or user == "Guest":
        return False
    roles = set(frappe.get_roles(user))
    return bool(roles & set(OVERRIDE_ROLES))


# FASE 11A: Mi Empresa — roles que pueden gestionar configuración (máquinas, materiales, etc.)
COMPANY_SETUP_ROLES = OVERRIDE_ROLES + ("Administración",)


def _user_can_manage_company_setup(user=None):
    """True si el usuario puede gestionar Mi Empresa (CRUD máquinas, materiales, operaciones, rutas, productos)."""
    if not user:
        user = frappe.session.user
    if not user or user == "Guest":
        return False
    roles = set(frappe.get_roles(user))
    return bool(roles & set(COMPANY_SETUP_ROLES))


def _require_company_setup():
    """Exige login y rol de administración/gerencia para Mi Empresa."""
    _require_login()
    if not _user_can_manage_company_setup(frappe.session.user):
        frappe.throw("Solo Gerencia, System Manager o Administración pueden gestionar la configuración de Mi Empresa.")


def _wo_is_rollback(from_status, to_status):
    """True si to_status es el estado anterior inmediato a from_status en el grafo."""
    if from_status in WO_STATUS_SPECIAL or to_status in WO_STATUS_SPECIAL:
        return False
    if from_status not in WO_STATUS_FLOW or to_status not in WO_STATUS_FLOW:
        return False
    idx_from = WO_STATUS_FLOW.index(from_status)
    idx_to = WO_STATUS_FLOW.index(to_status)
    return idx_to == idx_from - 1


def _wo_valid_next_statuses(current_status, user=None):
    """Devuelve estados válidos desde current_status para el usuario. Retroceso y Cancelled solo si tiene rol override."""
    if user is None:
        user = frappe.session.user
    has_override = _user_has_override_role(user)
    if current_status in WO_STATUS_SPECIAL:
        return list(WO_STATUS_FLOW) + (list(WO_STATUS_SPECIAL) if has_override else [])
    if current_status not in WO_STATUS_FLOW:
        return list(WO_STATUS_FLOW) + (list(WO_STATUS_SPECIAL) if has_override else [])
    idx = WO_STATUS_FLOW.index(current_status)
    next_list = []
    # Siguiente en el flujo
    if idx + 1 < len(WO_STATUS_FLOW):
        next_list.append(WO_STATUS_FLOW[idx + 1])
    # Un paso atrás solo para roles override
    if ALLOW_ONE_STEP_BACK and idx > 0 and has_override:
        next_list.append(WO_STATUS_FLOW[idx - 1])
    # Cancelled solo para roles override
    if has_override:
        next_list.extend(WO_STATUS_SPECIAL)
    return next_list


def _require_login():
    """Garantiza que la sesión no sea del usuario Guest. Las APIs whitelist permiten llamadas no autenticadas en algunos casos."""
    if frappe.session.user == "Guest":
        frappe.throw("Debe iniciar sesión para realizar esta operación", frappe.AuthenticationError)


# ── FASE 9: Producción por sectores (ruteo) ─────────────────────────────────
DEFAULT_SECTORS_TEMPLATE = [
    {"sector_key": "design", "sector_name": "Diseño", "idx": 1},
    {"sector_key": "printing", "sector_name": "Impresión", "idx": 2},
    {"sector_key": "finishing", "sector_name": "Terminación", "idx": 3},
    {"sector_key": "cutting", "sector_name": "Guillotina", "idx": 4},
    {"sector_key": "billing", "sector_name": "Facturación", "idx": 5},
    {"sector_key": "dispatch", "sector_name": "Despacho/Entrega", "idx": 6},
]
SECTOR_ROLE_PREFIX = "Operaciones - "  # Rol sugerido: "Operaciones - Impresión", etc.


def _wo_current_sector(doc):
    """Sector actual: primer stage Pending o In Progress por idx."""
    stages = getattr(doc, "stages", None) or []
    for s in sorted(stages, key=lambda x: (x.idx or 0)):
        st = (s.stage_status or "").strip()
        if st in ("Pending", "In Progress"):
            return (s.sector_key or "").strip() or None
    return None


def _user_can_operate_sector(user, sector_key):
    """True si el usuario tiene rol del sector o override."""
    if not user or user == "Guest":
        return False
    if _user_has_override_role(user):
        return True
    roles = frappe.get_roles(user)
    # Rol exacto "Operaciones - Impresión" o sector_key -> sector_name mapping
    sector_name = None
    for t in DEFAULT_SECTORS_TEMPLATE:
        if t.get("sector_key") == sector_key:
            sector_name = t.get("sector_name")
            break
    if not sector_name:
        sector_name = (sector_key or "").replace("_", " ").title()
    role_name = SECTOR_ROLE_PREFIX + sector_name
    return role_name in roles


# ── FASE 5: Alertas inteligentes ─────────────────────────────────────────────

_DEFAULT_ALERT_SETTINGS = {
    "alerts_enabled": 1,
    "low_margin_pct_threshold": 15,
    "warning_margin_pct_threshold": 25,
    "waiting_approval_days_threshold": 3,
    "outsource_sent_days_threshold": 5,
    "overdue_delivery_days_threshold": 0,
    "invoice_pending_warning_days": 2,
    "invoice_pending_danger_days": 5,
}


def get_mathipe_settings():
    """Devuelve Mathipe Settings con defaults si no existe o faltan campos (Fase 5: umbrales de alertas)."""
    out = dict(_DEFAULT_ALERT_SETTINGS)
    if not frappe.db.table_exists("Mathipe Settings"):
        return out
    try:
        doc = frappe.get_single("Mathipe Settings")
        for k in out:
            if hasattr(doc, k) and getattr(doc, k) is not None:
                try:
                    if k == "alerts_enabled":
                        out[k] = int(doc.get(k))
                    elif k in ("invoice_pending_warning_days", "invoice_pending_danger_days", "waiting_approval_days_threshold", "outsource_sent_days_threshold", "overdue_delivery_days_threshold"):
                        out[k] = int(doc.get(k))
                    else:
                        out[k] = float(doc.get(k))
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    return out


# ── SAAS: Branding y suscripción por site (multisite = multi-tenant) ─────────

def get_company_profile():
    """Devuelve branding/company profile del site con defaults si no existe el doc o faltan campos."""
    defaults = {
        "company_display_name": "APP Mathipe",
        "company_legal_name": "",
        "logo": None,
        "primary_color": None,
        "support_email": None,
        "timezone": frappe.utils.get_time_zone() if hasattr(frappe.utils, "get_time_zone") else "UTC",
        "currency": "ARS",
    }
    settings = get_mathipe_settings()
    if settings.get("currency"):
        defaults["currency"] = settings["currency"]
    if not frappe.db.table_exists("Mathipe Settings"):
        return defaults
    try:
        doc = frappe.get_single("Mathipe Settings")
        for k in defaults:
            if hasattr(doc, k):
                v = doc.get(k)
                if v is not None and (not isinstance(v, str) or (v and v.strip())):
                    defaults[k] = v
        if not defaults.get("timezone"):
            defaults["timezone"] = frappe.utils.get_time_zone() if hasattr(frappe.utils, "get_time_zone") else "UTC"
    except Exception:
        pass
    return defaults


@frappe.whitelist()
def get_branding():
    """Devuelve branding para la SPA: display_name, logo_url, primary_color, support_email, timezone, currency."""
    profile = get_company_profile()
    logo = profile.get("logo")
    logo_url = None
    if logo:
        try:
            logo_url = frappe.utils.get_url(logo)
        except Exception:
            pass
    return {
        "display_name": (profile.get("company_display_name") or "APP Mathipe").strip(),
        "logo_url": logo_url,
        "primary_color": (profile.get("primary_color") or "").strip() or None,
        "support_email": (profile.get("support_email") or "").strip() or None,
        "timezone": (profile.get("timezone") or "").strip() or None,
        "currency": (profile.get("currency") or "ARS").strip(),
    }


@frappe.whitelist()
def get_subscription_context():
    """Devuelve plan, status, trial_ends_on, enabled_modules (lista) del site. Sin cobros. Para SPA y backend."""
    out = {
        "plan": "Internal",
        "status": "Active",
        "trial_ends_on": None,
        "enabled_modules": [],
    }
    if not frappe.db.table_exists("Mathipe Settings"):
        return out
    try:
        doc = frappe.get_single("Mathipe Settings")
        if hasattr(doc, "subscription_plan") and doc.get("subscription_plan"):
            out["plan"] = (doc.get("subscription_plan") or "Internal").strip()
        if hasattr(doc, "subscription_status") and doc.get("subscription_status"):
            out["status"] = (doc.get("subscription_status") or "Active").strip()
        if hasattr(doc, "trial_ends_on") and doc.get("trial_ends_on"):
            out["trial_ends_on"] = str(doc.get("trial_ends_on"))
        if hasattr(doc, "enabled_modules") and doc.get("enabled_modules"):
            raw = (doc.get("enabled_modules") or "").strip()
            if raw:
                out["enabled_modules"] = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
    except Exception:
        pass
    return out


def feature_enabled(feature_key):
    """
    True si el feature está habilitado para el site.
    - plan Internal -> todo habilitado.
    - status != Active -> bloquear features Pro/Enterprise (finanzas, alertas, analitica, tercerizacion).
    - Si enabled_modules tiene valores, usarlo como override (solo esos módulos).
    """
    ctx = get_subscription_context()
    plan = (ctx.get("plan") or "Internal").strip()
    status = (ctx.get("status") or "Active").strip()
    enabled = ctx.get("enabled_modules") or []

    if plan == "Internal":
        return True
    if status != "Active":
        return False

    # Mapeo feature_key (backend) -> nombre en enabled_modules (puede venir con mayúscula)
    key_to_label = {
        "finanzas": "Finanzas",
        "alertas": "Alertas",
        "analitica": "Analitica",
        "tercerizacion": "Tercerizacion",
    }
    label = key_to_label.get((feature_key or "").strip().lower()) if feature_key else None
    if not label:
        return False
    if enabled:
        return any((m or "").strip().lower() == label.lower() for m in enabled)
    # Sin override: Basic podría tener solo algunos; por ahora sin cobros permitimos según plan name
    return plan in ("Pro", "Enterprise")


@frappe.whitelist()
def get_feature_flags():
    """Para la SPA: dict con finanzas, alertas, analitica, tercerizacion (bool)."""
    return {
        "finanzas": feature_enabled("finanzas"),
        "alertas": feature_enabled("alertas"),
        "analitica": feature_enabled("analitica"),
        "tercerizacion": feature_enabled("tercerizacion"),
    }


def _days_since_waiting_approval(wo_doc):
    """Días desde la última transición a WaitingApproval (status_log). Fallback: modified o creation."""
    if getattr(wo_doc, "status_log", None):
        for r in sorted(wo_doc.status_log, key=lambda x: (x.changed_at or ""), reverse=True):
            if (r.get("to_status") or "").strip() == "WaitingApproval" and r.get("changed_at"):
                try:
                    return (frappe.utils.getdate() - r.changed_at.date()).days
                except Exception:
                    return 0
    try:
        ref = wo_doc.modified or wo_doc.creation
        if ref:
            return (frappe.utils.getdate() - (ref.date() if hasattr(ref, "date") else ref)).days
    except Exception:
        pass
    return 0


def _compute_alerts(wo_doc, settings):
    """Calcula la lista completa de alertas para una OT. settings = get_mathipe_settings()."""
    alerts = []
    if not (settings.get("alerts_enabled") and wo_doc):
        return alerts

    today = frappe.utils.getdate()
    revenue = float(getattr(wo_doc, "revenue_total", None) or 0)
    margin_pct = float(getattr(wo_doc, "gross_margin_pct", None) or 0)
    low_margin = float(settings.get("low_margin_pct_threshold") or 15)
    warn_margin = float(settings.get("warning_margin_pct_threshold") or 25)
    wait_approval_days = int(settings.get("waiting_approval_days_threshold") or 3)
    outsource_sent_days = int(settings.get("outsource_sent_days_threshold") or 5)
    status = (getattr(wo_doc, "status", None) or "").strip()
    delivery_date = getattr(wo_doc, "delivery_date", None)

    # A) LOW_MARGIN (solo si revenue_total > 0)
    if revenue > 0:
        if margin_pct < low_margin:
            alerts.append({
                "code": "LOW_MARGIN",
                "level": "danger",
                "title": "Margen bajo",
                "message": "El margen bruto ({:.1f}%) está por debajo del umbral de {}%.".format(margin_pct, low_margin),
                "meta": {"margin_pct": margin_pct, "threshold": low_margin},
            })
        elif margin_pct < warn_margin:
            alerts.append({
                "code": "LOW_MARGIN",
                "level": "warning",
                "title": "Margen en advertencia",
                "message": "El margen bruto ({:.1f}%) está por debajo del umbral de advertencia ({}%).".format(margin_pct, warn_margin),
                "meta": {"margin_pct": margin_pct, "threshold": warn_margin},
            })

    # B) WAITING_APPROVAL_TOO_LONG
    if status == "WaitingApproval":
        days = _days_since_waiting_approval(wo_doc)
        if days >= wait_approval_days:
            alerts.append({
                "code": "WAITING_APPROVAL_TOO_LONG",
                "level": "warning",
                "title": "Aprobación demorada",
                "message": "Lleva {} días esperando aprobación (umbral: {}).".format(days, wait_approval_days),
                "meta": {"days": days, "threshold": wait_approval_days},
            })

    # C) OUTSOURCE_SENT_TOO_LONG (agrupado por proveedor)
    items = getattr(wo_doc, "items", None) or []
    sent_by_supplier = {}
    for i in items:
        if not (i.get("is_outsourced") and (i.get("outsource_status") or "").strip() == "Sent"):
            continue
        supp = (i.get("supplier") or "").strip() or "Sin proveedor"
        sent_at = i.get("outsource_sent_at")
        if not sent_at:
            continue
        try:
            d = sent_at.date() if hasattr(sent_at, "date") else frappe.utils.getdate(sent_at)
            days_sent = (today - d).days
        except Exception:
            days_sent = 0
        if days_sent >= outsource_sent_days:
            sent_by_supplier[supp] = max(sent_by_supplier.get(supp, 0), days_sent)
    for supp, days_sent in sent_by_supplier.items():
        alerts.append({
            "code": "OUTSOURCE_SENT_TOO_LONG",
            "level": "warning",
            "title": "Tercerizado enviado hace mucho",
            "message": "Proveedor '{}': enviado hace {} días (umbral: {}).".format(supp, days_sent, outsource_sent_days),
            "meta": {"supplier": supp, "days": days_sent, "threshold": outsource_sent_days},
        })

    # D) OUTSOURCE_PENDING_VENDOR
    has_pending = any(
        (i.get("is_outsourced") and (i.get("outsource_status") or "").strip() == "PendingVendor")
        for i in items
    )
    if has_pending:
        alerts.append({
            "code": "OUTSOURCE_PENDING_VENDOR",
            "level": "info",
            "title": "Tercerizado pendiente de proveedor",
            "message": "Hay ítems tercerizados sin enviar al proveedor.",
            "meta": {},
        })

    # E) DELIVERY_OVERDUE
    if delivery_date and status not in ("Delivered", "Cancelled"):
        try:
            dd = delivery_date if hasattr(delivery_date, "year") else frappe.utils.getdate(delivery_date)
            if dd < today:
                overdue_days = (today - dd).days
                level = "danger" if overdue_days >= 3 else "warning"
                alerts.append({
                    "code": "DELIVERY_OVERDUE",
                    "level": level,
                    "title": "Entrega atrasada",
                    "message": "Fecha de entrega pasada hace {} día(s).".format(overdue_days),
                    "meta": {"overdue_days": overdue_days},
                })
        except Exception:
            pass

    # F) INVOICE_PENDING_AFTER_DELIVERY (Fase 10)
    delivery_status = (getattr(wo_doc, "delivery_status", None) or "").strip()
    invoice_status = (getattr(wo_doc, "invoice_status", None) or "").strip()
    if delivery_status in ("Delivered", "PickedUp") and invoice_status == "Pending":
        delivered_at = getattr(wo_doc, "delivered_at", None)
        try:
            if delivered_at and hasattr(delivered_at, "date"):
                ref_date = delivered_at.date()
            elif delivered_at:
                ref_date = frappe.utils.getdate(delivered_at)
            else:
                ref_date = frappe.utils.getdate(wo_doc.modified or wo_doc.creation)
            days = (today - ref_date).days
        except Exception:
            days = 0
        warn_days = int(settings.get("invoice_pending_warning_days") or 2)
        danger_days = int(settings.get("invoice_pending_danger_days") or 5)
        if days >= danger_days:
            level = "danger"
        elif days >= warn_days:
            level = "warning"
        else:
            level = "info"
        alerts.append({
            "code": "INVOICE_PENDING_AFTER_DELIVERY",
            "level": level,
            "title": "Factura pendiente",
            "message": "Entrega realizada hace {} día(s) y aún no está facturado.".format(days),
            "meta": {"days": days, "warning_threshold": warn_days, "danger_threshold": danger_days},
        })

    return alerts


def _compute_alerts_summary(wo_doc, settings):
    """Solo counts (danger/warning/info) y top alert para tableros. Barato si ya tienes el doc."""
    alerts = _compute_alerts(wo_doc, settings)
    summary = {"danger": 0, "warning": 0, "info": 0}
    for a in alerts:
        lev = a.get("level") or "info"
        if lev in summary:
            summary[lev] += 1
    top = alerts[0] if alerts else None
    return {
        "alerts_summary": summary,
        "top_alert_level": top.get("level") if top else None,
        "top_alert_code": top.get("code") if top else None,
        "top_alert_title": top.get("title") if top else None,
    }


def _get_wo_detail(work_order_id):
    """Serializa un Mathipe Work Order como dict para el frontend. Incluye status_log ordenado desc."""
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    out = {
        "name": doc.name,
        "sales_order": doc.sales_order,
        "customer": doc.customer,
        "customer_name": doc.customer_name,
        "delivery_date": str(doc.delivery_date) if doc.delivery_date else None,
        "status": doc.status,
        "notes": doc.notes or "",
        "tags": [t.strip() for t in (doc.tags or "").split(",") if t.strip()],
        "assigned_users": [
            {"user": u.user, "full_name": u.full_name or u.user}
            for u in (doc.assigned_users or [])
        ],
        "checklist_items": [
            {
                "name": i.name,
                "title": i.title,
                "done": bool(i.done),
                "done_by": i.done_by,
                "done_at": str(i.done_at) if i.done_at else None,
            }
            for i in (doc.checklist_items or [])
        ],
    }
    # Ítems / Tercerización (Fase 2 Sprint B) + quote_item y campos sync
    if getattr(doc, "items", None):
        out["items"] = [
            {
                "name": i.name,
                "quote_item": (i.get("quote_item") or "").strip() or None,
                "item_code": i.get("item_code"),
                "description": (i.get("description") or "").strip(),
                "product_type": (i.get("product_type") or "").strip() or None,
                "qty": float(i.get("qty") or 0),
                "width": float(i.get("width") or 0) or None,
                "height": float(i.get("height") or 0) or None,
                "area_total": float(i.get("area_total") or 0) or None,
                "cost_total": float(i.get("cost_total") or 0) or None,
                "sale_total": float(i.get("sale_total") or 0) or None,
                "uom": (i.get("uom") or "").strip() or "Unit",
                "source": (i.get("source") or "").strip(),
                "breakdown_version": int(i.get("breakdown_version") or 0) or None,
                "is_outsourced": bool(i.get("is_outsourced")),
                "supplier": (i.get("supplier") or "").strip() or None,
                "outsource_status": (i.get("outsource_status") or "").strip() or None,
                "outsource_sent_at": str(i.outsource_sent_at) if i.get("outsource_sent_at") else None,
                "outsource_received_at": str(i.outsource_received_at) if i.get("outsource_received_at") else None,
                "outsource_cost": float(i.get("outsource_cost") or 0) or None,
                "outsource_notes": (i.get("outsource_notes") or "").strip() or None,
            }
            for i in doc.items
        ]
    else:
        out["items"] = []
    # Historial de estado (ordenado por changed_at desc)
    if getattr(doc, "status_log", None):
        rows = [
            {
                "from_status": r.from_status,
                "to_status": r.to_status,
                "changed_by": r.changed_by,
                "changed_at": str(r.changed_at) if r.changed_at else None,
                "comment": (r.comment or "").strip(),
            }
            for r in doc.status_log
        ]
        rows.sort(key=lambda x: (x["changed_at"] or ""), reverse=True)
        out["status_log"] = rows
    else:
        out["status_log"] = []
    # Resumen financiero (Fase 3)
    out["revenue_total"] = float(doc.revenue_total or 0)
    out["estimated_cost_total"] = float(doc.estimated_cost_total or 0)
    out["real_cost_total"] = float(doc.real_cost_total or 0)
    out["gross_margin"] = float(doc.gross_margin or 0)
    out["gross_margin_pct"] = float(doc.gross_margin_pct or 0)
    # Estados válidos desde el actual (para UI; depende del rol del usuario)
    out["valid_next_statuses"] = _wo_valid_next_statuses(doc.status, frappe.session.user)
    # Fase 5: alertas
    settings = get_mathipe_settings()
    if settings.get("alerts_enabled"):
        full_alerts = _compute_alerts(doc, settings)
        out["alerts"] = full_alerts
        summ = _compute_alerts_summary(doc, settings)
        out["alerts_summary"] = summ["alerts_summary"]
        out["top_alert_level"] = summ["top_alert_level"]
        out["top_alert_code"] = summ["top_alert_code"]
        out["top_alert_title"] = summ["top_alert_title"]
    else:
        out["alerts"] = []
        out["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
        out["top_alert_level"] = None
        out["top_alert_code"] = None
        out["top_alert_title"] = None
    # Fase 9: ruta de producción por sectores
    if getattr(doc, "stages", None):
        out["stages"] = [
            {
                "name": s.name,
                "sector_key": s.sector_key,
                "sector_name": s.sector_name or s.sector_key,
                "stage_status": s.stage_status,
                "assigned_to": s.assigned_to,
                "started_at": str(s.started_at) if s.started_at else None,
                "finished_at": str(s.finished_at) if s.finished_at else None,
                "notes": (s.notes or "").strip(),
                "idx": s.idx,
            }
            for s in doc.stages
        ]
    else:
        out["stages"] = []
    if getattr(doc, "stage_log", None):
        rows = [
            {
                "from_status": r.from_status,
                "to_status": r.to_status,
                "sector_key": r.sector_key,
                "changed_by": r.changed_by,
                "changed_at": str(r.changed_at) if r.changed_at else None,
                "comment": (r.comment or "").strip(),
                "stage_row_id": (r.stage_row_id or "").strip(),
            }
            for r in doc.stage_log
        ]
        rows.sort(key=lambda x: (x["changed_at"] or ""), reverse=True)
        out["stage_log"] = rows
    else:
        out["stage_log"] = []
    out["current_sector"] = _wo_current_sector(doc)
    # Fase 10: despacho y factura
    out["remito_status"] = (getattr(doc, "remito_status", None) or "").strip() or "Pending"
    out["delivery_status"] = (getattr(doc, "delivery_status", None) or "").strip() or "Pending"
    out["invoice_status"] = (getattr(doc, "invoice_status", None) or "").strip() or "Pending"
    out["delivered_at"] = str(doc.delivered_at) if getattr(doc, "delivered_at", None) else None
    # Fase 7: contrato mínimo para dashboard (acciones rápidas)
    out["work_order_id"] = out.get("name")
    out["new_status"] = out.get("status")
    return out


@frappe.whitelist()
def create_or_get_work_order(sales_order_id):
    """Retorna la OT existente o crea una nueva vinculada a la Sales Order."""
    if not sales_order_id:
        frappe.throw("sales_order_id es requerido")

    existing = frappe.db.get_value(
        "Mathipe Work Order", {"sales_order": sales_order_id}, "name"
    )
    if existing:
        return _get_wo_detail(existing)

    try:
        so = frappe.get_doc("Sales Order", sales_order_id)
    except frappe.DoesNotExistError:
        frappe.throw(f"Sales Order '{sales_order_id}' no encontrada")

    doc = frappe.new_doc("Mathipe Work Order")
    doc.sales_order = sales_order_id
    doc.customer = so.customer
    doc.customer_name = so.customer_name
    doc.delivery_date = so.delivery_date
    doc.status = "New"
    quote_id = getattr(so, "mathipe_quote", None) or None
    if quote_id and frappe.db.exists("Mathipe Quote", quote_id):
        quote = frappe.get_doc("Mathipe Quote", quote_id)
        if getattr(doc, "items", None) is not None and quote.items:
            for row in quote.items:
                doc.append("items", _quote_row_to_wo_item(row))
    elif getattr(doc, "items", None) is not None and so.items:
        for row in so.items:
            doc.append("items", {
                "item_code": (row.get("item_code") or "").strip() or None,
                "description": (row.get("description") or row.get("item_code") or "Ítem")[:2000],
                "qty": float(row.get("qty") or 0),
                "uom": (row.get("uom") or "Unit").strip() or "Unit",
                "source": "Sales Order",
                "is_outsourced": 0,
                "outsource_status": "",
            })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(doc.name)


@frappe.whitelist()
def get_work_order(work_order_id):
    """Retorna el detalle de una OT."""
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def get_work_order_by_so(sales_order_id):
    """Retorna la OT vinculada a una Sales Order, si existe."""
    existing = frappe.db.get_value(
        "Mathipe Work Order", {"sales_order": sales_order_id}, "name"
    )
    if not existing:
        return None
    return _get_wo_detail(existing)


@frappe.whitelist()
def update_work_order_assignments(work_order_id, user_ids):
    """Reemplaza los usuarios asignados a la OT."""
    _require_login()
    if isinstance(user_ids, str):
        user_ids = frappe.parse_json(user_ids)
    if not isinstance(user_ids, list):
        user_ids = []

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    doc.set("assigned_users", [])
    for uid in user_ids:
        uid = (uid or "").strip()
        if not uid:
            continue
        full_name = frappe.db.get_value("User", uid, "full_name") or uid
        doc.append("assigned_users", {"user": uid, "full_name": full_name})
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def update_work_order_tags(work_order_id, tags):
    """Reemplaza las etiquetas de la OT (lista → CSV)."""
    _require_login()
    if isinstance(tags, str):
        tags = frappe.parse_json(tags)
    if not isinstance(tags, list):
        tags = []

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    doc.tags = ",".join(t.strip() for t in tags if t.strip())
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def update_work_order_checklist(work_order_id, checklist_items):
    """Reemplaza el checklist de la OT."""
    _require_login()
    if isinstance(checklist_items, str):
        checklist_items = frappe.parse_json(checklist_items)
    if not isinstance(checklist_items, list):
        checklist_items = []

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    now = frappe.utils.now_datetime()
    current_user = frappe.session.user

    doc.set("checklist_items", [])
    for item in checklist_items:
        done = bool(item.get("done"))
        done_by = item.get("done_by") or (current_user if done else None)
        done_at = item.get("done_at") or (str(now) if done else None)
        doc.append(
            "checklist_items",
            {
                "title": item.get("title", ""),
                "done": 1 if done else 0,
                "done_by": done_by,
                "done_at": done_at if done else None,
            },
        )
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


def _fase9_init_stages_on_production(work_order_id):
    """Cuando la OT pasa a Production, inicializar stages si no tiene (Fase 9)."""
    if not frappe.db.table_exists("Mathipe WO Stage"):
        return
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    if getattr(doc, "stages", None) and len(doc.stages) > 0:
        return
    init_wo_stages_from_template(work_order_id, template_key=None)


@frappe.whitelist()
def update_work_order_status(work_order_id, to_status, comment=None):
    """Cambia el estado de la OT validando el grafo. Retroceso y Cancelled solo con rol override. Registra en status_log."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    to_status = (to_status or "").strip()
    if not work_order_id:
        frappe.throw("work_order_id es requerido")
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    from_status = doc.status
    if from_status == to_status:
        return _get_wo_detail(work_order_id)

    valid_all = list(WO_STATUS_FLOW) + list(WO_STATUS_SPECIAL)
    if to_status not in valid_all:
        frappe.throw(f"Estado inválido: {to_status}")

    user = frappe.session.user or "Guest"
    allowed = _wo_valid_next_statuses(from_status, user)
    if to_status not in allowed:
        frappe.throw(
            f"No se puede pasar de '{from_status}' a '{to_status}'. "
            f"Estados permitidos: {', '.join(allowed)}"
        )

    # Bloqueo Approved → Production si hay ítems tercerizados no recibidos (Fase 2 Sprint B)
    if to_status == "Production" and getattr(doc, "items", None):
        for it in doc.items:
            if it.get("is_outsourced") and (it.get("outsource_status") or "").strip() != "Received":
                frappe.throw(
                    "No se puede pasar a Producción: hay ítems tercerizados pendientes de recibir."
                )

    # Fase 10: Delivered/PickedUp requiere remito_status == Generated (no exige invoice_status)
    if to_status == "Delivered" and frappe.db.has_column("Mathipe Work Order", "remito_status"):
        remito = (getattr(doc, "remito_status", None) or "").strip()
        if remito != "Generated":
            frappe.throw("Para marcar como Entregado el remito debe estar generado (remito_status = Generated).")
        if frappe.db.has_column("Mathipe Work Order", "delivery_status"):
            doc.delivery_status = "Delivered"
        if frappe.db.has_column("Mathipe Work Order", "delivered_at"):
            doc.delivered_at = frappe.utils.now_datetime()

    # Retroceso: solo roles override; comentario automático OVERRIDE si viene vacío
    is_rollback = _wo_is_rollback(from_status, to_status)
    is_cancelled = to_status == "Cancelled"
    if is_rollback or is_cancelled:
        if not _user_has_override_role(user):
            frappe.throw("No tienes permisos para retroceder estados. Solicita a Gerencia.")
        comment_text = (comment or "").strip()
        if not comment_text:
            comment_text = f"OVERRIDE: retroceso autorizado por rol (user={user})"
        else:
            comment_text = "OVERRIDE: " + comment_text
        comment = comment_text[:2000]

    now = frappe.utils.now_datetime()
    log_comment = (comment or "").strip()[:2000] if not (is_rollback or is_cancelled) else comment
    doc.status = to_status

    if getattr(doc, "status_log", None) is not None and frappe.db.table_exists("Mathipe WO Status Log"):
        doc.append(
            "status_log",
            {
                "from_status": from_status,
                "to_status": to_status,
                "changed_by": user,
                "changed_at": now,
                "comment": log_comment,
            },
        )
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    if to_status == "Production":
        _fase9_init_stages_on_production(work_order_id)
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def get_work_order_details(work_order_id):
    """Retorna el detalle de una OT (incluye status_log). Alias de get_work_order."""
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    return _get_wo_detail(work_order_id)


# ── Fase 9: Sectores y tablero por sector ───────────────────────────────────

@frappe.whitelist()
def get_sectors():
    """Devuelve catálogo de sectores (Mathipe Sector). Si no hay, devuelve template por defecto."""
    if not frappe.db.table_exists("Mathipe Sector"):
        return [{"sector_key": t["sector_key"], "sector_name": t["sector_name"], "color": None, "allow_parallel": 0} for t in DEFAULT_SECTORS_TEMPLATE]
    sectors = frappe.get_all("Mathipe Sector", fields=["sector_key", "sector_name", "color", "allow_parallel"], order_by="sector_key")
    return [{"sector_key": s.sector_key, "sector_name": s.sector_name, "color": s.color, "allow_parallel": s.allow_parallel} for s in sectors]


@frappe.whitelist()
def ensure_default_sectors():
    """Crea sectores base si no existen (idempotente). Solo System Manager o Gerencia."""
    _require_login()
    if not _user_has_override_role(frappe.session.user):
        frappe.throw("Solo Gerencia o System Manager pueden ejecutar ensure_default_sectors.")
    if not frappe.db.table_exists("Mathipe Sector"):
        return {"ok": True, "message": "DocType Mathipe Sector no existe aún. Ejecute migración."}
    for t in DEFAULT_SECTORS_TEMPLATE:
        key = t["sector_key"]
        if frappe.db.exists("Mathipe Sector", {"sector_key": key}):
            continue
        doc = frappe.new_doc("Mathipe Sector")
        doc.sector_key = key
        doc.sector_name = t["sector_name"]
        doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "message": "Sectores por defecto creados/verificados."}


@frappe.whitelist()
def get_sector_board(sector_key, delivery_from=None, delivery_to=None, only_open=1):
    """Devuelve { pending: [], in_progress: [], done: [] } para el tablero del sector. WO en Production con stages."""
    sector_key = (sector_key or "").strip()
    if not sector_key:
        frappe.throw("sector_key es requerido")
    only_open = int(only_open) if only_open is not None else 1
    if not frappe.db.table_exists("Mathipe WO Stage"):
        return {"pending": [], "in_progress": [], "done": []}
    # WO en Production que tengan al menos un stage con este sector_key
    wo_list = frappe.db.sql("""
        SELECT DISTINCT p.name AS work_order_id
        FROM `tabMathipe Work Order` p
        INNER JOIN `tabMathipe WO Stage` s ON s.parent = p.name AND s.parenttype = 'Mathipe Work Order'
        WHERE p.status = 'Production' AND s.sector_key = %(sector_key)s
    """, {"sector_key": sector_key}, as_dict=True)
    wo_ids = [r.work_order_id for r in wo_list]
    if not wo_ids:
        return {"pending": [], "in_progress": [], "done": []}
    placeholders = ", ".join(["%s"] * len(wo_ids))
    stages_rows = frappe.db.sql("""
        SELECT s.parent AS work_order_id, s.name AS stage_row_id, s.stage_status, s.assigned_to, s.idx
        FROM `tabMathipe WO Stage` s
        WHERE s.parent IN ({0}) AND s.sector_key = %s
    """.format(placeholders), wo_ids + [sector_key], as_dict=True)
    stage_by_wo = {}
    for r in stages_rows:
        stage_by_wo[r.work_order_id] = {"stage_row_id": r.stage_row_id, "stage_status": r.stage_status, "assigned_to": r.assigned_to, "idx": r.idx}
    wo_data = frappe.db.sql("""
        SELECT name, sales_order, customer_name, delivery_date, status, gross_margin_pct
        FROM `tabMathipe Work Order`
        WHERE name IN ({0})
    """.format(placeholders), wo_ids, as_dict=True)
    settings = get_mathipe_settings() if frappe.db.table_exists("Mathipe Settings") else {}
    alerts_enabled = settings.get("alerts_enabled")
    pending, in_progress, done = [], [], []
    for w in wo_data:
        wid = w.name
        st = stage_by_wo.get(wid, {})
        stage_status = (st.get("stage_status") or "Pending").strip()
        card = {
            "work_order_id": wid,
            "sales_order": w.sales_order,
            "customer_name": w.customer_name or "",
            "delivery_date": str(w.delivery_date) if w.delivery_date else None,
            "wo_status": w.status,
            "stage_status": stage_status,
            "stage_row_id": st.get("stage_row_id"),
            "assigned_to": st.get("assigned_to"),
            "top_alert_title": None,
            "alerts_summary": {"danger": 0, "warning": 0, "info": 0},
            "gross_margin_pct": float(w.gross_margin_pct or 0),
        }
        if alerts_enabled and wid:
            try:
                doc = frappe.get_doc("Mathipe Work Order", wid)
                summ = _compute_alerts_summary(doc, settings)
                card["alerts_summary"] = summ.get("alerts_summary", card["alerts_summary"])
                card["top_alert_title"] = summ.get("top_alert_title")
            except Exception:
                pass
        if only_open and stage_status == "Done":
            done.append(card)
        elif stage_status == "In Progress":
            in_progress.append(card)
        elif stage_status == "Done":
            done.append(card)
        else:
            pending.append(card)
    return {"pending": pending, "in_progress": in_progress, "done": done}


@frappe.whitelist()
def update_wo_stage(work_order_id, stage_row_id, action, comment=None, assigned_to=None):
    """Actualiza etapa: take (Pending->In Progress), finish (In Progress->Done), reopen, skip (solo override), assign."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    stage_row_id = (stage_row_id or "").strip()
    action = (action or "").strip().lower()
    if not work_order_id or not stage_row_id:
        frappe.throw("work_order_id y stage_row_id son requeridos")
    if action not in ("take", "finish", "reopen", "skip", "assign"):
        frappe.throw("action debe ser: take, finish, reopen, skip o assign")
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    if not getattr(doc, "stages", None):
        frappe.throw("Esta OT no tiene etapas de producción (ruta no inicializada).")
    row = None
    for s in doc.stages:
        if s.name == stage_row_id:
            row = s
            break
    if not row:
        frappe.throw(f"Etapa '{stage_row_id}' no encontrada en la OT.")
    sector_key = (row.sector_key or "").strip()
    user = frappe.session.user or "Guest"
    if action in ("reopen", "skip"):
        if not _user_has_override_role(user):
            frappe.throw("Solo Gerencia o System Manager pueden reabrir o omitir etapas.")
    else:
        if not _user_can_operate_sector(user, sector_key):
            frappe.throw(f"No tienes permiso para operar el sector '{sector_key}'.")
    now = frappe.utils.now_datetime()
    from_status = (row.stage_status or "").strip()
    to_status = None
    if action == "take":
        if from_status != "Pending":
            frappe.throw("Solo se puede 'tomar' una etapa en estado Pending.")
        to_status = "In Progress"
        if not row.started_at:
            row.started_at = now
    elif action == "finish":
        if from_status != "In Progress":
            frappe.throw("Solo se puede 'finalizar' una etapa en estado In Progress.")
        to_status = "Done"
        row.finished_at = now
    elif action == "reopen":
        to_status = "In Progress"
        row.finished_at = None
    elif action == "skip":
        to_status = "Skipped"
    elif action == "assign":
        assigned_to = (assigned_to or "").strip() or None
        row.assigned_to = assigned_to
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return _get_wo_detail(work_order_id)
    if to_status:
        row.stage_status = to_status
    if getattr(doc, "stage_log", None) is not None and frappe.db.table_exists("Mathipe WO Stage Log"):
        doc.append("stage_log", {
            "from_status": from_status,
            "to_status": to_status or from_status,
            "sector_key": sector_key,
            "changed_by": user,
            "changed_at": now,
            "comment": (comment or "").strip()[:2000] or None,
            "stage_row_id": stage_row_id,
        })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def init_wo_stages_from_template(work_order_id, template_key=None):
    """Inicializa stages de la OT. Si template_key es el name de un Mathipe Route Template, usa sus pasos;
    si no, usa DEFAULT_SECTORS_TEMPLATE. Idempotente: si ya hay stages, no duplica."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    if not work_order_id:
        frappe.throw("work_order_id es requerido")
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    if getattr(doc, "stages", None) and len(doc.stages) > 0:
        return _get_wo_detail(work_order_id)
    if not frappe.db.table_exists("Mathipe WO Stage"):
        frappe.throw("DocType Mathipe WO Stage no existe. Ejecute migración.")
    template_name = (template_key or "").strip()
    if template_name and frappe.db.exists("Mathipe Route Template", template_name):
        route_doc = frappe.get_doc("Mathipe Route Template", template_name)
        for i, step in enumerate(getattr(route_doc, "steps", None) or [], start=1):
            sector_link = step.get("sector_key")
            sector_key = sector_name = ""
            if sector_link:
                sec = frappe.db.get_value("Mathipe Sector", sector_link, ["sector_key", "sector_name"], as_dict=True)
                if sec:
                    sector_key = (sec.get("sector_key") or sector_link)[:140]
                    sector_name = (sec.get("sector_name") or sector_key)[:140]
            doc.append("stages", {
                "sector_key": sector_key or str(sector_link),
                "sector_name": sector_name,
                "stage_status": "Pending",
                "idx": i,
            })
    else:
        for t in DEFAULT_SECTORS_TEMPLATE:
            doc.append("stages", {
                "sector_key": t["sector_key"],
                "sector_name": t["sector_name"],
                "stage_status": "Pending",
                "idx": t["idx"],
            })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


# ── Fase 10: Tablero despacho (entrega sin factura) ───────────────────────────

@frappe.whitelist()
def get_dispatch_board():
    """Tablero despacho: 4 listas — to_remito, to_deliver, delivered_uninvoiced, completed."""
    if not frappe.db.has_column("Mathipe Work Order", "remito_status"):
        return {"to_remito": [], "to_deliver": [], "delivered_uninvoiced": [], "completed": []}
    cols = ["name", "sales_order", "customer_name", "delivery_date", "status"]
    if frappe.db.has_column("Mathipe Work Order", "remito_status"):
        cols.append("remito_status")
    if frappe.db.has_column("Mathipe Work Order", "delivery_status"):
        cols.append("delivery_status")
    if frappe.db.has_column("Mathipe Work Order", "invoice_status"):
        cols.append("invoice_status")
    if frappe.db.has_column("Mathipe Work Order", "delivered_at"):
        cols.append("delivered_at")
    rows = frappe.get_all(
        "Mathipe Work Order",
        fields=cols,
        filters={"status": ["not in", ["Cancelled"]]},
        order_by="delivery_date asc",
    )
    to_remito = []
    to_deliver = []
    delivered_uninvoiced = []
    completed = []
    settings = get_mathipe_settings()
    for r in rows:
        r["work_order_id"] = r.get("name")
        r["delivery_date"] = str(r["delivery_date"]) if r.get("delivery_date") else None
        r["delivered_at"] = str(r["delivered_at"]) if r.get("delivered_at") else None
        remito = (r.get("remito_status") or "").strip() or "Pending"
        delivery = (r.get("delivery_status") or "").strip() or "Pending"
        invoice = (r.get("invoice_status") or "").strip() or "Pending"
        if remito == "Pending":
            to_remito.append(r)
        elif delivery in ("Delivered", "PickedUp") and invoice == "Invoiced":
            completed.append(r)
        elif delivery in ("Delivered", "PickedUp") and invoice == "Pending":
            delivered_uninvoiced.append(r)
        elif delivery in ("Pending", "Ready"):
            to_deliver.append(r)
        else:
            to_deliver.append(r)
        if settings.get("alerts_enabled"):
            try:
                doc = frappe.get_doc("Mathipe Work Order", r["name"])
                summ = _compute_alerts_summary(doc, settings)
                r["alerts_summary"] = summ["alerts_summary"]
                r["top_alert_title"] = summ["top_alert_title"]
                r["top_alert_level"] = summ["top_alert_level"]
            except Exception:
                r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
                r["top_alert_title"] = r["top_alert_level"] = None
        else:
            r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
            r["top_alert_title"] = r["top_alert_level"] = None
    return {"to_remito": to_remito, "to_deliver": to_deliver, "delivered_uninvoiced": delivered_uninvoiced, "completed": completed}


@frappe.whitelist()
def mark_wo_invoiced(work_order_id):
    """Marca la OT como facturada (invoice_status = Invoiced). Fase 10."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    if not work_order_id:
        frappe.throw("work_order_id es requerido")
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    if not frappe.db.has_column("Mathipe Work Order", "invoice_status"):
        frappe.throw("El campo invoice_status no existe. Ejecute migración Fase 10.")
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    doc.invoice_status = "Invoiced"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def get_work_order_items(work_order_id):
    """Devuelve lista de ítems de la OT con campos de tercerización y quote_item (Fase 2)."""
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    return _get_wo_detail(work_order_id).get("items", [])


@frappe.whitelist()
def resync_work_order_items_from_quote(work_order_id):
    """Re-sincroniza WO Items desde la Quote vinculada (SO → mathipe_quote). Solo roles override (System Manager/Gerencia)."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    if not work_order_id:
        frappe.throw("work_order_id es requerido")
    if not _user_has_override_role(frappe.session.user):
        frappe.throw("Solo Gerencia o System Manager pueden re-sincronizar ítems desde la cotización.")
    if not frappe.db.exists("Mathipe Work Order", work_order_id):
        frappe.throw(f"Orden de Trabajo '{work_order_id}' no encontrada")
    wo = frappe.get_doc("Mathipe Work Order", work_order_id)
    so_name = (wo.sales_order or "").strip()
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw("La OT no tiene Sales Order vinculada.")
    so = frappe.get_doc("Sales Order", so_name)
    quote_id = (getattr(so, "mathipe_quote", None) or "").strip()
    if not quote_id or not frappe.db.exists("Mathipe Quote", quote_id):
        frappe.throw("La orden de venta no está vinculada a una cotización (mathipe_quote).")
    _sync_wo_items_from_quote(work_order_id, quote_id)
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def update_work_order_item(work_order_id, item_row_id, patch_fields):
    """Actualiza campos de un ítem WO (is_outsourced, supplier, outsource_cost, outsource_notes). Valida supplier si is_outsourced."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    item_row_id = (item_row_id or "").strip()
    if not work_order_id or not item_row_id:
        frappe.throw("work_order_id e item_row_id son requeridos")
    if isinstance(patch_fields, str):
        patch_fields = frappe.parse_json(patch_fields) or {}
    if not isinstance(patch_fields, dict):
        frappe.throw("patch_fields debe ser un objeto")

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    if not getattr(doc, "items", None):
        frappe.throw("Esta OT no tiene ítems editables")
    row = None
    for i in doc.items:
        if i.name == item_row_id:
            row = i
            break
    if not row:
        frappe.throw(f"Ítem '{item_row_id}' no encontrado en la OT")

    for key in ("is_outsourced", "supplier", "outsource_cost", "outsource_notes"):
        if key in patch_fields:
            if key == "is_outsourced":
                row.set(key, bool(patch_fields[key]))
            elif key == "supplier":
                row.set(key, (patch_fields[key] or "").strip() or None)
            elif key == "outsource_cost":
                row.set(key, float(patch_fields[key]) if patch_fields[key] is not None else None)
            else:
                row.set(key, (patch_fields[key] or "").strip()[:2000] or None)

    if row.get("is_outsourced") and not row.get("supplier"):
        frappe.throw("Si el ítem es tercerizado, el proveedor es obligatorio.")
    if row.get("is_outsourced") and not row.get("outsource_status"):
        row.set("outsource_status", "PendingVendor")

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def update_outsource_status(work_order_id, item_row_id, action, comment=None):
    """Marca ítem tercerizado como Sent/Received/Pending. Registra en Status Log con prefijo OUTSOURCE (Fase 2 Sprint B)."""
    _require_login()
    work_order_id = (work_order_id or "").strip()
    item_row_id = (item_row_id or "").strip()
    action = (action or "").strip().lower()
    if not work_order_id or not item_row_id:
        frappe.throw("work_order_id e item_row_id son requeridos")
    if action not in ("sent", "received", "pending"):
        frappe.throw("action debe ser: sent, received o pending")

    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    if not getattr(doc, "items", None):
        frappe.throw("Esta OT no tiene ítems")
    row = None
    for i in doc.items:
        if i.name == item_row_id:
            row = i
            break
    if not row:
        frappe.throw(f"Ítem '{item_row_id}' no encontrado en la OT")
    if not row.get("is_outsourced"):
        frappe.throw("El ítem no está marcado como tercerizado")

    now = frappe.utils.now_datetime()
    user = frappe.session.user or "Guest"
    status_map = {"sent": "Sent", "received": "Received", "pending": "PendingVendor"}
    new_status = status_map[action]

    row.set("outsource_status", new_status)
    if action == "sent":
        row.set("outsource_sent_at", now)
    elif action == "received":
        row.set("outsource_received_at", now)

    item_desc = (row.get("description") or row.get("item_code") or item_row_id)[:80]
    supplier_name = (row.get("supplier") or "")
    cost_str = ""
    if row.get("outsource_cost"):
        cost_str = " cost={}".format(row.get("outsource_cost"))
    log_msg = "OUTSOURCE: item={} status={} supplier={}{}".format(
        item_desc, new_status, supplier_name, cost_str
    )
    if comment:
        log_msg += " | {}".format((comment or "").strip()[:500])

    if getattr(doc, "status_log", None) is not None and frappe.db.table_exists("Mathipe WO Status Log"):
        doc.append(
            "status_log",
            {
                "from_status": doc.status,
                "to_status": doc.status,
                "changed_by": user,
                "changed_at": now,
                "comment": log_msg[:2000],
            },
        )
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def get_outsource_board(filters=None):
    """Devuelve ítems tercerizados agrupados en pending_vendor, sent, received (Fase 2 Sprint B)."""
    if filters is None or (isinstance(filters, str) and not filters.strip()):
        filters = {}
    elif isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}

    supplier = (filters.get("supplier") or "").strip() or None
    only_overdue = bool(filters.get("only_overdue"))
    date_from = (filters.get("date_from") or "").strip() or None
    date_to = (filters.get("date_to") or "").strip() or None

    conds = ["wi.is_outsourced = 1"]
    args = []
    if supplier:
        conds.append("wi.supplier = %s")
        args.append(supplier)
    if date_from:
        conds.append("wo.delivery_date >= %s")
        args.append(date_from)
    if date_to:
        conds.append("wo.delivery_date <= %s")
        args.append(date_to)
    where = " AND ".join(conds)

    sql = """
        SELECT
            wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status,
            wi.name AS item_row_id, wi.item_code, wi.description, wi.qty, wi.supplier,
            wi.outsource_status, wi.outsource_sent_at, wi.outsource_received_at, wi.outsource_cost
        FROM `tabMathipe WO Item` wi
        INNER JOIN `tabMathipe Work Order` wo ON wo.name = wi.parent
        WHERE {where}
        ORDER BY wo.delivery_date ASC, wi.idx ASC
    """.format(where=where)

    rows = frappe.db.sql(sql, args, as_dict=True)
    today = frappe.utils.getdate()
    pending_vendor = []
    sent = []
    received = []
    for r in rows:
        r["delivery_date"] = str(r["delivery_date"]) if r.get("delivery_date") else None
        r["customer"] = (r.get("customer_name") or "").strip() or None
        r["wo_status"] = (r.get("status") or "").strip() or None
        item_desc = (r.get("description") or r.get("item_code") or "Ítem")[:60]
        r["item_summary"] = item_desc
        r["item_desc"] = item_desc
        r["time_since"] = None
        if r.get("outsource_sent_at"):
            r["time_since"] = str(r["outsource_sent_at"])
        if r.get("outsource_received_at"):
            r["time_since"] = str(r["outsource_received_at"])
        if only_overdue and r.get("delivery_date"):
            try:
                d = frappe.utils.getdate(r["delivery_date"])
                if d >= today:
                    continue
            except Exception:
                pass
        status = (r.get("outsource_status") or "").strip()
        if status == "PendingVendor":
            pending_vendor.append(r)
        elif status == "Sent":
            sent.append(r)
        elif status == "Received":
            received.append(r)

    # Fase 5: alertas por WO (una vez por work_order_id, adjuntar a cada fila)
    settings = get_mathipe_settings()
    wo_alerts = {}
    if settings.get("alerts_enabled"):
        for r in rows:
            wid = r.get("work_order_id")
            if wid and wid not in wo_alerts:
                try:
                    doc = frappe.get_doc("Mathipe Work Order", wid)
                    wo_alerts[wid] = _compute_alerts_summary(doc, settings)
                except Exception:
                    wo_alerts[wid] = {"alerts_summary": {"danger": 0, "warning": 0, "info": 0}, "top_alert_level": None, "top_alert_code": None, "top_alert_title": None}
        for r in pending_vendor + sent + received:
            wid = r.get("work_order_id")
            s = wo_alerts.get(wid) or {"alerts_summary": {"danger": 0, "warning": 0, "info": 0}, "top_alert_level": None, "top_alert_code": None, "top_alert_title": None}
            r["alerts_summary"] = s.get("alerts_summary", {"danger": 0, "warning": 0, "info": 0})
            r["top_alert_level"] = s.get("top_alert_level")
            r["top_alert_code"] = s.get("top_alert_code")
            r["top_alert_title"] = s.get("top_alert_title")
    else:
        for r in pending_vendor + sent + received:
            r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
            r["top_alert_level"] = r["top_alert_code"] = r["top_alert_title"] = None

    return {"pending_vendor": pending_vendor, "sent": sent, "received": received}


@frappe.whitelist()
def update_wo_status(work_order_id, status, comment=None):
    """Cambia el estado de la OT. Delega en update_work_order_status (Fase 2: con log)."""
    return update_work_order_status(work_order_id, status, comment=comment)


@frappe.whitelist()
def request_client_approval(work_order_id, message=""):
    """Solicita aprobación al cliente: cambia estado a WaitingApproval (con log)."""
    comment = f"Aprobación solicitada al cliente. {message or ''}".strip() or None
    return update_work_order_status(work_order_id, "WaitingApproval", comment=comment)


@frappe.whitelist()
def approve_work_order(work_order_id, comment=""):
    """Aprueba la OT: cambia estado a Approved (con log)."""
    return update_work_order_status(work_order_id, "Approved", comment=(comment or "").strip() or None)


@frappe.whitelist()
def get_my_work_orders(user=None):
    """Retorna las OTs asignadas al usuario actual (excluye Done/Delivered/Cancelled)."""
    if not user:
        user = frappe.session.user

    rows = frappe.db.sql(
        """
        SELECT
            wo.name, wo.sales_order, wo.customer_name,
            wo.delivery_date, wo.status, wo.tags
        FROM `tabMathipe Work Order` wo
        INNER JOIN `tabMathipe WO Assigned User` wou ON wou.parent = wo.name
        WHERE wou.user = %(user)s
          AND wo.status NOT IN ('Done', 'Delivered', 'Cancelled')
        ORDER BY wo.delivery_date ASC
        """,
        {"user": user},
        as_dict=True,
    )

    for r in rows:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        r["tags"] = [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()]

    return rows


@frappe.whitelist()
def get_wo_board():
    """Retorna las OTs agrupadas por estado para los tableros Kanban."""
    rows = frappe.db.sql(
        """
        SELECT
            wo.name, wo.sales_order, wo.customer_name,
            wo.delivery_date, wo.status, wo.tags,
            so.customer_name AS so_customer_name
        FROM `tabMathipe Work Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order
        WHERE wo.status NOT IN ('Cancelled', 'Delivered')
        ORDER BY wo.delivery_date ASC
        """,
        as_dict=True,
    )

    board = {
        "new": [],
        "design": [],
        "waiting_approval": [],
        "approved": [],
        "production": [],
        "done": [],
    }

    _status_map = {
        "New": "new",
        "Design": "design",
        "WaitingApproval": "waiting_approval",
        "Approved": "approved",
        "Production": "production",
        "Done": "done",
    }

    for r in rows:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        r["tags"] = [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()]
        r["item_summary"] = r.get("customer_name") or r.get("so_customer_name") or ""
        key = _status_map.get(r.get("status"), "new")
        board[key].append(r)

    # Fase 5: alertas summary por tarjeta (solo si está habilitado)
    settings = get_mathipe_settings()
    if settings.get("alerts_enabled"):
        for key in board:
            for r in board[key]:
                try:
                    wo_doc = frappe.get_doc("Mathipe Work Order", r["name"])
                    summ = _compute_alerts_summary(wo_doc, settings)
                    r["alerts_summary"] = summ["alerts_summary"]
                    r["top_alert_level"] = summ["top_alert_level"]
                    r["top_alert_code"] = summ["top_alert_code"]
                    r["top_alert_title"] = summ["top_alert_title"]
                except Exception:
                    r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
                    r["top_alert_level"] = r["top_alert_code"] = r["top_alert_title"] = None
    else:
        for key in board:
            for r in board[key]:
                r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
                r["top_alert_level"] = r["top_alert_code"] = r["top_alert_title"] = None

    return board


@frappe.whitelist()
def get_work_order_alerts(work_order_id):
    """Fase 5: Devuelve alertas calculadas para una OT y counts (danger/warning/info)."""
    if not work_order_id:
        return {"alerts": [], "summary": {"danger": 0, "warning": 0, "info": 0}}
    try:
        doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    except Exception:
        return {"alerts": [], "summary": {"danger": 0, "warning": 0, "info": 0}}
    settings = get_mathipe_settings()
    alerts = _compute_alerts(doc, settings) if settings.get("alerts_enabled") else []
    summary = {"danger": 0, "warning": 0, "info": 0}
    for a in alerts:
        lev = a.get("level") or "info"
        if lev in summary:
            summary[lev] += 1
    return {"alerts": alerts, "summary": summary}


@frappe.whitelist()
def get_alerts_board(date_from=None, date_to=None, only_open=1, level=None):
    """Fase 5: Lista de OTs con alertas para vista Admin Alertas. Filtro por delivery_date."""
    _require_login()
    if not feature_enabled("alertas"):
        frappe.throw("Tu plan no incluye Alertas.", frappe.PermissionError)
    only_open = frappe.utils.cint(only_open)
    date_from = (date_from or "").strip() or None
    date_to = (date_to or "").strip() or None
    level = (level or "").strip() or None

    conds = ["1=1"]
    params = {}
    if date_from:
        conds.append("wo.delivery_date >= %(date_from)s")
        params["date_from"] = date_from
    if date_to:
        conds.append("wo.delivery_date <= %(date_to)s")
        params["date_to"] = date_to
    if only_open:
        conds.append("wo.status NOT IN ('Delivered', 'Cancelled')")
    where = " AND ".join(conds)

    rows = frappe.db.sql(
        """
        SELECT wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status,
               wo.revenue_total, wo.gross_margin_pct
        FROM `tabMathipe Work Order` wo
        WHERE """ + where + """
        ORDER BY wo.delivery_date ASC
        """,
        params,
        as_dict=True,
    )
    for r in rows:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        r["margin_pct"] = float(r.get("gross_margin_pct") or 0)

    settings = get_mathipe_settings()
    if not settings.get("alerts_enabled"):
        return [{"work_order_id": r["work_order_id"], "sales_order": r.get("sales_order"), "customer_name": r.get("customer_name"), "delivery_date": r.get("delivery_date"), "status": r.get("status"), "margin_pct": r.get("margin_pct"), "alerts_summary": {"danger": 0, "warning": 0, "info": 0}, "top_alert_title": None} for r in rows]

    result = []
    for r in rows:
        try:
            doc = frappe.get_doc("Mathipe Work Order", r["work_order_id"])
            summ = _compute_alerts_summary(doc, settings)
            alerts_list = _compute_alerts(doc, settings)
            if level:
                alerts_list = [a for a in alerts_list if (a.get("level") or "") == level]
                summ["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
                for a in alerts_list:
                    lev = a.get("level") or "info"
                    if lev in summ["alerts_summary"]:
                        summ["alerts_summary"][lev] += 1
            result.append({
                "work_order_id": r["work_order_id"],
                "sales_order": r.get("sales_order"),
                "customer_name": r.get("customer_name"),
                "delivery_date": r.get("delivery_date"),
                "status": r.get("status"),
                "margin_pct": r.get("margin_pct"),
                "alerts_summary": summ["alerts_summary"],
                "top_alert_title": summ.get("top_alert_title"),
            })
        except Exception:
            result.append({
                "work_order_id": r["work_order_id"],
                "sales_order": r.get("sales_order"),
                "customer_name": r.get("customer_name"),
                "delivery_date": r.get("delivery_date"),
                "status": r.get("status"),
                "margin_pct": r.get("margin_pct"),
                "alerts_summary": {"danger": 0, "warning": 0, "info": 0},
                "top_alert_title": None,
            })

    # Filtrar solo filas con al menos una alerta si level está definido (opcional)
    if level:
        result = [x for x in result if (x["alerts_summary"].get("danger") or x["alerts_summary"].get("warning") or x["alerts_summary"].get("info")) > 0]
    return result


@frappe.whitelist()
def update_work_order_notes(work_order_id, notes):
    """Guarda las notas internas de la OT."""
    _require_login()
    doc = frappe.get_doc("Mathipe Work Order", work_order_id)
    doc.notes = notes or ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_wo_detail(work_order_id)


@frappe.whitelist()
def get_system_users():
    """Lista de usuarios del sistema habilitados (para asignación)."""
    users = frappe.db.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "user_image"],
        order_by="full_name asc",
    )
    return users


# ── FASE 3 / FASE 4: helpers de fecha compartidos ────────────────────────────

def _sale_date_where(date_from, date_to, include_fallback):
    """Genera so_filter, cláusula WHERE de fecha y params para queries de analítica.

    Usa COALESCE(so.transaction_date, DATE(wo.creation)) como fecha efectiva.
    Diseñado para queries donde el filtro de fecha va en WHERE (no HAVING).
    La tabla so debe estar ya en el FROM como LEFT JOIN con alias 'so'.
    """
    date_expr = "COALESCE(so.transaction_date, DATE(wo.creation))"
    so_filter = "" if include_fallback else "AND so.transaction_date IS NOT NULL"
    parts = []
    params = {}
    if date_from:
        parts.append(f"{date_expr} >= %(date_from)s")
        params["date_from"] = date_from
    if date_to:
        parts.append(f"{date_expr} <= %(date_to)s")
        params["date_to"] = date_to
    where_date = ("AND " + " AND ".join(parts)) if parts else ""
    return so_filter, where_date, params


# ── FASE 3: Dashboard Financiero ─────────────────────────────────────────────

@frappe.whitelist()
def get_financial_dashboard(date_from=None, date_to=None, include_without_sales_order=0):
    """Devuelve KPIs financieros globales y top/bottom 5 OTs por margen.

    Filtra por Sales Order.transaction_date (fecha real de venta).

    include_without_sales_order (default False):
    - False: excluye OTs sin SO válido (sin transaction_date).
    - True: incluye con fallback DATE(wo.creation) como fecha de referencia.

    Lógica de costo real por ítem:
    - is_outsourced=1 AND outsource_status='Received' → usa outsource_cost
    - cualquier otro caso → usa cost_total (estimado)
    """
    _require_login()
    if not feature_enabled("finanzas"):
        frappe.throw("Tu plan no incluye Finanzas.", frappe.PermissionError)

    include_fallback = frappe.utils.cint(include_without_sales_order)

    # Campo de fecha efectivo
    date_expr = "COALESCE(MAX(so.transaction_date), DATE(wo.creation))"

    # Cláusula extra cuando se excluyen OTs sin SO
    so_filter = "" if include_fallback else "AND so.transaction_date IS NOT NULL"

    # HAVING solo permite agregados o columnas del GROUP BY; wo.creation no está en GROUP BY.
    # Usar la misma expresión con MAX(wo.creation) para que sea agregado válido en HAVING.
    having_date_expr = "COALESCE(MAX(so.transaction_date), DATE(MAX(wo.creation)))"
    date_filters = []
    params = {}
    if date_from:
        date_filters.append(f"{having_date_expr} >= %(date_from)s")
        params["date_from"] = date_from
    if date_to:
        date_filters.append(f"{having_date_expr} <= %(date_to)s")
        params["date_to"] = date_to

    having_date = ("AND " + " AND ".join(date_filters)) if date_filters else ""

    # Agrega financieros por OT directamente desde ítems.
    # MAX(so.transaction_date) es seguro: cada WO tiene a lo sumo un SO.
    rows = frappe.db.sql(f"""
        SELECT
            wo.name AS work_order,
            wo.customer_name,
            wo.delivery_date,
            wo.status,
            MAX(so.transaction_date) AS so_transaction_date,
            {date_expr} AS sale_date,
            COALESCE(SUM(item.sale_total), 0) AS revenue_total,
            COALESCE(SUM(item.cost_total), 0) AS estimated_cost_total,
            COALESCE(SUM(
                CASE
                    WHEN item.is_outsourced = 1 AND item.outsource_status = 'Received'
                    THEN COALESCE(item.outsource_cost, 0)
                    ELSE COALESCE(item.cost_total, 0)
                END
            ), 0) AS real_cost_total
        FROM `tabMathipe Work Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order AND so.docstatus < 2
        LEFT JOIN `tabMathipe WO Item` item ON item.parent = wo.name
        WHERE wo.status != 'Cancelled'
        {so_filter}
        GROUP BY wo.name
        HAVING revenue_total > 0
        {having_date}
    """, params, as_dict=True)

    # Construir lista de OTs con margen calculado
    wo_list = []
    so_linked_count = 0
    fallback_count = 0
    for r in rows:
        revenue = float(r.get("revenue_total") or 0)
        real_cost = float(r.get("real_cost_total") or 0)
        gross_margin = revenue - real_cost
        gross_margin_pct = round(gross_margin / revenue * 100, 2) if revenue > 0 else 0.0
        has_so_date = bool(r.get("so_transaction_date"))
        if has_so_date:
            so_linked_count += 1
        else:
            fallback_count += 1
        wo_list.append({
            "work_order": r.get("work_order") or "",
            "customer_name": (r.get("customer_name") or "").strip(),
            "delivery_date": str(r.get("delivery_date")) if r.get("delivery_date") else None,
            "sale_date": str(r.get("sale_date")) if r.get("sale_date") else None,
            "status": (r.get("status") or "").strip(),
            "revenue_total": revenue,
            "estimated_cost_total": float(r.get("estimated_cost_total") or 0),
            "real_cost_total": real_cost,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct,
        })

    # KPIs globales
    total_revenue = sum(r["revenue_total"] for r in wo_list)
    total_real_cost = sum(r["real_cost_total"] for r in wo_list)
    total_margin = total_revenue - total_real_cost
    avg_margin_pct = round(total_margin / total_revenue * 100, 2) if total_revenue > 0 else 0.0

    # Top 5 más rentables (mayor gross_margin_pct)
    sorted_desc = sorted(wo_list, key=lambda x: x["gross_margin_pct"], reverse=True)
    top_profitable = sorted_desc[:5]

    # Top 5 menos rentables (menor gross_margin_pct)
    sorted_asc = sorted(wo_list, key=lambda x: x["gross_margin_pct"])
    bottom_profitable = sorted_asc[:5]

    return {
        "total_revenue": total_revenue,
        "total_real_cost": total_real_cost,
        "total_margin": total_margin,
        "avg_margin_pct": avg_margin_pct,
        "top_profitable": top_profitable,
        "bottom_profitable": bottom_profitable,
        "total_work_orders": len(wo_list),
        "so_linked_count": so_linked_count,
        "fallback_count": fallback_count,
        "date_field": "coalesce(sales_order.transaction_date, work_order.creation)",
    }


# ── FASE 6: Dashboard Operativo Central ──────────────────────────────────────

LIST_LIMIT = 10
DANGER_WARNING_SAMPLE = 200  # límite para contar danger/warning sin cargar todas las OTs


def _enrich_wo_row(row, doc, settings):
    """Añade gross_margin_pct, alerts_summary, top_alert_* a un dict row (tiene work_order_id, sales_order, etc.)."""
    row["gross_margin_pct"] = float(getattr(doc, "gross_margin_pct", None) or 0)
    summ = _compute_alerts_summary(doc, settings)
    row["alerts_summary"] = summ.get("alerts_summary") or {"danger": 0, "warning": 0, "info": 0}
    row["top_alert_title"] = summ.get("top_alert_title")
    row["top_alert_level"] = summ.get("top_alert_level")
    return row


@frappe.whitelist()
def get_operational_dashboard(delivery_from=None, delivery_to=None, date_from=None, date_to=None):
    """Dashboard operativo central (Control Center tipo Twist Print, SaaS-ready).

    delivery_from/delivery_to: filtro opcional por delivery_date en listas.
    date_from/date_to: usados solo para KPIs financieros (ventas del mes por defecto).
    """
    _require_login()
    today = frappe.utils.getdate()
    delivery_from = (delivery_from or "").strip() or None
    delivery_to = (delivery_to or "").strip() or None
    date_from = (date_from or "").strip() or None
    date_to = (date_to or "").strip() or None
    settings = get_mathipe_settings()

    # Default período financiero = mes actual
    if not date_from and not date_to:
        first = today.replace(day=1)
        date_from = first.strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")

    active_where = "wo.status NOT IN ('Delivered', 'Cancelled')"
    delivery_filter = ""
    delivery_params = {}
    if delivery_from:
        delivery_filter += " AND wo.delivery_date >= %(delivery_from)s"
        delivery_params["delivery_from"] = delivery_from
    if delivery_to:
        delivery_filter += " AND wo.delivery_date <= %(delivery_to)s"
        delivery_params["delivery_to"] = delivery_to

    # ── A) KPIs operativos (siempre) ─────────────────────────────────────────
    base_params = {"today": today, **delivery_params}

    # KPIs operativos: counts globales (sin filtro delivery)
    active_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabMathipe Work Order` wo
        WHERE """ + active_where,
        base_params, as_dict=False)[0][0] or 0

    new_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'New'",
        as_dict=False)[0][0] or 0
    design_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'Design'",
        as_dict=False)[0][0] or 0
    waiting_approval_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'WaitingApproval'",
        as_dict=False)[0][0] or 0
    approved_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'Approved'",
        as_dict=False)[0][0] or 0
    production_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'Production'",
        as_dict=False)[0][0] or 0
    done_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabMathipe Work Order` wo WHERE wo.status = 'Done'",
        as_dict=False)[0][0] or 0

    deliveries_today_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabMathipe Work Order` wo
        WHERE wo.delivery_date = %(today)s AND """ + active_where,
        base_params, as_dict=False)[0][0] or 0

    overdue_deliveries_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabMathipe Work Order` wo
        WHERE wo.delivery_date < %(today)s AND """ + active_where,
        base_params, as_dict=False)[0][0] or 0

    outsource_pending_vendor_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT wo.name) FROM `tabMathipe Work Order` wo
        INNER JOIN `tabMathipe WO Item` wi ON wi.parent = wo.name
        WHERE """ + active_where + """
          AND wi.is_outsourced = 1 AND wi.outsource_status = 'PendingVendor'
    """, as_dict=False)[0][0] or 0

    outsource_sent_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT wo.name) FROM `tabMathipe Work Order` wo
        INNER JOIN `tabMathipe WO Item` wi ON wi.parent = wo.name
        WHERE """ + active_where + """
          AND wi.is_outsourced = 1 AND wi.outsource_status = 'Sent'
    """, as_dict=False)[0][0] or 0

    active_names = frappe.db.sql("""
        SELECT wo.name FROM `tabMathipe Work Order` wo
        WHERE """ + active_where + """
        ORDER BY wo.delivery_date ASC
        LIMIT %s
    """ % DANGER_WARNING_SAMPLE, as_dict=False)
    active_names = [r[0] for r in active_names]
    danger_alerts_count = 0
    warning_alerts_count = 0
    for name in active_names:
        try:
            doc = frappe.get_doc("Mathipe Work Order", name)
            summ = _compute_alerts_summary(doc, settings)
            s = summ.get("alerts_summary") or {}
            if (s.get("danger") or 0) > 0:
                danger_alerts_count += 1
            if (s.get("warning") or 0) > 0:
                warning_alerts_count += 1
        except Exception:
            pass

    # ── B) KPIs financieros (solo si feature_enabled('finanzas')) ────────────
    revenue_period = total_margin_period = avg_margin_pct_period = 0
    if feature_enabled("finanzas"):
        fin = get_financial_dashboard(date_from=date_from, date_to=date_to, include_without_sales_order=0)
        revenue_period = fin.get("total_revenue") or 0
        total_margin_period = fin.get("total_margin") or 0
        avg_margin_pct_period = fin.get("avg_margin_pct") or 0

    # ── C) Listas accionables (máx 10 cada una) ─────────────────────────────
    urgent_where = active_where + delivery_filter
    urgent_rows = frappe.db.sql("""
        SELECT wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status
        FROM `tabMathipe Work Order` wo
        WHERE """ + urgent_where + """
        ORDER BY wo.delivery_date ASC
        LIMIT %s
    """ % LIST_LIMIT, base_params, as_dict=True)
    for r in urgent_rows:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        r.setdefault("time_in_status_days", None)
        try:
            doc = frappe.get_doc("Mathipe Work Order", r["work_order_id"])
            _enrich_wo_row(r, doc, settings)
        except Exception:
            r["gross_margin_pct"] = 0
            r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
            r["top_alert_title"] = r["top_alert_level"] = None
    urgent = urgent_rows

    active_for_critical = frappe.db.sql("""
        SELECT wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status
        FROM `tabMathipe Work Order` wo
        WHERE """ + urgent_where + """
        ORDER BY wo.delivery_date ASC
        LIMIT 50
    """, base_params, as_dict=True)
    critical_candidates = []
    for r in active_for_critical:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        r.setdefault("time_in_status_days", None)
        try:
            doc = frappe.get_doc("Mathipe Work Order", r["work_order_id"])
            _enrich_wo_row(r, doc, settings)
            if (r.get("alerts_summary") or {}).get("danger", 0) > 0:
                critical_candidates.append(r)
        except Exception:
            pass
    critical_candidates.sort(key=lambda x: (x.get("delivery_date") or "", -((x.get("alerts_summary") or {}).get("danger") or 0)))
    critical_alerts = critical_candidates[:LIST_LIMIT]

    wait_rows = frappe.db.sql("""
        SELECT wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status
        FROM `tabMathipe Work Order` wo
        WHERE wo.status = 'WaitingApproval' """ + delivery_filter + """
        LIMIT 25
    """, base_params, as_dict=True)
    wait_with_days = []
    for r in wait_rows:
        if r.get("delivery_date"):
            r["delivery_date"] = str(r["delivery_date"])
        try:
            doc = frappe.get_doc("Mathipe Work Order", r["work_order_id"])
            days = _days_since_waiting_approval(doc)
            r["time_in_status_days"] = days
            _enrich_wo_row(r, doc, settings)
            wait_with_days.append((days, r))
        except Exception:
            r["gross_margin_pct"] = 0
            r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
            r["top_alert_title"] = r["top_alert_level"] = None
            r["time_in_status_days"] = 0
            wait_with_days.append((0, r))
    wait_with_days.sort(key=lambda t: -t[0])
    waiting_approval_oldest = [t[1] for t in wait_with_days[:LIST_LIMIT]]

    threshold_days = int(settings.get("outsource_sent_days_threshold") or 5)
    overdue_wo_ids = frappe.db.sql("""
        SELECT wo.name AS work_order_id,
               MAX(DATEDIFF(%(today)s, wi.outsource_sent_at)) AS time_in_status_days
        FROM `tabMathipe Work Order` wo
        INNER JOIN `tabMathipe WO Item` wi ON wi.parent = wo.name
        WHERE """ + active_where + delivery_filter + """
          AND wi.is_outsourced = 1 AND wi.outsource_status = 'Sent'
          AND wi.outsource_sent_at IS NOT NULL
          AND DATEDIFF(%(today)s, wi.outsource_sent_at) >= %(threshold)s
        GROUP BY wo.name
        ORDER BY time_in_status_days DESC
        LIMIT """ + str(LIST_LIMIT),
        {"today": today, "threshold": threshold_days, **delivery_params}, as_dict=True)
    outsourcing_overdue = []
    for row in overdue_wo_ids:
        wid = row.get("work_order_id")
        days_sent = int(row.get("time_in_status_days") or 0)
        full = frappe.db.sql("""
            SELECT wo.name AS work_order_id, wo.sales_order, wo.customer_name, wo.delivery_date, wo.status
            FROM `tabMathipe Work Order` wo WHERE wo.name = %s
        """, (wid,), as_dict=True)
        if full:
            r = full[0]
            if r.get("delivery_date"):
                r["delivery_date"] = str(r["delivery_date"])
            r["time_in_status_days"] = days_sent
            try:
                doc = frappe.get_doc("Mathipe Work Order", wid)
                _enrich_wo_row(r, doc, settings)
            except Exception:
                r["gross_margin_pct"] = 0
                r["alerts_summary"] = {"danger": 0, "warning": 0, "info": 0}
                r["top_alert_title"] = r["top_alert_level"] = None
            outsourcing_overdue.append(r)
    outsourcing_overdue = outsourcing_overdue[:LIST_LIMIT]

    kpis = {
        "active_count": active_count,
        "new_count": new_count,
        "design_count": design_count,
        "waiting_approval_count": waiting_approval_count,
        "approved_count": approved_count,
        "production_count": production_count,
        "done_count": done_count,
        "deliveries_today_count": deliveries_today_count,
        "overdue_deliveries_count": overdue_deliveries_count,
        "outsource_pending_vendor_count": outsource_pending_vendor_count,
        "outsource_sent_count": outsource_sent_count,
        "danger_alerts_count": danger_alerts_count,
        "warning_alerts_count": warning_alerts_count,
    }
    if feature_enabled("finanzas"):
        kpis["revenue_period"] = revenue_period
        kpis["total_margin_period"] = total_margin_period
        kpis["avg_margin_pct_period"] = avg_margin_pct_period

    return {
        "kpis": kpis,
        "urgent": urgent,
        "critical_alerts": critical_alerts,
        "waiting_approval_oldest": waiting_approval_oldest,
        "outsourcing_overdue": outsourcing_overdue,
    }


# ── FASE 4: Analítica de Rentabilidad por Dimensiones ────────────────────────

@frappe.whitelist()
def get_profitability_breakdown(date_from=None, date_to=None,
                                include_without_sales_order=0, min_revenue=5000):
    """Analítica de rentabilidad desagregada por cliente, tipo de ítem y proveedor.

    Comparte patrón de filtro de fecha con get_financial_dashboard.

    Params:
      date_from / date_to : filtran por Sales Order.transaction_date
                            (fallback: DATE(wo.creation) si include_without_sales_order=1)
      include_without_sales_order : 0 excluye OTs sin SO; 1 usa fallback
      min_revenue         : revenue mínimo para calcular bottom_by_margin_pct (evita ruido)

    Las tres queries son independientes y sin N+1 (un SELECT por dimensión).
    """
    _require_login()
    if not feature_enabled("analitica"):
        frappe.throw("Tu plan no incluye Analítica.", frappe.PermissionError)
    include_fallback = frappe.utils.cint(include_without_sales_order)
    try:
        min_rev = float(min_revenue) if min_revenue is not None and str(min_revenue).strip() != "" else 5000.0
    except (TypeError, ValueError):
        min_rev = 5000.0
    if min_rev < 0:
        min_rev = 5000.0
    # include_without_sales_order=0: excluir OTs sin SO (igual que Finanzas)
    so_filter, where_date, params = _sale_date_where(date_from, date_to, include_fallback)

    # ── Fragmento SQL de costo real reutilizado en las tres queries ───────────
    _real_cost_expr = """COALESCE(SUM(
                CASE
                    WHEN item.is_outsourced = 1 AND item.outsource_status = 'Received'
                    THEN COALESCE(item.outsource_cost, 0)
                    ELSE COALESCE(item.cost_total, 0)
                END
            ), 0)"""

    # ── 1. Por cliente ────────────────────────────────────────────────────────
    customer_rows = frappe.db.sql(f"""
        SELECT
            COALESCE(wo.customer, '') AS customer,
            COALESCE(wo.customer_name, 'Sin cliente') AS customer_name,
            COUNT(DISTINCT wo.name) AS wo_count,
            COALESCE(SUM(item.sale_total), 0) AS revenue_total,
            COALESCE(SUM(item.cost_total), 0) AS estimated_cost_total,
            {_real_cost_expr} AS real_cost_total
        FROM `tabMathipe Work Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order AND so.docstatus < 2
        LEFT JOIN `tabMathipe WO Item` item ON item.parent = wo.name
        WHERE wo.status != 'Cancelled'
        {so_filter}
        {where_date}
        GROUP BY wo.customer, wo.customer_name
        HAVING revenue_total > 0
    """, params, as_dict=True)

    def _enrich(r, revenue_key="revenue_total"):
        revenue = float(r.get(revenue_key) or 0)
        real_cost = float(r.get("real_cost_total") or 0)
        gross_margin = revenue - real_cost
        gross_margin_pct = round(gross_margin / revenue * 100, 2) if revenue > 0 else 0.0
        return revenue, real_cost, gross_margin, gross_margin_pct

    customers = []
    for r in customer_rows:
        revenue, real_cost, gross_margin, gross_margin_pct = _enrich(r)
        customers.append({
            "customer": (r.get("customer") or "").strip() or "",
            "customer_name": (r.get("customer_name") or None) and str(r.get("customer_name")).strip() or "Sin cliente",
            "wo_count": int(r.get("wo_count") or 0),
            "revenue_total": revenue,
            "estimated_cost_total": float(r.get("estimated_cost_total") or 0),
            "real_cost_total": real_cost,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct,
        })

    top_by_revenue = sorted(customers, key=lambda x: x["revenue_total"], reverse=True)[:10]
    top_by_margin = sorted(customers, key=lambda x: x["gross_margin"], reverse=True)[:10]
    eligible = [c for c in customers if c["revenue_total"] >= min_rev]
    bottom_by_margin_pct = sorted(eligible, key=lambda x: x["gross_margin_pct"])[:10]

    # ── 2. Por tipo de ítem ───────────────────────────────────────────────────
    type_rows = frappe.db.sql(f"""
        SELECT
            COALESCE(item.product_type, 'Sin tipo') AS product_type,
            COUNT(*) AS count_items,
            COALESCE(SUM(item.sale_total), 0) AS revenue_total,
            COALESCE(SUM(item.cost_total), 0) AS estimated_cost_total,
            {_real_cost_expr} AS real_cost_total
        FROM `tabMathipe Work Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order AND so.docstatus < 2
        INNER JOIN `tabMathipe WO Item` item ON item.parent = wo.name
        WHERE wo.status != 'Cancelled'
        {so_filter}
        {where_date}
        GROUP BY item.product_type
        HAVING revenue_total > 0
        ORDER BY revenue_total DESC
    """, params, as_dict=True)

    by_type = []
    for r in type_rows:
        revenue, real_cost, gross_margin, gross_margin_pct = _enrich(r)
        by_type.append({
            "product_type": (r.get("product_type") or None) and str(r.get("product_type")).strip() or "Sin tipo",
            "count_items": int(r.get("count_items") or 0),
            "revenue_total": revenue,
            "estimated_cost_total": float(r.get("estimated_cost_total") or 0),
            "real_cost_total": real_cost,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct,
        })

    # ── 3. Por proveedor (solo ítems tercerizados). Costo real = Finanzas: Received→outsource_cost, sino cost_total.
    # received_rate = received_count / count_items (ítems tercerizados).
    supplier_rows = frappe.db.sql(f"""
        SELECT
            COALESCE(item.supplier, 'Sin proveedor') AS supplier,
            COUNT(*) AS count_items,
            SUM(CASE WHEN item.outsource_status = 'Received' THEN 1 ELSE 0 END) AS received_count,
            COALESCE(SUM(item.sale_total), 0) AS outsourced_revenue,
            COALESCE(SUM(item.cost_total), 0) AS estimated_cost_total,
            COALESCE(SUM(
                CASE
                    WHEN item.outsource_status = 'Received'
                    THEN COALESCE(item.outsource_cost, 0)
                    ELSE COALESCE(item.cost_total, 0)
                END
            ), 0) AS real_cost_total
        FROM `tabMathipe Work Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order AND so.docstatus < 2
        INNER JOIN `tabMathipe WO Item` item ON item.parent = wo.name AND item.is_outsourced = 1
        WHERE wo.status != 'Cancelled'
        {so_filter}
        {where_date}
        GROUP BY item.supplier
        HAVING outsourced_revenue > 0
        ORDER BY outsourced_revenue DESC
    """, params, as_dict=True)

    by_supplier = []
    for r in supplier_rows:
        revenue, real_cost, gross_margin, gross_margin_pct = _enrich(r, "outsourced_revenue")
        count = int(r.get("count_items") or 0)
        received = int(r.get("received_count") or 0)
        by_supplier.append({
            "supplier": (r.get("supplier") or None) and str(r.get("supplier")).strip() or "Sin proveedor",
            "count_items": count,
            "received_count": received,
            "received_rate": round(received / count * 100, 1) if count > 0 else 0.0,
            "outsourced_revenue": revenue,
            "estimated_cost_total": float(r.get("estimated_cost_total") or 0),
            "real_cost_total": real_cost,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct,
        })

    return {
        "by_customer": {
            "top_by_revenue": top_by_revenue,
            "top_by_margin": top_by_margin,
            "bottom_by_margin_pct": bottom_by_margin_pct,
            "total_customers": len(customers),
            "min_revenue_threshold": min_rev,
        },
        "by_product_type": by_type,
        "by_supplier": by_supplier,
    }


# ── FASE 11A: Mi Empresa (configurador) ──────────────────────────────────────

def _company_setup_counts():
    """Cuentas de cada entidad de Mi Empresa (tablas pueden no existir aún)."""
    counts = {"machines": 0, "materials": 0, "operations": 0, "route_templates": 0, "product_templates": 0}
    if frappe.db.table_exists("Mathipe Machine"):
        counts["machines"] = frappe.db.count("Mathipe Machine")
    if frappe.db.table_exists("Mathipe Material"):
        counts["materials"] = frappe.db.count("Mathipe Material")
    if frappe.db.table_exists("Mathipe Operation"):
        counts["operations"] = frappe.db.count("Mathipe Operation")
    if frappe.db.table_exists("Mathipe Route Template"):
        counts["route_templates"] = frappe.db.count("Mathipe Route Template")
    if frappe.db.table_exists("Mathipe Product Template"):
        counts["product_templates"] = frappe.db.count("Mathipe Product Template")
    return counts


@frappe.whitelist()
def get_company_setup():
    """Resumen de Mi Empresa: counts y defaults para la SPA."""
    _require_login()
    counts = _company_setup_counts()
    sectors = []
    if frappe.db.table_exists("Mathipe Sector"):
        sectors = frappe.get_all(
            "Mathipe Sector",
            fields=["name", "sector_key", "sector_name"],
            order_by="sector_key",
        )
    return {
        "counts": counts,
        "defaults": {},
        "sectors": [{"name": s.name, "sector_key": s.sector_key, "sector_name": s.sector_name} for s in sectors],
    }


def _apply_search_list(doctype, filters, search, name_field):
    """Listado con búsqueda opcional por name_field (LIKE)."""
    if search and isinstance(search, str) and search.strip():
        esc = _escape_like(search.strip())
        filters[name_field] = ["like", "%" + esc + "%"]
    return frappe.get_all(doctype, filters=filters, fields=["*"], order_by="modified desc")


# ── Machines ─────────────────────────────────────────────────────────────────

@frappe.whitelist()
def list_machines(search=None):
    """Lista Mathipe Machine; opcional búsqueda por machine_name."""
    _require_login()
    if not frappe.db.table_exists("Mathipe Machine"):
        return []
    return _apply_search_list("Mathipe Machine", {}, search, "machine_name")


@frappe.whitelist()
def save_machine(payload):
    """Crea o actualiza Mathipe Machine. payload con name -> update; sin name -> insert. Idempotente."""
    _require_company_setup()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("name") or payload.get("machine_name") or "").strip()
    if not name:
        frappe.throw("machine_name es requerido")
    if frappe.db.exists("Mathipe Machine", name):
        doc = frappe.get_doc("Mathipe Machine", name)
    else:
        doc = frappe.new_doc("Mathipe Machine")
        doc.machine_name = name
    for k, v in payload.items():
        if k in ("name", "machine_name") and doc.get("machine_name"):
            continue
        if k == "machine_name":
            doc.machine_name = (v or "").strip() or doc.machine_name
        elif hasattr(doc, k):
            setattr(doc, k, v)
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "machine_name": doc.machine_name}


@frappe.whitelist()
def delete_machine(name):
    """Elimina Mathipe Machine por name (machine_name)."""
    _require_company_setup()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Machine", name):
        frappe.throw("Máquina no encontrada")
    frappe.delete_doc("Mathipe Machine", name, force=1)
    frappe.db.commit()
    return {"ok": True}


# ── Materials ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def list_materials(search=None):
    """Lista Mathipe Material; opcional búsqueda por material_name."""
    _require_login()
    if not frappe.db.table_exists("Mathipe Material"):
        return []
    return _apply_search_list("Mathipe Material", {}, search, "material_name")


@frappe.whitelist()
def save_material(payload):
    """Crea o actualiza Mathipe Material. payload con name -> update; sin name -> insert."""
    _require_company_setup()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("name") or payload.get("material_name") or "").strip()
    if not name:
        frappe.throw("material_name es requerido")
    if frappe.db.exists("Mathipe Material", name):
        doc = frappe.get_doc("Mathipe Material", name)
    else:
        doc = frappe.new_doc("Mathipe Material")
        doc.material_name = name
    for k, v in payload.items():
        if k in ("name", "material_name") and doc.get("material_name"):
            continue
        if k == "material_name":
            doc.material_name = (v or "").strip() or doc.material_name
        elif hasattr(doc, k):
            setattr(doc, k, v)
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "material_name": doc.material_name}


@frappe.whitelist()
def delete_material(name):
    """Elimina Mathipe Material por name."""
    _require_company_setup()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Material", name):
        frappe.throw("Material no encontrado")
    frappe.delete_doc("Mathipe Material", name, force=1)
    frappe.db.commit()
    return {"ok": True}


# ── Operations ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def list_operations(search=None):
    """Lista Mathipe Operation; opcional búsqueda por operation_name."""
    _require_login()
    if not frappe.db.table_exists("Mathipe Operation"):
        return []
    return _apply_search_list("Mathipe Operation", {}, search, "operation_name")


@frappe.whitelist()
def save_operation(payload):
    """Crea o actualiza Mathipe Operation."""
    _require_company_setup()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("name") or payload.get("operation_name") or "").strip()
    if not name:
        frappe.throw("operation_name es requerido")
    if frappe.db.exists("Mathipe Operation", name):
        doc = frappe.get_doc("Mathipe Operation", name)
    else:
        doc = frappe.new_doc("Mathipe Operation")
        doc.operation_name = name
    for k, v in payload.items():
        if k in ("name", "operation_name") and doc.get("operation_name"):
            continue
        if k == "operation_name":
            doc.operation_name = (v or "").strip() or doc.operation_name
        elif hasattr(doc, k):
            setattr(doc, k, v)
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "operation_name": doc.operation_name}


@frappe.whitelist()
def delete_operation(name):
    """Elimina Mathipe Operation por name."""
    _require_company_setup()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Operation", name):
        frappe.throw("Operación no encontrada")
    frappe.delete_doc("Mathipe Operation", name, force=1)
    frappe.db.commit()
    return {"ok": True}


# ── Route Templates ──────────────────────────────────────────────────────────

@frappe.whitelist()
def list_route_templates(search=None):
    """Lista Mathipe Route Template; opcional búsqueda por route_name."""
    _require_login()
    if not frappe.db.table_exists("Mathipe Route Template"):
        return []
    return _apply_search_list("Mathipe Route Template", {}, search, "route_name")


@frappe.whitelist()
def get_route_template(name):
    """Devuelve un Route Template por name con sus steps."""
    _require_login()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Route Template", name):
        frappe.throw("Plantilla de ruta no encontrada")
    doc = frappe.get_doc("Mathipe Route Template", name)
    return doc.as_dict()


@frappe.whitelist()
def save_route_template(payload):
    """Crea o actualiza Mathipe Route Template con steps."""
    _require_company_setup()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("name") or payload.get("route_name") or "").strip()
    if not name:
        frappe.throw("route_name es requerido")
    if frappe.db.exists("Mathipe Route Template", name):
        doc = frappe.get_doc("Mathipe Route Template", name)
    else:
        doc = frappe.new_doc("Mathipe Route Template")
        doc.route_name = name
    doc.route_name = name
    if "description" in payload:
        doc.description = payload.get("description")
    steps = payload.get("steps") or []
    doc.steps = []
    for i, row in enumerate(steps):
        if isinstance(row, dict):
            doc.append("steps", {
                "sector_key": row.get("sector_key"),
                "mandatory": 1 if row.get("mandatory") else 0,
                "allow_parallel": 1 if row.get("allow_parallel") else 0,
                "default_assigned_role": row.get("default_assigned_role"),
                "sla_days": row.get("sla_days"),
                "idx": i + 1,
            })
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "route_name": doc.route_name}


@frappe.whitelist()
def delete_route_template(name):
    """Elimina Mathipe Route Template por name."""
    _require_company_setup()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Route Template", name):
        frappe.throw("Plantilla de ruta no encontrada")
    frappe.delete_doc("Mathipe Route Template", name, force=1)
    frappe.db.commit()
    return {"ok": True}


# ── Product Templates ────────────────────────────────────────────────────────

@frappe.whitelist()
def list_product_templates(search=None):
    """Lista Mathipe Product Template; opcional búsqueda por product_name."""
    _require_login()
    if not frappe.db.table_exists("Mathipe Product Template"):
        return []
    return _apply_search_list("Mathipe Product Template", {}, search, "product_name")


@frappe.whitelist()
def get_product_template(name):
    """Devuelve un Product Template por name con sus components."""
    _require_login()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Product Template", name):
        frappe.throw("Plantilla de producto no encontrada")
    doc = frappe.get_doc("Mathipe Product Template", name)
    return doc.as_dict()


@frappe.whitelist()
def save_product_template(payload):
    """Crea o actualiza Mathipe Product Template con components."""
    _require_company_setup()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    name = (payload.get("name") or payload.get("product_name") or "").strip()
    if not name:
        frappe.throw("product_name es requerido")
    if frappe.db.exists("Mathipe Product Template", name):
        doc = frappe.get_doc("Mathipe Product Template", name)
    else:
        doc = frappe.new_doc("Mathipe Product Template")
        doc.product_name = name
    doc.product_name = name
    for f in ("category", "costing_mode", "allow_dimensions", "allow_qty", "default_margin_pct",
              "default_route_template", "manual_base_price", "manual_base_cost"):
        if f in payload:
            setattr(doc, f, payload.get(f))
    components = payload.get("components") or []
    doc.components = []
    for i, row in enumerate(components):
        if isinstance(row, dict):
            doc.append("components", {
                "component_type": row.get("component_type"),
                "ref_material": row.get("ref_material"),
                "ref_operation": row.get("ref_operation"),
                "ref_machine": row.get("ref_machine"),
                "qty_mode": row.get("qty_mode"),
                "qty_value": row.get("qty_value"),
                "waste_pct": row.get("waste_pct") or 0,
                "notes": row.get("notes"),
                "idx": i + 1,
            })
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "product_name": doc.product_name}


@frappe.whitelist()
def delete_product_template(name):
    """Elimina Mathipe Product Template por name."""
    _require_company_setup()
    name = (name or "").strip()
    if not name:
        frappe.throw("name es requerido")
    if not frappe.db.exists("Mathipe Product Template", name):
        frappe.throw("Plantilla de producto no encontrada")
    frappe.delete_doc("Mathipe Product Template", name, force=1)
    frappe.db.commit()
    return {"ok": True}
