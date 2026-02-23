/**
 * MATHIPE: al abrir el módulo MATHIPE desde el Desk, ir a la SPA (Dashboard Vue).
 * /app/mathipe → SPA Dashboard. /app solo → Desk estándar (no redirigir).
 */
(function () {
	var path = window.location.pathname.replace(/\/$/, '') || '/';
	if (path === '/app/mathipe') {
		window.location.replace('/dashboard');
	}
})();
