frappe.pages['mathipe-dashboard'].on_page_load = function (wrapper) {
	console.log("MATHIPE DASHBOARD JS CARGÓ ✅", new Date().toISOString());

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true
	});

	$(frappe.render_template("mathipe_dashboard")).appendTo(page.body.addClass("no-border"));

	setTimeout(function () {
		init(page);
	}, 0);
};

function init(page) {
	console.log("MATHIPE DASHBOARD INIT OK ✅", new Date().toISOString());

	var $container = $(page.body).find('#mathipe-dashboard-cards');
	var $loading = $(page.body).find('#mathipe-dashboard-loading');

	frappe.call({
		method: 'mathipe_ui.mathipe_ui.page.mathipe_dashboard.mathipe_dashboard.get_metrics',
		freeze: true,
		freeze_message: 'Cargando dashboard…',
		callback: function (r) {
			$loading.remove();
			var data = r.message || {};
			renderCards($container, data);
		},
		error: function () {
			$loading.replaceWith(
				'<div class="col-12"><div class="alert alert-danger rounded-3">No se pudieron cargar las métricas. Revisá permisos o logs.</div></div>'
			);
		}
	});
}

function renderCards($container, data) {
	var cards = [];

	// Clientes
	cards.push({
		title: 'Clientes',
		icon: 'users',
		items: [
			{ label: 'Nuevos este mes', value: (data.customers_new_this_month != null) ? data.customers_new_this_month : '—' },
			{ label: 'Cuentas por cobrar', value: data.debtors_summary || '—' }
		]
	});

	// Inventario
	cards.push({
		title: 'Inventario',
		icon: 'inventory',
		items: [
			{ label: 'Items bajo mínimo', value: (data.items_below_min != null) ? data.items_below_min : '—' },
			{ label: 'Alerta', value: (data.items_below_min > 0) ? 'Revisar stock' : 'OK' }
		]
	});

	// Producción
	cards.push({
		title: 'Producción',
		icon: 'manufacturing',
		items: [
			{ label: 'Work Orders en curso', value: (data.work_orders_in_progress != null) ? data.work_orders_in_progress : '—' },
			{ label: 'Retrasadas', value: (data.work_orders_delayed != null) ? data.work_orders_delayed : '—' }
		]
	});

	// Entregas
	cards.push({
		title: 'Entregas',
		icon: 'delivery-truck',
		items: [
			{ label: 'Hoy', value: (data.deliveries_today != null) ? data.deliveries_today : '—' },
			{ label: 'Mañana', value: (data.deliveries_tomorrow != null) ? data.deliveries_tomorrow : '—' }
		]
	});

	// Ventas
	cards.push({
		title: 'Ventas',
		icon: 'sell',
		items: [
			{ label: 'Ventas del mes', value: data.sales_this_month || '—' },
			{ label: 'Cotizaciones abiertas', value: (data.quotations_open != null) ? data.quotations_open : '—' }
		]
	});

	var html = '';
	cards.forEach(function (card) {
		var itemsHtml = (card.items || []).map(function (item) {
			return '<div class="d-flex justify-content-between py-1"><span class="text-muted">' + frappe.utils.escape_html(item.label) + '</span><span class="metric-value">' + frappe.utils.escape_html(String(item.value)) + '</span></div>';
		}).join('');
		html += '<div class="col-12 col-md-6 col-lg-4"><div class="card p-3 h-100">' +
			'<div class="card-title">' + frappe.utils.escape_html(card.title) + '</div>' +
			'<div class="card-body p-0">' + itemsHtml + '</div></div></div>';
	});
	$container.append(html);
}
