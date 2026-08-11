<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-5xl mx-auto w-full">
      <div v-if="store.loading" class="text-muted text-sm">{{ $t('common.loading') }}</div>

      <template v-else-if="asset">
        <div class="flex items-center justify-between mb-8 flex-wrap gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
              {{ asset.asset_code }}
            </p>
            <h1 class="text-2xl font-bold tracking-tight">{{ asset.name }}</h1>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs font-semibold px-3 py-1 rounded-full bg-white text-primary whitespace-nowrap">
              {{ $t(`assets.status.${asset.status}`) }}
            </span>
            <button
              v-if="auth.isAssetManager && !editing"
              @click="startEdit"
              class="bg-white hover:bg-gray-100 text-gray-900 text-xs font-semibold px-3 py-1.5 rounded transition-colors"
            >
              {{ $t('assetDetail.edit') }}
            </button>
            <button
              @click="printDossier"
              class="bg-white hover:bg-gray-100 text-gray-900 text-xs font-semibold px-3 py-1.5 rounded transition-colors"
            >
              {{ $t('assetDetail.printDossier') }}
            </button>
            <router-link
              v-if="auth.isAdmin"
              :to="`/admin/asset-actions/transfer?assetId=${asset.id}`"
              class="bg-amber-400 hover:bg-amber-300 text-gray-900 text-xs font-semibold px-3 py-1.5 rounded transition-colors"
            >
              {{ $t('assetActions.quickLink.transfer') }}
            </router-link>
            <router-link
              v-if="auth.isAdmin"
              :to="`/admin/asset-actions/liquidate?assetId=${asset.id}`"
              class="bg-amber-400 hover:bg-amber-300 text-gray-900 text-xs font-semibold px-3 py-1.5 rounded transition-colors"
            >
              {{ $t('assetActions.quickLink.liquidate') }}
            </router-link>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Profile -->
          <div class="bg-white text-gray-900 rounded p-6">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-4">
              {{ $t('assetDetail.profile') }}
            </h2>
            <form v-if="editing" @submit.prevent="saveEdit" class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.name') }}</label>
                  <input v-model="editForm.name" required class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.code') }}</label>
                  <input v-model="editForm.asset_code" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.category') }}</label>
                  <input v-model="editForm.category" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.serialNumber') }}</label>
                  <input v-model="editForm.serial_number" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.spec') }}</label>
                <textarea v-model="editForm.spec" rows="2" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.manufacturer') }}</label>
                  <input v-model="editForm.manufacturer" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.status') }}</label>
                  <select v-model="editForm.status" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary">
                    <option v-for="s in ASSET_STATUSES" :key="s" :value="s">{{ $t(`assets.status.${s}`) }}</option>
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.department') }}</label>
                  <input v-model="editForm.department" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.columns.holder') }}</label>
                  <input v-model="editForm.holder" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assets.filters.location') }}</label>
                  <input v-model="editForm.location" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.purchaseSource') }}</label>
                  <input v-model="editForm.purchase_source" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.originalCost') }}</label>
                  <input v-model.number="editForm.original_cost" type="number" min="0" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.warranty') }}</label>
                  <input v-model.number="editForm.warranty_months" type="number" min="0" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
                </div>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">{{ $t('assetDetail.notes') }}</label>
                <textarea v-model="editForm.notes" rows="2" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>

              <p v-if="editError" class="text-red-600 text-xs">{{ $t(editError) }}</p>

              <div class="flex gap-2 pt-1">
                <button
                  type="submit"
                  :disabled="!editForm.name || saving"
                  class="bg-brand hover:opacity-90 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-opacity"
                >
                  {{ saving ? $t('common.saving') : $t('common.save') }}
                </button>
                <button
                  type="button"
                  @click="cancelEdit"
                  class="border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-semibold px-4 py-2 rounded transition-colors"
                >
                  {{ $t('common.cancel') }}
                </button>
              </div>
            </form>

            <dl v-else class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assets.columns.category') }}</dt>
                <dd>{{ asset.category || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.spec') }}</dt>
                <dd class="break-words">{{ asset.spec || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.serialNumber') }}</dt>
                <dd>{{ asset.serial_number || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.manufacturer') }}</dt>
                <dd>{{ asset.manufacturer || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assets.columns.department') }}</dt>
                <dd>{{ asset.department || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assets.columns.holder') }}</dt>
                <dd>{{ asset.holder || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assets.filters.location') }}</dt>
                <dd>{{ asset.location || '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.originalCost') }}</dt>
                <dd>{{ formatCurrency(asset.original_cost) }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.warranty') }}</dt>
                <dd>{{ asset.warranty_months ?? '—' }}</dd>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.purchaseSource') }}</dt>
                <dd>{{ asset.purchase_source || '—' }}</dd>
              </div>
              <div v-if="asset.notes" class="grid grid-cols-2 gap-2">
                <dt class="text-gray-500">{{ $t('assetDetail.notes') }}</dt>
                <dd class="break-words">{{ asset.notes }}</dd>
              </div>
            </dl>

            <template v-if="extraFieldEntries.length">
              <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mt-6 mb-3">
                {{ $t('assetDetail.extraFields') }}
              </h2>
              <dl class="space-y-2 text-sm">
                <div v-for="[key, value] in extraFieldEntries" :key="key" class="grid grid-cols-2 gap-2">
                  <dt class="text-gray-500 break-words">{{ key }}</dt>
                  <dd class="break-words">{{ value }}</dd>
                </div>
              </dl>
            </template>

            <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mt-6 mb-3">
              {{ $t('assetDetail.documents') }}
            </h2>
            <ul class="space-y-1.5 text-sm mb-3">
              <li v-for="d in asset.documents" :key="d.id">
                <a :href="`/api/upload/files/${d.file_url}`" target="_blank" class="text-primary hover:underline">
                  {{ d.filename }}
                </a>
              </li>
              <li v-if="!asset.documents.length" class="text-gray-400">{{ $t('common.noResults') }}</li>
            </ul>
            <input v-if="auth.isAssetManager" type="file" @change="onFilePick" class="text-xs" />
          </div>

          <!-- History -->
          <div class="bg-white text-gray-900 rounded p-6">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-4">
              {{ $t('assetDetail.history') }}
            </h2>

            <form v-if="auth.isAssetManager" @submit.prevent="submitNote" class="flex gap-2 mb-5">
              <input
                v-model="noteText"
                :placeholder="$t('assetDetail.notePlaceholder')"
                class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <button
                type="submit"
                :disabled="!noteText.trim()"
                class="bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-colors"
              >
                {{ $t('assetDetail.addNote') }}
              </button>
            </form>

            <ol class="space-y-3 text-sm">
              <li v-for="e in asset.events" :key="e.id" class="border-l-2 border-gray-200 pl-3">
                <p class="text-xs text-gray-400">{{ new Date(e.timestamp).toLocaleString() }}</p>
                <p>{{ e.note || $t(`assetDetail.eventType.${e.type}`) }}</p>
              </li>
              <li v-if="!asset.events.length" class="text-gray-400">{{ $t('common.noResults') }}</li>
            </ol>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { openBlobInNewTab } from '@/utils/download'

const ASSET_STATUSES = ['dang_su_dung', 'dang_sua_chua', 'cho_thanh_ly', 'da_thanh_ly', 'da_dieu_dong']

const route = useRoute()
const store = useAssetsStore()
const auth = useAuthStore()

const noteText = ref('')
const asset = computed(() => store.currentAsset)
const extraFieldEntries = computed(() => Object.entries(asset.value?.extra_fields || {}))

const editing = ref(false)
const saving = ref(false)
const editError = ref('')
const editForm = reactive({})

function load() {
  store.fetchAsset(route.params.id)
}

onMounted(load)
watch(() => route.params.id, load)

function formatCurrency(value) {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('vi-VN').format(value) + 'đ'
}

async function submitNote() {
  if (!noteText.value.trim()) return
  await store.addEvent(route.params.id, noteText.value.trim())
  noteText.value = ''
}

async function onFilePick(e) {
  const file = e.target.files?.[0]
  if (!file) return
  await store.uploadDocument(route.params.id, file)
  e.target.value = ''
}

async function printDossier() {
  const { data } = await api.get(`/api/assets/${route.params.id}/pdf`, { responseType: 'blob' })
  openBlobInNewTab(data)
}

function startEdit() {
  Object.assign(editForm, {
    name: asset.value.name,
    asset_code: asset.value.asset_code,
    category: asset.value.category,
    spec: asset.value.spec,
    serial_number: asset.value.serial_number,
    manufacturer: asset.value.manufacturer,
    department: asset.value.department,
    holder: asset.value.holder,
    location: asset.value.location,
    status: asset.value.status,
    original_cost: asset.value.original_cost,
    warranty_months: asset.value.warranty_months,
    purchase_source: asset.value.purchase_source,
    notes: asset.value.notes,
  })
  editError.value = ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveEdit() {
  if (!editForm.name) return
  saving.value = true
  editError.value = ''
  try {
    await store.updateAsset(route.params.id, { ...editForm })
    editing.value = false
  } catch (e) {
    editError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    saving.value = false
  }
}
</script>
