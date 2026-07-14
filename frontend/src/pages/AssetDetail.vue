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
          <span class="text-xs font-semibold px-3 py-1 rounded-full bg-white text-primary">
            {{ $t(`assets.status.${asset.status}`) }}
          </span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Profile -->
          <div class="bg-white text-gray-900 rounded p-6">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-4">
              {{ $t('assetDetail.profile') }}
            </h2>
            <dl class="space-y-3 text-sm">
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const store = useAssetsStore()
const auth = useAuthStore()

const noteText = ref('')
const asset = computed(() => store.currentAsset)

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
</script>
