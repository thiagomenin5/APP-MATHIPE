<template>
  <div class="min-h-full bg-slate-50">
    <!-- Encabezado -->
    <div class="mb-6 flex flex-col gap-4">
      <button
        type="button"
        class="inline-flex w-fit items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="router.back()"
      >
        <ArrowLeft class="h-4 w-4" />
        Volver
      </button>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
            #{{ order?.name || route.params.id }}
          </h1>
          <p class="mt-1 text-base text-gray-600">{{ order?.customer_name || order?.customer || "—" }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <span
            class="inline-flex rounded-xl px-4 py-2 text-lg font-semibold"
            :class="giantBadgeClass"
          >
            {{ giantBadgeLabel }}
          </span>
          <template v-if="canStartProduction">
            <button
              type="button"
              :disabled="actionLoading"
              class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-base font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-60"
              @click="runAction('start')"
            >
              <Play class="h-5 w-5" />
              {{ actionLoading ? "..." : "Iniciar Producción" }}
            </button>
          </template>
          <template v-else-if="canFinishProduction">
            <button
              type="button"
              :disabled="actionLoading"
              class="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-base font-semibold text-white shadow-md hover:bg-emerald-700 disabled:opacity-60"
              @click="runAction('finish')"
            >
              <Check class="h-5 w-5" />
              {{ actionLoading ? "..." : "Marcar Terminado" }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando orden...</p>
    </div>

    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      {{ error }}
    </div>

    <div v-else>
      <!-- Pestañas -->
      <div class="mb-4 border-b border-gray-200">
        <nav class="-mb-px flex gap-6" aria-label="Tabs">
          <button
            type="button"
            class="whitespace-nowrap border-b-2 pb-3 pt-1 text-sm font-medium transition-colors"
            :class="activeTab === 'detail'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
            @click="activeTab = 'detail'"
          >
            Detalle
          </button>
          <button
            type="button"
            class="whitespace-nowrap border-b-2 pb-3 pt-1 text-sm font-medium transition-colors flex items-center gap-1.5"
            :class="activeTab === 'ot'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
            @click="switchToOT"
          >
            <ClipboardList class="h-4 w-4" />
            Workspace OT
            <span
              v-if="wo"
              class="ml-1 inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
              :class="woStatusBadgeClass(wo.status)"
            >{{ woStatusLabel(wo.status) }}</span>
          </button>
        </nav>
      </div>

      <!-- Tab: Detalle -->
      <div v-show="activeTab === 'detail'" class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Columna izquierda: Especificaciones -->
        <div class="space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 class="mb-3 text-sm font-medium uppercase tracking-wider text-gray-500">Especificaciones</h2>
            <div class="rounded-lg bg-slate-50 p-4">
              <p class="whitespace-pre-wrap text-sm font-medium text-gray-900">{{ firstItemDescription || "—" }}</p>
            </div>
            <dl class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div>
                <dt class="text-xs font-medium uppercase tracking-wider text-gray-500">Entrega</dt>
                <dd class="mt-0.5 text-sm font-semibold text-gray-900">{{ formatDate(order?.delivery_date) }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wider text-gray-500">Cantidad</dt>
                <dd class="mt-0.5 text-sm font-semibold text-gray-900">{{ totalQty }}</dd>
              </div>
              <div>
                <dt class="text-xs font-medium uppercase tracking-wider text-gray-500">Total</dt>
                <dd class="mt-0.5 text-sm font-semibold text-gray-900">{{ formatCurrency(order?.grand_total) }}</dd>
              </div>
            </dl>
          </div>
          <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
            <div class="border-b border-gray-200 px-5 py-3">
              <h2 class="text-base font-semibold text-gray-900">Ítems</h2>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-5 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Código</th>
                    <th scope="col" class="px-5 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Descripción</th>
                    <th scope="col" class="px-5 py-2 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Cant.</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="(item, idx) in items" :key="idx">
                    <td class="whitespace-nowrap px-5 py-2 text-sm font-medium text-gray-900">{{ item.item_code }}</td>
                    <td class="px-5 py-2 text-sm text-gray-700">{{ item.description || "—" }}</td>
                    <td class="whitespace-nowrap px-5 py-2 text-right text-sm text-gray-700">{{ item.qty }}</td>
                  </tr>
                  <tr v-if="items.length === 0">
                    <td colspan="3" class="px-5 py-4 text-center text-sm text-gray-500">Sin ítems.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Columna derecha: Archivos de Producción -->
        <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 class="mb-4 text-base font-semibold text-gray-900">Archivos de Producción</h2>

          <div v-if="attachments.length > 0" class="mb-4 space-y-2">
            <div
              v-for="(file, idx) in attachments"
              :key="file.name || idx"
              class="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
            >
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                <FileText class="h-5 w-5" />
              </div>
              <span class="min-w-0 flex-1 truncate text-sm font-medium text-gray-900" :title="file.file_name">
                {{ file.file_name || "Archivo" }}
              </span>
              <a
                :href="resolveFileUrl(file.file_url)"
                target="_blank"
                rel="noopener noreferrer"
                class="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
              >
                Descargar
              </a>
            </div>
          </div>
          <p v-else class="mb-4 rounded-lg border border-amber-200 bg-amber-50 py-3 text-center text-sm text-amber-800">
            Sin archivos adjuntos
          </p>

          <div class="border-t border-gray-200 pt-4">
            <label class="mb-2 block text-sm font-medium text-gray-700">Subir archivo (Artes / Originales)</label>
            <div
              class="flex min-h-[120px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-6 transition-colors"
              :class="{ 'border-indigo-400 bg-indigo-50/50': dragOver }"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop.prevent="onDrop"
            >
              <Upload class="mb-2 h-10 w-10 text-gray-400" />
              <p class="mb-2 text-center text-sm text-gray-600">Arrastrá un archivo o hacé clic para elegir</p>
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                multiple
                @change="onFileSelect"
              />
              <button
                type="button"
                :disabled="uploading"
                class="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                @click="fileInputRef?.click()"
              >
                {{ uploading ? "Subiendo..." : "Elegir archivo" }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Workspace OT -->
      <div v-show="activeTab === 'ot'">
        <div v-if="woLoading" class="flex items-center justify-center gap-3 py-10">
          <Loader2 class="h-8 w-8 animate-spin text-indigo-600" />
          <span class="text-sm text-gray-500">Cargando OT...</span>
        </div>

        <div v-else-if="wo" class="space-y-5">
          <!-- Fase 10: aviso entrega sin factura -->
          <div
            v-if="(wo.delivery_status === 'Delivered' || wo.delivery_status === 'PickedUp') && wo.invoice_status === 'Pending'"
            class="rounded-xl border border-amber-300 bg-amber-50 p-4 flex items-center gap-3"
          >
            <AlertTriangle class="h-6 w-6 shrink-0 text-amber-600" />
            <div>
              <p class="font-semibold text-amber-900">Entrega realizada y factura pendiente</p>
              <p class="mt-0.5 text-sm text-amber-800">Esta OT está entregada pero aún no marcada como facturada. Use el tablero de Despacho para marcar como facturado cuando corresponda.</p>
            </div>
            <router-link to="/operaciones/despacho" class="ml-auto shrink-0 rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700">Ir a Despacho</router-link>
          </div>
          <!-- Header OT -->
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div class="flex items-center gap-3">
              <span class="text-xs font-medium uppercase tracking-wider text-gray-400">OT</span>
              <span class="font-mono text-sm font-bold text-gray-900">{{ wo.name }}</span>
              <span class="inline-flex rounded-lg px-3 py-1 text-sm font-semibold" :class="woStatusBadgeClass(wo.status)">
                {{ woStatusLabel(wo.status) }}
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <select
                v-model="woStatusEdit"
                class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                :disabled="woActioning"
                @change="onStatusSelectChange"
              >
                <option :value="wo?.status">{{ woStatusLabel(wo?.status) }} (actual)</option>
                <option
                  v-for="s in (wo?.valid_next_statuses || [])"
                  :key="s"
                  :value="s"
                >{{ woStatusLabel(s) }}</option>
              </select>
              <input
                v-model="woStatusComment"
                type="text"
                placeholder="Comentario (opcional)"
                class="max-w-[200px] rounded-lg border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="button"
                :disabled="woActioning || !statusChangePending"
                class="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                @click="applyStatusChange"
              >
                {{ woActioning ? "..." : "Aplicar" }}
              </button>
              <a
                :href="`/print/ot/${wo.name}`"
                target="_blank"
                class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
              >
                <Printer class="h-4 w-4" />
                Imprimir OT
              </a>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <!-- Equipo asignado -->
            <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
                <Users class="h-4 w-4 text-indigo-500" />
                Equipo asignado
              </h3>
              <!-- Chips de asignados -->
              <div class="mb-3 flex flex-wrap gap-2">
                <span
                  v-for="u in wo.assigned_users"
                  :key="u.user"
                  class="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-800"
                >
                  {{ u.full_name || u.user }}
                  <button
                    type="button"
                    class="ml-1 rounded-full p-0.5 hover:bg-indigo-200"
                    @click="removeAssignedUser(u.user)"
                  >
                    <X class="h-3 w-3" />
                  </button>
                </span>
                <span v-if="wo.assigned_users.length === 0" class="text-xs text-gray-400">Sin usuarios asignados</span>
              </div>
              <!-- Selector para agregar -->
              <select
                class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                @change="addAssignedUser($event.target.value); $event.target.value = ''"
              >
                <option value="">+ Agregar usuario...</option>
                <option
                  v-for="u in availableUsersToAdd"
                  :key="u.name"
                  :value="u.name"
                >{{ u.full_name || u.name }}</option>
              </select>
            </div>

            <!-- Etiquetas -->
            <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
                <Tag class="h-4 w-4 text-purple-500" />
                Etiquetas
              </h3>
              <!-- Chips de tags -->
              <div class="mb-3 flex flex-wrap gap-2">
                <span
                  v-for="tag in wo.tags"
                  :key="tag"
                  class="inline-flex items-center gap-1 rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-800"
                >
                  {{ tag }}
                  <button type="button" class="ml-1 rounded-full p-0.5 hover:bg-purple-200" @click="removeTag(tag)">
                    <X class="h-3 w-3" />
                  </button>
                </span>
                <span v-if="wo.tags.length === 0" class="text-xs text-gray-400">Sin etiquetas</span>
              </div>
              <!-- Input para agregar tag -->
              <div class="flex gap-2">
                <input
                  v-model="newTagInput"
                  type="text"
                  placeholder="Nueva etiqueta..."
                  class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  @keydown.enter.prevent="addTag"
                />
                <button
                  type="button"
                  class="rounded-lg bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700"
                  @click="addTag"
                >
                  +
                </button>
              </div>
              <!-- Sugerencias rápidas -->
              <div class="mt-2 flex flex-wrap gap-1.5">
                <button
                  v-for="sug in tagSuggestions.filter(s => !wo.tags.includes(s))"
                  :key="sug"
                  type="button"
                  class="rounded-full border border-dashed border-purple-300 px-2.5 py-0.5 text-xs text-purple-600 hover:border-purple-500 hover:bg-purple-50"
                  @click="addTagDirect(sug)"
                >
                  {{ sug }}
                </button>
              </div>
            </div>
          </div>

          <!-- Ítems / Tercerización -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h3 class="flex items-center gap-2 text-sm font-semibold text-gray-900">
                <Package class="h-4 w-4 text-slate-500" />
                Ítems / Tercerización
              </h3>
              <button
                v-if="wo?.name && (wo?.items || []).length > 0"
                type="button"
                :disabled="woActioning"
                class="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                title="Re-sincronizar ítems desde la cotización (solo admin)"
                @click="resyncWoItemsFromQuote"
              >
                Resync desde cotización
              </button>
            </div>
            <div v-if="(wo?.items || []).length === 0" class="py-4 text-center text-sm text-gray-500">
              Sin ítems en esta OT (se cargan al convertir desde la cotización).
            </div>
            <div v-else class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Descripción</th>
                    <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500">Cant.</th>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Tercerizar</th>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Proveedor</th>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Estado</th>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Acciones</th>
                    <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Costo / Notas</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="(it, idx) in wo.items" :key="it.name || idx" class="align-top">
                    <td class="px-3 py-2">
                      <span class="font-medium text-gray-900">{{ it.description || it.item_code || "—" }}</span>
                      <span v-if="it.width || it.height" class="ml-1 text-xs text-gray-500">{{ it.width }}×{{ it.height }} mm</span>
                      <span v-if="it.quote_item" class="block mt-0.5 text-[10px] text-gray-400" :title="'Quote Item: ' + it.quote_item">Origen: {{ it.quote_item }}</span>
                    </td>
                    <td class="px-3 py-2 text-right text-gray-700">{{ it.qty }}</td>
                    <td class="px-3 py-2">
                      <input
                        type="checkbox"
                        :checked="it.is_outsourced"
                        class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        @change="toggleOutsourced(it, $event.target.checked)"
                      />
                      <p v-if="it.is_outsourced && !it.supplier" class="mt-0.5 text-xs text-amber-600">Proveedor obligatorio</p>
                    </td>
                    <td class="px-3 py-2">
                      <input
                        v-model="itemPatch[it.name].supplier"
                        type="text"
                        placeholder="Proveedor"
                        class="w-32 rounded border border-gray-300 px-2 py-1 text-xs focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                        @blur="saveItemPatch(it, 'supplier')"
                      />
                    </td>
                    <td class="px-3 py-2">
                      <span
                        v-if="it.is_outsourced"
                        class="inline-flex rounded px-2 py-0.5 text-xs font-medium"
                        :class="outsourceStatusClass(it.outsource_status)"
                      >{{ outsourceStatusLabel(it.outsource_status) }}</span>
                      <span v-else class="text-gray-400">—</span>
                    </td>
                    <td class="px-3 py-2">
                      <template v-if="it.is_outsourced">
                        <button
                          v-if="it.outsource_status === 'PendingVendor'"
                          type="button"
                          :disabled="woActioning || !it.supplier"
                          class="mr-1 rounded bg-amber-500 px-2 py-1 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                          @click="setOutsourceStatus(it, 'sent')"
                        >
                          Marcar Enviado
                        </button>
                        <button
                          v-if="it.outsource_status === 'Sent' || it.outsource_status === 'PendingVendor'"
                          type="button"
                          :disabled="woActioning"
                          class="rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                          @click="setOutsourceStatus(it, 'received')"
                        >
                          Marcar Recibido
                        </button>
                      </template>
                    </td>
                    <td class="px-3 py-2">
                      <input
                        v-model="itemPatch[it.name].outsource_cost"
                        type="number"
                        step="0.01"
                        placeholder="Costo"
                        class="mb-1 w-20 rounded border border-gray-300 px-2 py-1 text-xs focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                        @blur="saveItemPatch(it, 'outsource_cost')"
                      />
                      <input
                        v-model="itemPatch[it.name].outsource_notes"
                        type="text"
                        placeholder="Notas"
                        class="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                        @blur="saveItemPatch(it, 'outsource_notes')"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Panel Alertas (Fase 5) -->
          <div v-if="wo && (wo.alerts_summary?.danger || wo.alerts_summary?.warning || wo.alerts_summary?.info)" class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <AlertTriangle class="h-4 w-4 text-amber-500" />
              Alertas
            </h3>
            <div class="mb-3 flex flex-wrap gap-2">
              <span v-if="wo.alerts_summary.danger" class="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800">
                {{ wo.alerts_summary.danger }} peligro
              </span>
              <span v-if="wo.alerts_summary.warning" class="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
                {{ wo.alerts_summary.warning }} advertencia
              </span>
              <span v-if="wo.alerts_summary.info" class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                {{ wo.alerts_summary.info }} info
              </span>
            </div>
            <ul class="space-y-2">
              <li
                v-for="(a, idx) in (wo.alerts || [])"
                :key="idx"
                class="flex items-start gap-2 rounded-lg border p-2 text-sm"
                :class="a.level === 'danger' ? 'border-red-200 bg-red-50' : a.level === 'warning' ? 'border-amber-200 bg-amber-50' : 'border-blue-200 bg-blue-50'"
              >
                <span class="font-medium">{{ a.title }}</span>
                <span class="text-gray-600">— {{ a.message }}</span>
              </li>
            </ul>
            <div class="mt-3">
              <router-link
                to="/admin/alertas"
                class="inline-flex items-center gap-1.5 rounded border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
              >
                Ver en Alertas
              </router-link>
            </div>
          </div>

          <!-- Resumen Financiero (Fase 3) -->
          <div v-if="wo" class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <BarChart2 class="h-4 w-4 text-indigo-500" />
              Resumen Financiero
            </h3>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div class="rounded-lg bg-gray-50 p-3">
                <p class="text-xs text-gray-500">Total Venta</p>
                <p class="mt-1 text-base font-semibold text-gray-900">{{ formatCurrency(wo.revenue_total) }}</p>
              </div>
              <div class="rounded-lg bg-gray-50 p-3">
                <p class="text-xs text-gray-500">Costo Estimado</p>
                <p class="mt-1 text-base font-semibold text-gray-900">{{ formatCurrency(wo.estimated_cost_total) }}</p>
              </div>
              <div class="rounded-lg bg-gray-50 p-3">
                <p class="text-xs text-gray-500">Costo Real</p>
                <p class="mt-1 text-base font-semibold text-gray-900">{{ formatCurrency(wo.real_cost_total) }}</p>
              </div>
              <div class="rounded-lg bg-gray-50 p-3">
                <p class="text-xs text-gray-500">Margen Bruto</p>
                <p class="mt-1 text-base font-semibold text-gray-900">{{ formatCurrency(wo.gross_margin) }}</p>
              </div>
            </div>
            <div class="mt-3">
              <div
                class="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold"
                :class="marginColorClass"
              >
                <TrendingUp class="h-4 w-4" />
                Margen {{ (wo.gross_margin_pct || 0).toFixed(1) }}%
              </div>
            </div>
          </div>

          <!-- Checklist -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <CheckSquare class="h-4 w-4 text-emerald-500" />
              Checklist de control
            </h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in wo.checklist_items"
                :key="item.name || idx"
                class="flex items-start gap-3 rounded-lg p-2 transition-colors hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  :checked="item.done"
                  class="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  @change="toggleChecklistItem(idx, $event.target.checked)"
                />
                <span
                  class="flex-1 text-sm"
                  :class="item.done ? 'text-gray-400 line-through' : 'text-gray-900'"
                >{{ item.title }}</span>
                <span v-if="item.done && item.done_by" class="text-xs text-gray-400">
                  {{ item.done_by }}
                </span>
                <button
                  type="button"
                  class="text-gray-400 hover:text-red-500"
                  @click="removeChecklistItem(idx)"
                >
                  <X class="h-3.5 w-3.5" />
                </button>
              </div>
              <div v-if="wo.checklist_items.length === 0" class="py-4 text-center text-sm text-gray-400">
                Sin tareas en el checklist
              </div>
            </div>
            <!-- Agregar tarea -->
            <div class="mt-3 flex gap-2 border-t border-gray-100 pt-3">
              <input
                v-model="newChecklistTitle"
                type="text"
                placeholder="Nueva tarea..."
                class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                @keydown.enter.prevent="addChecklistItem"
              />
              <button
                type="button"
                class="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                @click="addChecklistItem"
              >
                +
              </button>
            </div>
          </div>

          <!-- Aprobación cliente -->
          <div class="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
            <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-900">
              <Send class="h-4 w-4" />
              Aprobación del cliente
            </h3>
            <div class="mb-3 flex items-center gap-2">
              <span class="text-xs font-medium text-amber-700">Estado actual:</span>
              <span class="inline-flex rounded-lg px-2.5 py-1 text-xs font-semibold" :class="woStatusBadgeClass(wo.status)">
                {{ woStatusLabel(wo.status) }}
              </span>
            </div>
            <div v-if="wo.status !== 'Approved' && wo.status !== 'Done' && wo.status !== 'Delivered'" class="space-y-3">
              <textarea
                v-model="approvalMessage"
                rows="2"
                placeholder="Mensaje para el cliente (opcional)..."
                class="w-full rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  :disabled="woActioning"
                  class="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-60"
                  @click="requestApproval"
                >
                  <Send class="h-4 w-4" />
                  Pedir OK al cliente
                </button>
                <button
                  type="button"
                  :disabled="woActioning"
                  class="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
                  @click="approveOT"
                >
                  <Check class="h-4 w-4" />
                  Aprobar
                </button>
              </div>
            </div>
            <div v-else class="rounded-lg bg-emerald-100 px-4 py-3 text-sm font-medium text-emerald-800">
              Orden aprobada / finalizada. Sin acciones de aprobación pendientes.
            </div>
          </div>

          <!-- Historial de estado -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <ClipboardList class="h-4 w-4 text-gray-500" />
              Historial de estado
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Fecha</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Usuario</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">De → A</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Comentario</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="(entry, idx) in (wo?.status_log || [])" :key="idx">
                    <td class="whitespace-nowrap px-3 py-2 text-gray-600">{{ formatDateTime(entry.changed_at) }}</td>
                    <td class="whitespace-nowrap px-3 py-2 text-gray-900">{{ entry.changed_by }}</td>
                    <td class="whitespace-nowrap px-3 py-2">
                      <span class="text-gray-500">{{ woStatusLabel(entry.from_status) }}</span>
                      <span class="mx-1 text-gray-400">→</span>
                      <span class="font-medium text-gray-900">{{ woStatusLabel(entry.to_status) }}</span>
                    </td>
                    <td class="px-3 py-2 text-gray-600">{{ entry.comment || "—" }}</td>
                  </tr>
                  <tr v-if="!(wo?.status_log || []).length">
                    <td colspan="4" class="px-3 py-4 text-center text-gray-500">Sin cambios de estado aún.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Ruta de Producción (Fase 9) -->
          <div v-if="wo" class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <ClipboardList class="h-4 w-4 text-indigo-500" />
              Ruta de Producción
              <span v-if="wo.current_sector" class="ml-2 rounded bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800">Sector actual: {{ wo.current_sector }}</span>
            </h3>
            <div v-if="(wo.stages || []).length" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Orden</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Sector</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Estado</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Asignado</th>
                    <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Iniciado / Finalizado</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="s in (wo.stages || [])" :key="s.name">
                    <td class="whitespace-nowrap px-3 py-2 text-gray-600">{{ s.idx }}</td>
                    <td class="whitespace-nowrap px-3 py-2 font-medium text-gray-900">{{ s.sector_name || s.sector_key || "—" }}</td>
                    <td class="px-3 py-2">
                      <span
                        class="inline-flex rounded px-2 py-0.5 text-xs font-medium"
                        :class="stageStatusClass(s.stage_status)"
                      >{{ s.stage_status || "—" }}</span>
                    </td>
                    <td class="whitespace-nowrap px-3 py-2 text-gray-600">{{ s.assigned_to || "—" }}</td>
                    <td class="whitespace-nowrap px-3 py-2 text-gray-600 text-xs">
                      {{ s.started_at ? formatDateTime(s.started_at) : "—" }}
                      <span v-if="s.finished_at"> / {{ formatDateTime(s.finished_at) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="py-4 text-center text-sm text-gray-500">
              Sin etapas. La ruta se crea al pasar la OT a Producción.
            </p>
            <div v-if="(wo.stages || []).length" class="mt-3 border-t border-gray-200 pt-3">
              <p class="mb-2 text-xs text-gray-500">Historial por etapa</p>
              <ul class="max-h-32 overflow-y-auto space-y-1 text-xs text-gray-600">
                <li v-for="(entry, idx) in (wo.stage_log || [])" :key="idx">
                  {{ formatDateTime(entry.changed_at) }} — {{ entry.sector_key }}: {{ entry.from_status }} → {{ entry.to_status }} ({{ entry.changed_by }})
                </li>
                <li v-if="!(wo.stage_log || []).length">Sin cambios de etapa aún.</li>
              </ul>
            </div>
            <div class="mt-4">
              <button
                type="button"
                :disabled="woActioning"
                class="rounded border border-amber-600 px-3 py-1.5 text-sm font-medium text-amber-800 hover:bg-amber-50 disabled:opacity-50"
                @click="regenerateStages"
              >
                Reiniciar / Regenerar Ruta
              </button>
              <span class="ml-2 text-xs text-gray-500">Solo Gerencia o System Manager</span>
            </div>
          </div>

          <!-- Notas -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 class="mb-3 text-sm font-semibold text-gray-900">Notas internas</h3>
            <textarea
              v-model="woNotesEdit"
              rows="3"
              placeholder="Notas para el equipo..."
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="button"
              :disabled="woActioning"
              class="mt-2 rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-60"
              @click="saveNotes"
            >
              Guardar notas
            </button>
          </div>
        </div>
      </div>
    </div>

    <Transition name="toast">
      <div
        v-if="toastVisible"
        class="fixed bottom-6 left-1/2 z-50 min-w-[280px] -translate-x-1/2 rounded-xl px-5 py-4 text-center text-base font-medium text-white shadow-lg"
        :class="toastError ? 'bg-red-600' : 'bg-emerald-600'"
        role="alert"
      >
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft, Play, Check, Loader2, FileText, Upload,
  ClipboardList, Users, Tag, CheckSquare, X, Send, Printer, Package,
  BarChart2, TrendingUp, AlertTriangle,
} from "lucide-vue-next";
import { call, uploadFile } from "@/api/frappe";

const route = useRoute();
const router = useRouter();

// ── Estado principal ──────────────────────────────────────────────────────────
const loading = ref(true);
const error = ref(null);
const data = ref(null);
const actionLoading = ref(false);
const uploading = ref(false);
const dragOver = ref(false);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);
const fileInputRef = ref(null);
const activeTab = ref("detail");

// ── Estado OT ─────────────────────────────────────────────────────────────────
const wo = ref(null);
const woLoading = ref(false);
const woActioning = ref(false);
const woStatusEdit = ref("New");
const woStatusComment = ref("");
const woNotesEdit = ref("");
const newTagInput = ref("");
const itemPatch = ref({});
const newChecklistTitle = ref("");
const approvalMessage = ref("");
const systemUsers = ref([]);

const tagSuggestions = ["Express", "Instalación", "Zona Norte", "Zona Sur", "Revisión", "Urgente"];

// ── Computed del pedido ───────────────────────────────────────────────────────
const order = computed(() => data.value?.order ?? null);
const items = computed(() => data.value?.items ?? []);
const attachments = computed(() => data.value?.attachments ?? data.value?.files ?? []);
const tags = computed(() => data.value?.tags ?? []);

const firstItemDescription = computed(() => items.value[0]?.description || "—");
const totalQty = computed(() => items.value.reduce((s, i) => s + (Number(i.qty) || 0), 0) || "—");

const canStartProduction = computed(() => !tags.value.includes("En Producción") && !tags.value.includes("Terminado"));
const canFinishProduction = computed(() => tags.value.includes("En Producción"));
const isOrderFinished = computed(() => tags.value.includes("Terminado"));

const giantBadgeClass = computed(() => {
  if (isOrderFinished.value) return "bg-emerald-100 text-emerald-800";
  if (tags.value.includes("En Producción")) return "bg-blue-100 text-blue-800";
  return "bg-amber-100 text-amber-800";
});
const giantBadgeLabel = computed(() => {
  if (isOrderFinished.value) return "Finalizado";
  if (tags.value.includes("En Producción")) return "En Producción";
  return "Pendiente";
});

// ── Computed OT ───────────────────────────────────────────────────────────────
const marginColorClass = computed(() => {
  const pct = wo.value?.gross_margin_pct || 0;
  if (pct > 30) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (pct >= 15) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-red-50 text-red-700 border-red-200";
});

const availableUsersToAdd = computed(() => {
  const assigned = new Set((wo.value?.assigned_users || []).map(u => u.user));
  return systemUsers.value.filter(u => !assigned.has(u.name));
});

const statusChangePending = computed(() => {
  const current = wo.value?.status;
  const selected = woStatusEdit.value;
  if (!current || !selected || selected === current) return false;
  const allowed = wo.value?.valid_next_statuses || [];
  return allowed.includes(selected);
});

watch(
  () => wo.value?.items,
  (items) => {
    if (!items?.length) return;
    const p = { ...itemPatch.value };
    items.forEach(i => {
      if (!p[i.name]) p[i.name] = { supplier: i.supplier ?? "", outsource_cost: i.outsource_cost ?? "", outsource_notes: i.outsource_notes ?? "" };
    });
    itemPatch.value = p;
  },
  { immediate: true, deep: true }
);

// ── Fetch datos ───────────────────────────────────────────────────────────────
async function fetchOrder() {
  const id = route.params.id;
  if (!id) return;
  try {
    const res = await call("mathipe_ui.api.get_order_details", { order_id: id });
    data.value = res?.message ?? res ?? null;
    if (!data.value?.order) error.value = "No se encontró la orden.";
    else error.value = null;
  } catch (e) {
    error.value = e.message || "Error al cargar la orden.";
    data.value = null;
  }
}

async function fetchSystemUsers() {
  try {
    const res = await call("mathipe_ui.api.get_system_users", {});
    systemUsers.value = res?.message ?? res ?? [];
  } catch (_) { /* no crítico */ }
}

async function fetchOrCreateWO() {
  const id = route.params.id;
  if (!id) return;
  woLoading.value = true;
  try {
    const res = await call("mathipe_ui.api.create_or_get_work_order", { sales_order_id: id });
    const detail = res?.message ?? res ?? null;
    wo.value = detail;
    if (detail) {
      woStatusEdit.value = detail.status;
      woStatusComment.value = "";
      woNotesEdit.value = detail.notes || "";
      const items = detail.items || [];
      const patch = {};
      items.forEach(i => {
        patch[i.name] = {
          supplier: i.supplier ?? "",
          outsource_cost: i.outsource_cost ?? "",
          outsource_notes: i.outsource_notes ?? "",
        };
      });
      itemPatch.value = patch;
    }
  } catch (e) {
    showToast("Error al cargar OT: " + (e.message || ""), true);
  } finally {
    woLoading.value = false;
  }
}

// ── Cambio de pestaña ─────────────────────────────────────────────────────────
async function switchToOT() {
  activeTab.value = "ot";
  if (!wo.value) {
    await Promise.all([fetchOrCreateWO(), fetchSystemUsers()]);
  } else if (systemUsers.value.length === 0) {
    fetchSystemUsers();
  }
}

// ── Acciones de pedido (producción) ──────────────────────────────────────────
onMounted(async () => {
  const id = route.params.id;
  if (!id) { error.value = "Falta el ID de la orden."; loading.value = false; return; }
  loading.value = true;
  await fetchOrder();
  loading.value = false;
});

async function runAction(action) {
  const id = route.params.id;
  if (!id || actionLoading.value) return;
  actionLoading.value = true;
  try {
    await call("mathipe_ui.api.update_production_status", { order_id: id, action });
    await fetchOrder();
    showToast(action === "start" ? "Producción iniciada." : "Marcado como terminado.");
  } catch (e) {
    showToast(e.message || "Error al actualizar.", true);
  } finally {
    actionLoading.value = false;
  }
}

// ── Archivos ──────────────────────────────────────────────────────────────────
function onFileSelect(ev) {
  const input = ev.target;
  if (input?.files?.length) handleFiles(Array.from(input.files));
  input.value = "";
}
function onDrop(ev) {
  dragOver.value = false;
  if (ev.dataTransfer?.files?.length) handleFiles(Array.from(ev.dataTransfer.files));
}
async function handleFiles(fileList) {
  const id = route.params.id;
  if (!id || uploading.value) return;
  uploading.value = true;
  let ok = 0; let err = null;
  for (const file of fileList) {
    try { await uploadFile(file, { doctype: "Sales Order", docname: id }); ok++; }
    catch (e) { err = e.message || "Error al subir"; }
  }
  uploading.value = false;
  if (ok > 0) { await fetchOrder(); showToast(ok === fileList.length ? "Archivo(s) subidos." : `${ok} subido(s). ${err || ""}`); }
  else if (err) showToast(err, true);
}
function resolveFileUrl(fileUrl) {
  if (!fileUrl) return "#";
  if (fileUrl.startsWith("http://") || fileUrl.startsWith("https://")) return fileUrl;
  return fileUrl.startsWith("/") ? `${window.location.origin}${fileUrl}` : `${window.location.origin}/${fileUrl}`;
}

// ── OT: Status ────────────────────────────────────────────────────────────────
function onStatusSelectChange() {
  // Solo habilita "Aplicar" cuando statusChangePending es true
}

async function applyStatusChange() {
  if (!wo.value || woActioning.value || !statusChangePending.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_status", {
      work_order_id: wo.value.name,
      to_status: woStatusEdit.value,
      comment: woStatusComment.value?.trim() || null,
    });
    wo.value = res?.message ?? res;
    woStatusEdit.value = wo.value.status;
    woStatusComment.value = "";
    showToast("Estado actualizado.");
  } catch (e) {
    showToast(e.message || "Error al cambiar estado.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Usuarios ─────────────────────────────────────────────────────────────
async function addAssignedUser(userId) {
  if (!userId || !wo.value) return;
  const current = wo.value.assigned_users.map(u => u.user);
  if (current.includes(userId)) return;
  await saveAssignments([...current, userId]);
}
async function removeAssignedUser(userId) {
  if (!wo.value) return;
  const current = wo.value.assigned_users.map(u => u.user).filter(u => u !== userId);
  await saveAssignments(current);
}
async function saveAssignments(userIds) {
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_assignments", {
      work_order_id: wo.value.name,
      user_ids: userIds,
    });
    wo.value = res?.message ?? res;
    showToast("Equipo actualizado.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Etiquetas ─────────────────────────────────────────────────────────────
async function addTag() {
  const tag = newTagInput.value.trim();
  if (!tag || !wo.value) return;
  newTagInput.value = "";
  await saveTags([...wo.value.tags, tag]);
}
async function addTagDirect(tag) {
  if (!wo.value || wo.value.tags.includes(tag)) return;
  await saveTags([...wo.value.tags, tag]);
}
async function removeTag(tag) {
  if (!wo.value) return;
  await saveTags(wo.value.tags.filter(t => t !== tag));
}
async function saveTags(tags) {
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_tags", {
      work_order_id: wo.value.name,
      tags,
    });
    wo.value = res?.message ?? res;
    showToast("Etiquetas guardadas.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Checklist ─────────────────────────────────────────────────────────────
async function addChecklistItem() {
  const title = newChecklistTitle.value.trim();
  if (!title || !wo.value) return;
  newChecklistTitle.value = "";
  const items = [...wo.value.checklist_items, { title, done: false }];
  await saveChecklist(items);
}
async function toggleChecklistItem(idx, done) {
  if (!wo.value) return;
  const items = wo.value.checklist_items.map((it, i) => i === idx ? { ...it, done } : it);
  await saveChecklist(items);
}
async function removeChecklistItem(idx) {
  if (!wo.value) return;
  const items = wo.value.checklist_items.filter((_, i) => i !== idx);
  await saveChecklist(items);
}
async function saveChecklist(checklist_items) {
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_checklist", {
      work_order_id: wo.value.name,
      checklist_items,
    });
    wo.value = res?.message ?? res;
  } catch (e) {
    showToast(e.message || "Error al guardar checklist.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Aprobación ────────────────────────────────────────────────────────────
async function requestApproval() {
  if (!wo.value || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.request_client_approval", {
      work_order_id: wo.value.name,
      message: approvalMessage.value,
    });
    wo.value = res?.message ?? res;
    woStatusEdit.value = wo.value.status;
    approvalMessage.value = "";
    showToast("Solicitud enviada. Estado: Esperando OK.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}
async function approveOT() {
  if (!wo.value || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.approve_work_order", {
      work_order_id: wo.value.name,
      comment: approvalMessage.value,
    });
    wo.value = res?.message ?? res;
    woStatusEdit.value = wo.value.status;
    approvalMessage.value = "";
    showToast("OT aprobada.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Notas ─────────────────────────────────────────────────────────────────
async function saveNotes() {
  if (!wo.value || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_notes", {
      work_order_id: wo.value.name,
      notes: woNotesEdit.value,
    });
    wo.value = res?.message ?? res;
    showToast("Notas guardadas.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Ítems / Tercerización ─────────────────────────────────────────────────
function outsourceStatusLabel(s) {
  const map = { PendingVendor: "Pend. proveedor", Sent: "Enviado", Received: "Recibido" };
  return map[s] || s || "—";
}
function outsourceStatusClass(s) {
  const map = {
    PendingVendor: "bg-amber-100 text-amber-800",
    Sent: "bg-blue-100 text-blue-800",
    Received: "bg-emerald-100 text-emerald-800",
  };
  return map[s] || "bg-gray-100 text-gray-700";
}
async function toggleOutsourced(it, checked) {
  if (!wo.value || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_item", {
      work_order_id: wo.value.name,
      item_row_id: it.name,
      patch_fields: { is_outsourced: checked, supplier: itemPatch.value[it.name]?.supplier || null },
    });
    wo.value = res?.message ?? res;
    if (res?.message?.items) {
      const patch = { ...itemPatch.value };
      res.message.items.forEach(i => {
        if (!patch[i.name]) patch[i.name] = {};
        patch[i.name].supplier = i.supplier ?? "";
        patch[i.name].outsource_cost = i.outsource_cost ?? "";
        patch[i.name].outsource_notes = i.outsource_notes ?? "";
      });
      itemPatch.value = patch;
    }
    showToast(checked ? "Ítem marcado como tercerizado." : "Tercerización desactivada.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}
async function saveItemPatch(it, field) {
  if (!wo.value || woActioning.value) return;
  const p = itemPatch.value[it.name];
  if (!p) return;
  const val = p[field];
  const payload = { is_outsourced: it.is_outsourced, supplier: p.supplier || null, outsource_cost: p.outsource_cost || null, outsource_notes: p.outsource_notes || null };
  if (field === "outsource_cost") payload.outsource_cost = val ? parseFloat(val) : null;
  else if (field === "outsource_notes") payload.outsource_notes = val || null;
  else if (field === "supplier") payload.supplier = val || null;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_work_order_item", {
      work_order_id: wo.value.name,
      item_row_id: it.name,
      patch_fields: payload,
    });
    wo.value = res?.message ?? res;
    showToast("Ítem actualizado.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}
async function setOutsourceStatus(it, action) {
  if (!wo.value || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.update_outsource_status", {
      work_order_id: wo.value.name,
      item_row_id: it.name,
      action,
    });
    wo.value = res?.message ?? res;
    showToast(action === "sent" ? "Marcado como Enviado." : "Marcado como Recibido.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

async function resyncWoItemsFromQuote() {
  if (!wo.value?.name || woActioning.value) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.resync_work_order_items_from_quote", {
      work_order_id: wo.value.name,
    });
    wo.value = res?.message ?? res;
    showToast("Ítems re-sincronizados desde la cotización.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── OT: Helpers visuales ──────────────────────────────────────────────────────
function woStatusLabel(status) {
  const map = {
    New: "Nuevo", Design: "Diseño", WaitingApproval: "Esperando OK",
    Approved: "Aprobado", Production: "Producción", Done: "Terminado",
    Delivered: "Entregado", Cancelled: "Cancelado",
  };
  return map[status] || status;
}
function woStatusBadgeClass(status) {
  const map = {
    New: "bg-gray-100 text-gray-700",
    Design: "bg-indigo-100 text-indigo-800",
    WaitingApproval: "bg-amber-100 text-amber-800",
    Approved: "bg-emerald-100 text-emerald-800",
    Production: "bg-blue-100 text-blue-800",
    Done: "bg-green-100 text-green-800",
    Delivered: "bg-teal-100 text-teal-800",
    Cancelled: "bg-red-100 text-red-700",
  };
  return map[status] || "bg-gray-100 text-gray-700";
}

function stageStatusClass(stageStatus) {
  const s = (stageStatus || "").toLowerCase();
  if (s === "done" || s === "skipped") return "bg-emerald-100 text-emerald-800";
  if (s === "in progress") return "bg-blue-100 text-blue-800";
  return "bg-amber-100 text-amber-800";
}

async function regenerateStages() {
  if (!wo.value?.name || woActioning.value) return;
  if (!confirm("¿Regenerar la ruta de producción? Solo tiene efecto si la OT aún no tiene etapas. ¿Continuar?")) return;
  woActioning.value = true;
  try {
    const res = await call("mathipe_ui.api.init_wo_stages_from_template", {
      work_order_id: wo.value.name,
    });
    wo.value = res?.message ?? res;
    showToast("Ruta actualizada.");
  } catch (e) {
    showToast(e.message || "Error.", true);
  } finally {
    woActioning.value = false;
  }
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => { toastVisible.value = false; }, 3000);
}

// ── Formateadores ─────────────────────────────────────────────────────────────
function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
}
function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" }).format(d);
}
function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}
</style>
