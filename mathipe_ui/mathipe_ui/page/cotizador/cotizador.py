import frappe
from frappe import _
from frappe.utils import flt

# Usamos util de ERPNext para traer rate real según price list / reglas
try:
    from erpnext.stock.get_item_details import get_item_details
except Exception:
    get_item_details = None


def _get_company():
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def _get_selling_price_list():
    # Standard Selling es el default típico
    return (
        frappe.defaults.get_user_default("Price List")
        or frappe.db.get_single_value("Selling Settings", "selling_price_list")
        or "Standard Selling"
    )


def _find_variant(template_item: str, paper: str, terminacion: str | None = None) -> str | None:
    """
    Busca una variante (Item) cuyo variant_of=template_item y que cumpla:
      - atributo Papel == paper
      - si terminacion viene, atributo Terminación/Terminacion == terminacion
    """
    variants = frappe.get_all(
        "Item",
        filters={"variant_of": template_item, "disabled": 0},
        pluck="name"
    )
    if not variants:
        return None

    # Traemos atributos de todas las variantes (más eficiente que doc por doc)
    rows = frappe.get_all(
        "Item Variant Attribute",
        filters={"parent": ["in", variants]},
        fields=["parent", "attribute", "attribute_value"]
    )

    by_item = {}
    for r in rows:
        by_item.setdefault(r["parent"], {}).setdefault(r["attribute"], set()).add(r["attribute_value"])

    # Normalizamos nombre del atributo de terminación
    term_attr_candidates = ["Terminación", "Terminacion", "Terminación ", "Terminacion "]

    for item_code in variants:
        attrs = by_item.get(item_code, {})
        paper_ok = paper in attrs.get("Papel", set())
        if not paper_ok:
            continue

        if terminacion:
            term_ok = False
            for a in term_attr_candidates:
                if terminacion in attrs.get(a, set()):
                    term_ok = True
                    break
            if not term_ok:
                continue

        return item_code

    return None


@frappe.whitelist()
def get_templates():
    """
    Devuelve items plantilla (templates) que tengan variantes.
    """
    items = frappe.get_all(
        "Item",
        filters={"has_variants": 1, "disabled": 0},
        fields=["item_code", "item_name"],
        order_by="item_name asc"
    )
    return items


@frappe.whitelist()
def get_variant_options(template_item: str):
    """
    Devuelve opciones disponibles para:
      - papers: valores del atributo Papel entre las variantes del template
      - terminaciones: valores del atributo Terminación/Terminacion si existe
    """
    if not template_item:
        return {"papers": [], "terminaciones": [], "terminacion_attribute": None}

    variants = frappe.get_all(
        "Item",
        filters={"variant_of": template_item, "disabled": 0},
        pluck="name"
    )
    if not variants:
        return {"papers": [], "terminaciones": [], "terminacion_attribute": None}

    rows = frappe.get_all(
        "Item Variant Attribute",
        filters={"parent": ["in", variants]},
        fields=["attribute", "attribute_value"]
    )

    papers = set()
    term_values = set()
    term_attr_found = None

    for r in rows:
        attr = r["attribute"]
        val = r["attribute_value"]

        if attr == "Papel":
            papers.add(val)

        if attr in ("Terminación", "Terminacion"):
            term_attr_found = attr
            term_values.add(val)

    return {
        "papers": sorted(papers),
        "terminaciones": sorted(term_values),
        "terminacion_attribute": term_attr_found
    }


@frappe.whitelist()
def get_pricing(template_item: str, paper: str, qty: float = 1, terminacion: str | None = None):
    """
    Resuelve la variante y calcula:
      - rate (precio unitario)
      - net = rate * qty
      - vat = 21%
      - total
    """
    qty = flt(qty) if qty else 0
    if not template_item or not paper or qty <= 0:
        return {"item_code": None, "pricing": None}

    item_code = _find_variant(template_item, paper, terminacion)
    if not item_code:
        return {"item_code": None, "pricing": None}

    company = _get_company()
    price_list = _get_selling_price_list()

    rate = None

    # Intentamos pricing real con util ERPNext
    if get_item_details:
        args = {
            "item_code": item_code,
            "company": company,
            "price_list": price_list,
            "qty": qty,
            "doctype": "Sales Order",
            "conversion_rate": 1,
            "plc_conversion_rate": 1,
            "currency": frappe.db.get_value("Company", company, "default_currency") if company else None,
        }
        details = get_item_details(args)
        rate = flt(details.get("price_list_rate") or details.get("rate") or 0)

    # Fallback: Item Price directo
    if not rate:
        rate = flt(
            frappe.db.get_value(
                "Item Price",
                {"item_code": item_code, "price_list": price_list},
                "price_list_rate"
            )
            or 0
        )

    if not rate:
        return {"item_code": item_code, "pricing": None}

    net = flt(rate * qty)
    vat = flt(net * 0.21)
    total = flt(net + vat)

    return {
        "item_code": item_code,
        "pricing": {
            "qty": qty,
            "rate": rate,
            "net": net,
            "vat": vat,
            "total": total,
            "price_list": price_list,
            "company": company
        }
    }


@frappe.whitelist()
def create_sales_order(item_code: str, qty: float, rate: float):
    """
    Crea Sales Order y devuelve su name. Redirección se hace en JS.
    """
    qty = flt(qty) if qty else 0
    rate = flt(rate) if rate else 0

    if not item_code or qty <= 0 or rate <= 0:
        frappe.throw(_("Datos inválidos para crear la orden."))

    company = _get_company()
    if not company:
        frappe.throw(_("No hay Company por defecto configurada."))

    # Elegimos customer por defecto (mejor práctica: setealo en Selling Settings si lo tenés)
    customer = (
        frappe.db.get_single_value("Selling Settings", "default_customer")
        if frappe.db.has_column("Selling Settings", "default_customer")
        else None
    )

    if not customer:
        # fallback: Mostrador (parametrizado para cotizador), luego Consumidor Final, luego primer customer
        if frappe.db.exists("Customer", "Mostrador"):
            customer = "Mostrador"
        elif frappe.db.exists("Customer", "Consumidor Final"):
            customer = "Consumidor Final"
        else:
            customer = frappe.get_all("Customer", pluck="name", limit=1)
            customer = customer[0] if customer else None

    if not customer:
        frappe.throw(_("No existe Customer. Creá uno (ej: 'Mostrador' o 'Consumidor Final') o definí default_customer en Selling Settings."))

    so = frappe.get_doc({
        "doctype": "Sales Order",
        "company": company,
        "customer": customer,
        "items": [
            {
                "item_code": item_code,
                "qty": qty,
                "rate": rate
            }
        ]
    })

    # Defaults y taxes si existen
    so.set_missing_values()

    # Setea template de taxes por defecto si existe en Selling Settings
    taxes_template = frappe.db.get_single_value("Selling Settings", "default_sales_taxes_and_charges_template")
    if taxes_template:
        so.taxes_and_charges = taxes_template
        # recargar taxes
        so.set_taxes(taxes_template)

    so.calculate_taxes_and_totals()
    so.insert(ignore_permissions=True)
    frappe.db.commit()

    return so.name
