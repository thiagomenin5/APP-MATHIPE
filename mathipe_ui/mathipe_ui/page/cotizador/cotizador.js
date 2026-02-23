frappe.pages['cotizador'].on_page_load = function (wrapper) {
	console.log("COTIZADOR JS CARGÓ ✅", new Date().toISOString());

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Cotizador',
		single_column: true
	});

	// HTML inyectado por Frappe desde cotizador.html (frappe.templates["cotizador"])
	$(frappe.render_template("cotizador")).appendTo(page.body.addClass("no-border"));

	// Inicializar después de que el DOM exista
	setTimeout(function () {
		init(page);
	}, 0);
};

function init(page) {
	console.log("COTIZADOR INIT OK ✅", new Date().toISOString());

	var state = {
		template_item: null,
		paper: null,
		terminacion: null,
		qty: 500,
		variant_item_code: null,
		pricing: null
	};

	var $root = $(page.body);
	var $producto = $root.find('#m_producto');
	var $papel = $root.find('#m_papel');
	var $terminacion = $root.find('#m_terminacion');
	var $cantidad = $root.find('#m_cantidad');
	var $reset = $root.find('#m_reset');
	var $label = $root.find('#m_variant_label');
	var $neto = $root.find('#m_neto');
	var $iva = $root.find('#m_iva');
	var $total = $root.find('#m_total');
	var $crear = $root.find('#m_crear_orden');

	if (!$producto.length || !$papel.length || !$cantidad.length || !$crear.length) {
		frappe.msgprint({
			title: 'Falta HTML / IDs',
			message: 'No se encontraron elementos esperados (#m_producto, #m_papel, #m_cantidad, #m_crear_orden).',
			indicator: 'orange'
		});
		return;
	}

	function money(v) {
		if (v === null || v === undefined || isNaN(v)) return '—';
		return format_currency(v, 'ARS');
	}

	function setLoading(isLoading) {
		if (isLoading) {
			$crear.prop('disabled', true).text('Calculando…');
		} else {
			$crear.text('Crear Orden de Venta');
			$crear.prop('disabled', !state.variant_item_code || !state.pricing);
		}
	}

	function resetUI() {
		state.template_item = null;
		state.paper = null;
		state.terminacion = null;
		state.qty = parseFloat($cantidad.val() || 500) || 500;
		state.variant_item_code = null;
		state.pricing = null;

		$producto.val('');
		$papel.prop('disabled', true).html('<option value="">Seleccionar…</option>');
		$terminacion.prop('disabled', true).html('<option value="">(Opcional) Seleccionar…</option>');
		$label.text('Elegí opciones');
		$neto.text('$ —');
		$iva.text('$ —');
		$total.text('$ —');
		$crear.prop('disabled', true);
	}

	function loadTemplates() {
		frappe.call({
			method: 'mathipe_ui.mathipe_ui.page.cotizador.cotizador.get_templates',
			freeze: true,
			freeze_message: 'Cargando productos…',
			callback: function (r) {
				var items = r.message || [];
				var options = ['<option value="">Seleccionar…</option>'].concat(
					items.map(function (x) {
						return '<option value="' + frappe.utils.escape_html(x.item_code) + '">' + frappe.utils.escape_html(x.item_name || x.item_code) + '</option>';
					})
				);
				$producto.html(options.join(''));
			}
		});
	}

	function loadVariantOptions() {
		if (!state.template_item) return;

		$papel.prop('disabled', true).html('<option value="">Cargando…</option>');
		$terminacion.prop('disabled', true).html('<option value="">Cargando…</option>');

		frappe.call({
			method: 'mathipe_ui.mathipe_ui.page.cotizador.cotizador.get_variant_options',
			args: { template_item: state.template_item },
			freeze: true,
			freeze_message: 'Cargando opciones…',
			callback: function (r) {
				var msg = r.message || {};
				var papers = msg.papers || [];
				var termAttrName = msg.terminacion_attribute || null;
				var terms = msg.terminaciones || [];

				var paperOptions = ['<option value="">Seleccionar…</option>'].concat(
					papers.map(function (v) {
						return '<option value="' + frappe.utils.escape_html(v) + '">' + frappe.utils.escape_html(v) + '</option>';
					})
				);
				$papel.html(paperOptions.join('')).prop('disabled', papers.length === 0);

				if (termAttrName && terms.length) {
					var termOptions = ['<option value="">(Opcional) Seleccionar…</option>'].concat(
						terms.map(function (v) {
							return '<option value="' + frappe.utils.escape_html(v) + '">' + frappe.utils.escape_html(v) + '</option>';
						})
					);
					$terminacion.html(termOptions.join('')).prop('disabled', false);
				} else {
					$terminacion.html('<option value="">(No aplica para este producto)</option>').prop('disabled', true);
				}

				state.paper = null;
				state.terminacion = null;
				state.variant_item_code = null;
				state.pricing = null;
				$label.text('Elegí opciones');
				$neto.text('$ —');
				$iva.text('$ —');
				$total.text('$ —');
				$crear.prop('disabled', true);
			}
		});
	}

	function recalcPrice() {
		if (!state.template_item || !state.paper) {
			state.variant_item_code = null;
			state.pricing = null;
			$label.text('Elegí opciones');
			$crear.prop('disabled', true);
			return;
		}

		setLoading(true);

		frappe.call({
			method: 'mathipe_ui.mathipe_ui.page.cotizador.cotizador.get_pricing',
			args: {
				template_item: state.template_item,
				paper: state.paper,
				terminacion: state.terminacion || undefined,
				qty: state.qty
			},
			callback: function (r) {
				var msg = r.message || {};
				state.variant_item_code = msg.item_code || null;
				state.pricing = msg.pricing || null;

				if (!state.variant_item_code || !state.pricing) {
					$label.text('No se encontró variante / precio');
					$neto.text('$ —');
					$iva.text('$ —');
					$total.text('$ —');
					$crear.prop('disabled', true);
					frappe.show_alert({ message: 'No se encontró una variante con esas opciones.', indicator: 'orange' });
				} else {
					$label.text(state.variant_item_code);
					$neto.text(money(state.pricing.net));
					$iva.text(money(state.pricing.vat));
					$total.text(money(state.pricing.total));
					$crear.prop('disabled', false);
				}
				setLoading(false);
			},
			error: function () {
				setLoading(false);
				frappe.msgprint({
					title: 'Error',
					message: 'No se pudo calcular el precio. Revisá la consola y los logs del servidor.',
					indicator: 'red'
				});
				$crear.prop('disabled', true);
			}
		});
	}

	function createSalesOrder() {
		if (!state.variant_item_code || !state.pricing) return;

		frappe.call({
			method: 'mathipe_ui.mathipe_ui.page.cotizador.cotizador.create_sales_order',
			args: {
				item_code: state.variant_item_code,
				qty: state.qty,
				rate: state.pricing.rate
			},
			freeze: true,
			freeze_message: 'Creando Orden de Venta…',
			callback: function (r) {
				var so_name = r.message;
				if (!so_name) {
					frappe.msgprint({ title: 'Error', message: 'No se pudo crear la Sales Order.', indicator: 'red' });
					return;
				}
				frappe.show_alert({ message: 'Orden creada: ' + so_name, indicator: 'green' });
				frappe.set_route('Form', 'Sales Order', so_name);
			},
			error: function () {
				frappe.msgprint({ title: 'Error', message: 'No se pudo crear la Orden de Venta.', indicator: 'red' });
			}
		});
	}

	$producto.on('change', function () {
		state.template_item = $producto.val() || null;
		loadVariantOptions();
	});

	$papel.on('change', function () {
		state.paper = $papel.val() || null;
		recalcPrice();
	});

	$terminacion.on('change', function () {
		state.terminacion = $terminacion.val() || null;
		recalcPrice();
	});

	$cantidad.on('change', function () {
		state.qty = parseFloat($cantidad.val() || 0) || 0;
		recalcPrice();
	});

	$reset.on('click', resetUI);
	$crear.on('click', createSalesOrder);

	resetUI();
	loadTemplates();
}
