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

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
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

      <div v-if="store.loading" class="space-y-2">
        <div v-for="i in 8" :key="i" class="h-12 bg-white/10 rounded animate-pulse" />
      </div>

      <div v-else-if="!filtered.length" class="text-muted text-sm">{{ $t('common.noResults') }}</div>

      <div v-else class="bg-white text-gray-900 border border-gray-200 rounded overflow-hidden overflow-x-auto">
        <table class="w-full text-sm min-w-[720px]">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
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
              <td class="px-4 py-3 text-gray-500">{{ a.asset_code }}</td>
              <td class="px-4 py-3 font-medium text-primary">{{ a.name }}</td>
              <td class="px-4 py-3">{{ a.category }}</td>
              <td class="px-4 py-3">{{ a.department }}</td>
              <td class="px-4 py-3">{{ a.holder }}</td>
              <td class="px-4 py-3">
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
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
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'

const store = useAssetsStore()
const auth = useAuthStore()

const search = ref('')
const departmentFilter = ref('')
const categoryFilter = ref('')
const statusFilter = ref('')

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
</script>
