# Copyright (c) 2025, Mathipe UI and contributors
# Sirve el index.html de la SPA Vue en la ruta raíz y rutas de la SPA (Vue Router history mode).

from __future__ import unicode_literals

import os

import frappe
from werkzeug.wrappers import Response


# Rutas que debe atender la SPA (primer segmento de la URL, sin /).
# Cualquier path que empiece con uno de estos (o sea exactamente "") devuelve index.html.
SPA_ROUTE_PREFIXES = frozenset([
	"",             # /
	"login",
	"dashboard",
	"orden",        # /orden/:id (detalle de orden)
	"comercial",
	"operaciones",
	"calendario",
	"admin",
	"empresa",
	# Legacy (redirects or unused)
	"cotizador",
	"produccion",
	"inventario",
	"compras",
	"configuracion",
])


def is_spa_path(path):
	if not path:
		return True
	path = path.strip("/")
	first_segment = (path.split("/") or [""])[0]
	return first_segment in SPA_ROUTE_PREFIXES


def get_spa_response():
	"""Devuelve la respuesta con el index.html de la SPA."""
	app_path = frappe.get_app_path("mathipe_ui", "public", "spa", "index.html")
	if not os.path.isfile(app_path):
		frappe.throw("SPA no encontrada. Ejecuta en frontend/: npm run build")
	with open(app_path, "rb") as f:
		html = f.read()
	return Response(html, content_type="text/html; charset=utf-8")


def patch_website_serve():
	"""Parchea get_response para servir la SPA en / y rutas SPA.
	Se parchea tanto serve como frappe.app porque app.py importa get_response al cargar
	y guarda esa referencia; si solo parcheamos serve, las peticiones siguen usando la original."""
	import frappe.website.serve as serve

	original_get_response = serve.get_response

	def get_response(path=None, http_status_code=200):
		path = path or (getattr(frappe.local, "request", None) and frappe.local.request.path or "/")
		if is_spa_path(path):
			return get_spa_response()
		return original_get_response(path=path, http_status_code=http_status_code)

	serve.get_response = get_response
	# Crítico: el handler principal en frappe.app ya importó get_response; hay que actualizarlo ahí también
	try:
		import frappe.app as app_module
		app_module.get_response = get_response
	except Exception:
		pass
