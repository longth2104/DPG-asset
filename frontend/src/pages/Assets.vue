<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-6xl mx-auto w-full">
      <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 class="text-2xl font-bold tracking-tight">{{ $t('assets.title') }}</h1>
        <router-link
          v-if="auth.isAssetManager"
          to="/assets/new"
          class="bg-brand hover:opacity-90 text-white text-sm font-semibold px-4 py-2 rounded transition-opacity"
        >
          {{ $t('assets.newAsset') }}
        </router-link>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <input
          v-model="search"
          :placeholder="$t('assets.search')"
          class="lg:col-span-2 bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded focus:outline-none focus:border-primary"
        />
        <select v-model="departmentFilter" class="bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded">
          <option value="">{{ $t('assets.filters.department') }} — {{ $t('assets.filters.all') }}</option>
          <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="categoryFilter" class="bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded">
          <option value="">{{ $t('assets.filters.category') }} — {{ $t('assets.filters.all') }}</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="statusFilter" class="bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded">
          <option value="">{{ $t('assets.filters.status') }} — {{ $t('assets.filters.all') }}</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ $t(`assets.status.${s}`) }}</option>
        </select>
      </div>

      <div class="flex items-center gap-2 mb-6 flex-wrap">
        <span v-if="selectedIds.size" class="text-sm text-white/80 mr-1">
          {{ $t('assets.io.selected', { count: selectedIds.size }) }}
        </span>
        <button
          @click="exportAssets('xlsx')"
          :disabled="exporting"
          class="bg-white text-gray-900 hover:bg-gray-100 disabled:opacity-50 text-sm font-semibold px-3 py-1.5 rounded transition-colors"
        >
          {{ $t('assets.io.exportExcel') }}
        </button>
        <button
          @click="exportAssets('pdf')"
          :disabled="exporting"
          class="bg-white text-gray-900 hover:bg-gray-100 disabled:opacity-50 text-sm font-semibold px-3 py-1.5 rounded transition-colors"
        >
          {{ $t('assets.io.exportPdf') }}
        </button>
        <label
          v-if="auth.isAssetManager"
          class="bg-white text-gray-900 hover:bg-gray-100 text-sm font-semibold px-3 py-1.5 rounded transition-colors cursor-pointer"
        >
          {{ importing ? $t('assets.io.importing') : $t('assets.io.import') }}
          <input type="file" accept=".xlsx" class="hidden" :disabled="importing" @change="onImportPick" />
        </label>

        <template v-if="auth.isAssetManager">
          <span class="w-px self-stretch bg-white/20 mx-1" />
          <button
            @click="deleteSelected"
            :disabled="!selectedIds.size || deleting"
            class="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-semibold px-3 py-1.5 rounded transition-colors"
          >
            {{ $t('assets.io.deleteSelected') }}
          </button>
          <button
            @click="deleteAll"
            :disabled="!filtered.length || deleting"
            class="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-semibold px-3 py-1.5 rounded transition-colors"
          >
            {{ $t('assets.io.deleteAll') }}
          </button>
        </template>

        <template v-if="auth.isAdmin">
          <span class="w-px self-stretch bg-white/20 mx-1" />
          <button
            @click="syncRds"
            :disabled="syncing"
            class="bg-white text-gray-900 hover:bg-gray-100 disabled:opacity-50 text-sm font-semibold px-3 py-1.5 rounded transition-colors"
          >
            {{ syncing ? $t('assets.io.syncing') : $t('assets.io.syncRds') }}
          </button>
        </template>
      </div>

      <div
        v-if="syncResult"
        class="bg-white text-gray-900 border border-gray-200 rounded p-4 mb-6 text-sm flex items-start justify-between gap-3"
      >
        <p>
          {{ $t('assets.io.syncResult', { created: syncResult.created, updated: syncResult.updated }) }}
          <span v-if="syncResult.unmapped_companies.length">
            — {{ $t('assets.io.syncUnmapped', { codes: syncResult.unmapped_companies.join(', ') }) }}
          </span>
        </p>
        <button @click="syncResult = null" class="text-gray-400 hover:text-gray-600 text-xs">✕</button>
      </div>
      <div
        v-if="syncError"
        class="bg-white text-gray-900 border border-red-300 rounded p-4 mb-6 text-sm flex items-start justify-between gap-3"
      >
        <p class="text-red-600">{{ $t(syncError) }}</p>
        <button @click="syncError = ''" class="text-gray-400 hover:text-gray-600 text-xs">✕</button>
      </div>

      <div
        v-if="deleteError"
        class="bg-white text-gray-900 border border-red-300 rounded p-4 mb-6 text-sm flex items-start justify-between gap-3"
      >
        <p class="text-red-600">{{ $t(deleteError) }}</p>
        <button @click="deleteError = ''" class="text-gray-400 hover:text-gray-600 text-xs">✕</button>
      </div>

      <div
        v-if="importResult"
        class="bg-white text-gray-900 border border-gray-200 rounded p-4 mb-6 text-sm"
      >
        <div class="flex items-start justify-between gap-3">
          <p>
            {{ $t('assets.io.importResult', { imported: importResult.imported, skipped: importResult.skipped }) }}
          </p>
          <button @click="importResult = null" class="text-gray-400 hover:text-gray-600 text-xs">✕</button>
        </div>
        <div v-if="importResult.errors.length" class="mt-2">
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
            {{ $t('assets.io.errorsHeader') }}
          </p>
          <ul class="text-xs text-red-600 space-y-0.5">
            <li v-for="(e, i) in importResult.errors" :key="i">
              {{ $t('assets.io.rowError', { row: e.row, reason: e.reason }) }}
            </li>
          </ul>
        </div>
      </div>

      <div
        v-if="importError"
        class="bg-white text-gray-900 border border-red-300 rounded p-4 mb-6 text-sm flex items-start justify-between gap-3"
      >
        <p class="text-red-600">{{ $t(importError) }}</p>
        <button @click="importError = ''" class="text-gray-400 hover:text-gray-600 text-xs">✕</button>
      </div>

      <div v-if="store.loading" class="space-y-2">
        <div v-for="i in 8" :key="i" class="h-12 bg-white/10 rounded animate-pulse" />
      </div>

      <div v-else-if="!filtered.length" class="text-muted text-sm">{{ $t('common.noResults') }}</div>

      <div v-else class="bg-white text-gray-900 border border-gray-200 rounded overflow-hidden overflow-x-auto">
        <table class="w-full text-sm min-w-[720px]">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3 w-10">
                <input type="checkbox" :checked="allSelected" @change="toggleAll" @click.stop />
              </th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.code') }}</th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.name') }}</th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.category') }}</th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.department') }}</th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.holder') }}</th>
              <th class="text-left px-4 py-3">{{ $t('assets.columns.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in filtered"
              :key="a.id"
              class="border-b border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer"
              @click="$router.push(`/assets/${a.id}`)"
            >
              <td class="px-4 py-3" @click.stop>
                <input type="checkbox" :checked="selectedIds.has(a.id)" @change="toggleOne(a.id)" />
              </td>
              <td class="px-4 py-3 text-gray-500">{{ a.asset_code }}</td>
              <td class="px-4 py-3 font-medium text-primary">{{ a.name }}</td>
              <td class="px-4 py-3">{{ a.category }}</td>
              <td class="px-4 py-3">{{ a.department }}</td>
              <td class="px-4 py-3">{{ a.holder }}</td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary whitespace-nowrap">
                  {{ $t(`assets.status.${a.status}`) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { downloadBlob } from '@/utils/download'

const store = useAssetsStore()
const auth = useAuthStore()
const { t } = useI18n()

const search = ref('')
const departmentFilter = ref('')
const categoryFilter = ref('')
const statusFilter = ref('')
const selectedIds = ref(new Set())
const exporting = ref(false)
const importing = ref(false)
const importResult = ref(null)
const importError = ref('')
const deleting = ref(false)
const deleteError = ref('')
const syncing = ref(false)
const syncResult = ref(null)
const syncError = ref('')

onMounted(() => store.fetchAssets())

const departments = computed(() =>
  [...new Set(store.assets.map((a) => a.department).filter(Boolean))].sort()
)
const categories = computed(() =>
  [...new Set(store.assets.map((a) => a.category).filter(Boolean))].sort()
)
const statuses = computed(() => [...new Set(store.assets.map((a) => a.status).filter(Boolean))])

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return store.assets.filter((a) => {
    if (departmentFilter.value && a.department !== departmentFilter.value) return false
    if (categoryFilter.value && a.category !== categoryFilter.value) return false
    if (statusFilter.value && a.status !== statusFilter.value) return false
    if (q) {
      const haystack = `${a.name} ${a.asset_code} ${a.holder}`.toLowerCase()
      if (!haystack.includes(q)) return false
    }
    return true
  })
})

const allSelected = computed(
  () => filtered.value.length > 0 && filtered.value.every((a) => selectedIds.value.has(a.id))
)

function toggleAll() {
  if (allSelected.value) {
    filtered.value.forEach((a) => selectedIds.value.delete(a.id))
  } else {
    filtered.value.forEach((a) => selectedIds.value.add(a.id))
  }
  selectedIds.value = new Set(selectedIds.value)
}

function toggleOne(id) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
  selectedIds.value = new Set(selectedIds.value)
}

async function exportAssets(format) {
  exporting.value = true
  try {
    const ids = selectedIds.value.size
      ? [...selectedIds.value]
      : filtered.value.map((a) => a.id)
    const { data } = await api.post(
      '/api/assets/export',
      { format, ids },
      { responseType: 'blob' }
    )
    downloadBlob(data, `danh-sach-tai-san.${format}`)
  } finally {
    exporting.value = false
  }
}

async function onImportPick(e) {
  const file = e.target.files?.[0]
  if (!file) return
  importing.value = true
  importResult.value = null
  importError.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/api/assets/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = data
    await store.fetchAssets()
  } catch (err) {
    importError.value = err.response?.data?.detail ?? 'common.genericError'
  } finally {
    importing.value = false
    e.target.value = ''
  }
}

async function deleteAssetIds(ids) {
  deleting.value = true
  deleteError.value = ''
  try {
    await api.post('/api/assets/delete', { ids })
    selectedIds.value = new Set()
    await store.fetchAssets()
  } catch (err) {
    deleteError.value = err.response?.data?.detail ?? 'common.genericError'
  } finally {
    deleting.value = false
  }
}

function deleteSelected() {
  const count = selectedIds.value.size
  if (!count) return
  if (!confirm(t('assets.io.confirmDeleteSelected', { count }))) return
  deleteAssetIds([...selectedIds.value])
}

function deleteAll() {
  const ids = filtered.value.map((a) => a.id)
  if (!ids.length) return
  if (!confirm(t('assets.io.confirmDeleteAll', { count: ids.length }))) return
  deleteAssetIds(ids)
}

async function syncRds() {
  syncing.value = true
  syncError.value = ''
  syncResult.value = null
  try {
    const { data } = await api.post('/api/assets/sync-rds')
    syncResult.value = data
    await store.fetchAssets()
  } catch (err) {
    syncError.value = err.response?.data?.detail ?? 'common.genericError'
  } finally {
    syncing.value = false
  }
}
</script>
