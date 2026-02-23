__version__ = "0.0.1"


def _patch_spa_serve():
	"""Sirve la SPA Vue en / y /login al cargar la app."""
	try:
		from mathipe_ui.spa_serve import patch_website_serve
		patch_website_serve()
	except Exception:
		pass  # Evitar romper si la app se carga antes de tener la SPA


def _patch_login_redirect():
	"""Tras el login, redirigir al Dashboard de la SPA (/dashboard) en lugar del Desk."""
	try:
		from mathipe_ui.auth_redirect import patch_login_redirect
		patch_login_redirect()
	except Exception:
		pass


_patch_spa_serve()
_patch_login_redirect()
