<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-5xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-6">{{ $t('requests.archive.title') }}</h1>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <select v-model="typeFilter" class="bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded">
          <option value="">{{ $t('requests.archive.type') }} — {{ $t('assets.filters.all') }}</option>
          <option v-for="t in ['transfer', 'acquire', 'liquidate']" :key="t" :value="t">{{ $t(`requests.type.${t}`) }}</option>
        </select>
        <select v-model="statusFilter" class="bg-white text-gray-900 border border-gray-200 px-3 py-2 text-sm rounded">
          <option value="">{{ $t('requests.archive.status') }} — {{ $t('assets.filters.all') }}</option>
          <option v-for="s in ['pending', 'approved', 'rejected', 'completed']" :key="s" :value="s">{{ $t(`requests.status.${s}`) }}</option>
        </select>
      </div>

      <div class="flex items-center gap-2 mb-4 flex-wrap">
        <span v-if="selectedIds.size" class="text-sm text-white/80 mr-1">
          {{ $t('assets.io.selected', { count: selectedIds.size }) }}
        </span>
        <button
          @click="deleteSelected"
          :disabled="!selectedIds.size || deleting"
          class="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-semibold px-3 py-1.5 rounded transition-colors"
        >
          {{ $t('assets.io.deleteSelected') }}
        </button>
        <button
          @click="deleteAll"
          :disabled="!requests.length || deleting"
          class="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-semibold px-3 py-1.5 rounded transition-colors"
        >
          {{ $t('assets.io.deleteAll') }}
        </button>
      </div>
      <p v-if="deleteError" class="text-red-400 text-xs mb-3">{{ $t(deleteError) }}</p>

      <div v-if="loading" class="space-y-2">
        <div v-for="i in 8" :key="i" class="h-12 bg-white/10 rounded animate-pulse" />
      </div>
      <div v-else-if="!requests.length" class="text-muted text-sm">{{ $t('common.noResults') }}</div>
      <div v-else class="bg-white text-gray-900 border border-gray-200 rounded overflow-hidden overflow-x-auto">
        <table class="w-full text-sm min-w-[600px]">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3 w-10">
                <input type="checkbox" :checked="allSelected" @change="toggleAll" />
              </th>
              <th class="text-left px-4 py-3">{{ $t('requests.archive.type') }}</th>
              <th class="text-left px-4 py-3">{{ $t('requests.archive.requester') }}</th>
              <th class="text-left px-4 py-3">{{ $t('requests.archive.status') }}</th>
              <th class="text-left px-4 py-3">{{ $t('requests.archive.createdAt') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in requests"
              :key="r.id"
              class="border-b border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer"
              @click="$router.push(`/requests/${r.id}`)"
            >
              <td class="px-4 py-3" @click.stop>
                <input type="checkbox" :checked="selectedIds.has(r.id)" @change="toggleOne(r.id)" />
              </td>
              <td class="px-4 py-3 font-medium text-primary">
                {{ $t(`requests.type.${r.type}`) }}
                <span v-if="r.origin === 'eoffice'" class="ml-1 text-xs font-semibold text-gray-400">
                  ({{ $t('requests.detail.viaEoffice') }})
                </span>
                <span v-else-if="r.origin === 'direct'" class="ml-1 text-xs font-semibold text-amber-600">
                  ({{ $t('requests.detail.viaDirect') }})
                </span>
              </td>
              <td class="px-4 py-3">{{ r.requester_name || '—' }}</td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary whitespace-nowrap">
                  {{ $t(`requests.status.${r.status}`) }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ new Date(r.created_at).toLocaleDateString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '@/components/AppHeader.vue'
import { useRequestsStore } from '@/stores/requests'

const store = useRequestsStore()
const { t } = useI18n()

const typeFilter = ref('')
const statusFilter = ref('')
const selectedIds = ref(new Set())
const deleting = ref(false)
const deleteError = ref('')

const requests = computed(() => store.requests)
const loading = computed(() => store.loading)

function fetchArchive() {
  const params = { all: true }
  if (typeFilter.value) params.type = typeFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  store.fetchList(params)
}

onMounted(fetchArchive)
watch([typeFilter, statusFilter], fetchArchive)

const allSelected = computed(
  () => requests.value.length > 0 && requests.value.every((r) => selectedIds.value.has(r.id))
)

function toggleAll() {
  if (allSelected.value) {
    requests.value.forEach((r) => selectedIds.value.delete(r.id))
  } else {
    requests.value.forEach((r) => selectedIds.value.add(r.id))
  }
  selectedIds.value = new Set(selectedIds.value)
}

function toggleOne(id) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
  selectedIds.value = new Set(selectedIds.value)
}

async function deleteIds(ids) {
  deleting.value = true
  deleteError.value = ''
  try {
    await store.deleteMany(ids)
    selectedIds.value = new Set()
    await fetchArchive()
  } catch (err) {
    deleteError.value = err.response?.data?.detail ?? 'common.genericError'
  } finally {
    deleting.value = false
  }
}

function deleteSelected() {
  const count = selectedIds.value.size
  if (!count) return
  if (!confirm(t('requests.archive.confirmDeleteSelected', { count }))) return
  deleteIds([...selectedIds.value])
}

function deleteAll() {
  const ids = requests.value.map((r) => r.id)
  if (!ids.length) return
  if (!confirm(t('requests.archive.confirmDeleteAll', { count: ids.length }))) return
  deleteIds(ids)
}
</script>
