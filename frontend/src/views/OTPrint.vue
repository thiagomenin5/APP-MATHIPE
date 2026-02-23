<template>
  <div class="print-wrapper">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <p>Cargando Orden de Trabajo...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <!-- Contenido imprimible -->
    <div v-else-if="wo" class="ot-page">

      <!-- Encabezado -->
      <div class="header">
        <div class="header-left">
          <div class="company-logo">MATHIPE</div>
          <div class="doc-title">ORDEN DE TRABAJO</div>
        </div>
        <div class="header-right">
          <div class="ot-number">{{ wo.name }}</div>
          <div class="so-number">SO: {{ wo.sales_order }}</div>
          <div class="status-badge">{{ woStatusLabel(wo.status) }}</div>
        </div>
      </div>

      <!-- Info cliente -->
      <div class="info-grid">
        <div class="info-block">
          <div class="info-label">CLIENTE</div>
          <div class="info-value">{{ wo.customer_name || wo.customer }}</div>
        </div>
        <div class="info-block">
          <div class="info-label">FECHA DE ENTREGA</div>
          <div class="info-value urgent" :class="{ urgent: isUrgent }">{{ formatDate(wo.delivery_date) }}</div>
        </div>
        <div class="info-block">
          <div class="info-label">FECHA EMISIÓN</div>
          <div class="info-value">{{ formatDate(today) }}</div>
        </div>
        <div class="info-block">
          <div class="info-label">ESTADO</div>
          <div class="info-value">{{ woStatusLabel(wo.status) }}</div>
        </div>
      </div>

      <!-- Etiquetas -->
      <div v-if="wo.tags && wo.tags.length > 0" class="section">
        <div class="section-title">ETIQUETAS</div>
        <div class="tags-row">
          <span v-for="tag in wo.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>

      <!-- Items de la orden -->
      <div v-if="soItems.length > 0" class="section">
        <div class="section-title">ÍTEMS DE LA ORDEN</div>
        <table class="items-table">
          <thead>
            <tr>
              <th class="col-code">Código</th>
              <th class="col-desc">Descripción</th>
              <th class="col-qty">Cantidad</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in soItems" :key="idx">
              <td class="col-code">{{ item.item_code }}</td>
              <td class="col-desc">{{ item.description || "—" }}</td>
              <td class="col-qty">{{ item.qty }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Checklist -->
      <div v-if="wo.checklist_items && wo.checklist_items.length > 0" class="section">
        <div class="section-title">CHECKLIST DE CONTROL</div>
        <table class="checklist-table">
          <thead>
            <tr>
              <th class="col-check"></th>
              <th>Tarea</th>
              <th class="col-by">Realizado por</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in wo.checklist_items" :key="idx" :class="{ done: item.done }">
              <td class="col-check">
                <span class="checkbox-cell">{{ item.done ? "☑" : "☐" }}</span>
              </td>
              <td :class="{ 'text-done': item.done }">{{ item.title }}</td>
              <td class="col-by">{{ item.done_by || "" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Equipo asignado -->
      <div v-if="wo.assigned_users && wo.assigned_users.length > 0" class="section">
        <div class="section-title">EQUIPO ASIGNADO</div>
        <div class="team-list">
          <span v-for="u in wo.assigned_users" :key="u.user" class="team-member">
            {{ u.full_name || u.user }}
          </span>
        </div>
      </div>

      <!-- Notas -->
      <div v-if="wo.notes" class="section">
        <div class="section-title">NOTAS INTERNAS</div>
        <div class="notes-box">{{ wo.notes }}</div>
      </div>

      <!-- Firma / Aprobación -->
      <div class="signatures">
        <div class="signature-block">
          <div class="signature-line"></div>
          <div class="signature-label">Responsable de producción</div>
        </div>
        <div class="signature-block">
          <div class="signature-line"></div>
          <div class="signature-label">Control de calidad</div>
        </div>
        <div class="signature-block">
          <div class="signature-line"></div>
          <div class="signature-label">Cliente</div>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer">
        <span>Impreso el {{ formatDateTime(new Date()) }}</span>
        <span>{{ wo.name }} — Mathipe</span>
      </div>

      <!-- Botón imprimir (no se imprime) -->
      <div class="print-actions no-print">
        <button type="button" class="btn-print" @click="window.print()">
          Imprimir / Guardar PDF
        </button>
        <button type="button" class="btn-close" @click="window.close()">
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { call } from "@/api/frappe";

const route = useRoute();

const loading = ref(true);
const error = ref(null);
const wo = ref(null);
const soItems = ref([]);
const today = new Date().toISOString().split("T")[0];

const isUrgent = computed(() => {
  if (!wo.value?.delivery_date) return false;
  const d = new Date(wo.value.delivery_date);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((d - now) / 86400000) <= 1;
});

onMounted(async () => {
  const id = route.params.id;
  if (!id) { error.value = "Falta el ID de la OT."; loading.value = false; return; }

  try {
    const res = await call("mathipe_ui.api.get_work_order", { work_order_id: id });
    wo.value = res?.message ?? res ?? null;
    if (!wo.value) { error.value = "No se encontró la Orden de Trabajo."; loading.value = false; return; }

    // Cargar items de la Sales Order
    if (wo.value.sales_order) {
      try {
        const soRes = await call("mathipe_ui.api.get_order_details", { order_id: wo.value.sales_order });
        const soData = soRes?.message ?? soRes ?? {};
        soItems.value = soData.items || [];
      } catch (_) { /* no crítico */ }
    }
  } catch (e) {
    error.value = e.message || "Error al cargar la OT.";
  } finally {
    loading.value = false;
  }
});

function woStatusLabel(status) {
  const map = {
    New: "Nuevo", Design: "Diseño", WaitingApproval: "Esperando OK",
    Approved: "Aprobado", Production: "En Producción", Done: "Terminado",
    Delivered: "Entregado", Cancelled: "Cancelado",
  };
  return map[status] || status;
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" }).format(d);
}

function formatDateTime(d) {
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(d);
}

// Exponer window para el template
const window = globalThis;
</script>

<style scoped>
/* ── Reset & base ─────────────────────────────────────────────────────────── */
* { box-sizing: border-box; margin: 0; padding: 0; }

.print-wrapper {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 11pt;
  color: #111;
  background: #f5f5f5;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 24px 16px;
}

.loading-state, .error-state {
  padding: 40px;
  text-align: center;
  color: #555;
}

/* ── Página A4 ────────────────────────────────────────────────────────────── */
.ot-page {
  background: #fff;
  width: 210mm;
  min-height: 297mm;
  padding: 16mm 16mm 12mm;
  box-shadow: 0 2px 16px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2.5px solid #1a1a2e;
  padding-bottom: 10px;
  margin-bottom: 14px;
}
.company-logo {
  font-size: 20pt;
  font-weight: 900;
  letter-spacing: 2px;
  color: #1a1a2e;
}
.doc-title {
  font-size: 10pt;
  font-weight: 600;
  color: #444;
  letter-spacing: 1.5px;
  margin-top: 2px;
}
.header-right { text-align: right; }
.ot-number {
  font-size: 15pt;
  font-weight: 800;
  color: #1a1a2e;
  letter-spacing: 1px;
}
.so-number { font-size: 9pt; color: #666; margin-top: 2px; }
.status-badge {
  display: inline-block;
  margin-top: 4px;
  background: #e0e7ff;
  color: #3730a3;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* ── Info grid ───────────────────────────────────────────────────────────── */
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 14px;
  background: #f8f9fc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 12px;
}
.info-block {}
.info-label {
  font-size: 7pt;
  font-weight: 700;
  color: #8896ab;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}
.info-value {
  font-size: 10pt;
  font-weight: 600;
  color: #1a202c;
  margin-top: 2px;
}
.info-value.urgent { color: #c53030; }

/* ── Secciones ───────────────────────────────────────────────────────────── */
.section { margin-bottom: 14px; }
.section-title {
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #4a5568;
  border-bottom: 1px solid #cbd5e0;
  padding-bottom: 3px;
  margin-bottom: 7px;
}

/* ── Tags ────────────────────────────────────────────────────────────────── */
.tags-row { display: flex; flex-wrap: wrap; gap: 5px; }
.tag {
  background: #ede9fe;
  color: #5b21b6;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 8.5pt;
  font-weight: 600;
}

/* ── Items table ─────────────────────────────────────────────────────────── */
.items-table, .checklist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
}
.items-table th, .checklist-table th {
  background: #f1f5f9;
  text-align: left;
  padding: 5px 8px;
  font-size: 7.5pt;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-bottom: 1px solid #cbd5e0;
}
.items-table td, .checklist-table td {
  padding: 5px 8px;
  border-bottom: 1px solid #f0f4f8;
  vertical-align: top;
}
.col-code { width: 100px; }
.col-qty  { width: 60px; text-align: right; }
.col-check { width: 28px; text-align: center; }
.col-by   { width: 110px; color: #666; font-size: 8.5pt; }
.checkbox-cell { font-size: 12pt; }
.text-done { text-decoration: line-through; color: #9ca3af; }
tr.done td { background: #f9fafb; }

/* ── Equipo ──────────────────────────────────────────────────────────────── */
.team-list { display: flex; flex-wrap: wrap; gap: 6px; }
.team-member {
  background: #dbeafe;
  color: #1e40af;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 9pt;
  font-weight: 600;
}

/* ── Notas ───────────────────────────────────────────────────────────────── */
.notes-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 9.5pt;
  color: #78350f;
  white-space: pre-wrap;
}

/* ── Firmas ──────────────────────────────────────────────────────────────── */
.signatures {
  display: flex;
  gap: 20px;
  margin-top: auto;
  padding-top: 24px;
  margin-bottom: 12px;
}
.signature-block { flex: 1; text-align: center; }
.signature-line {
  border-bottom: 1px solid #374151;
  height: 32px;
  margin-bottom: 4px;
}
.signature-label { font-size: 7.5pt; color: #6b7280; letter-spacing: 0.5px; }

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer {
  display: flex;
  justify-content: space-between;
  font-size: 7.5pt;
  color: #9ca3af;
  border-top: 1px solid #e5e7eb;
  padding-top: 6px;
}

/* ── Acciones (no se imprimen) ───────────────────────────────────────────── */
.print-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}
.btn-print {
  background: #1a1a2e;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 11pt;
  font-weight: 600;
  cursor: pointer;
}
.btn-close {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 11pt;
  cursor: pointer;
}

/* ── Print media ─────────────────────────────────────────────────────────── */
@media print {
  .print-wrapper {
    background: #fff;
    padding: 0;
  }
  .ot-page {
    box-shadow: none;
    width: 100%;
    min-height: auto;
    padding: 10mm 12mm 8mm;
  }
  .no-print { display: none !important; }

  @page {
    size: A4 portrait;
    margin: 8mm;
  }
}
</style>
