<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-5xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-6">{{ $t('home.title') }}</h1>

      <!-- Request actions -->
      <div class="mb-8">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-white/70 mb-3">
          {{ $t('home.actions') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <router-link
            v-for="type in ['transfer', 'acquire', 'liquidate']"
            :key="type"
            :to="`/requests/new/${type}`"
            class="bg-white text-gray-900 rounded p-4 hover:shadow-lg transition-shadow"
          >
            <p class="font-semibold text-primary">{{ $t(`home.action.${type}`) }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ $t(`home.action.${type}Hint`) }}</p>
          </router-link>
        </div>
      </div>

      <!-- My assets -->
      <div class="mb-8">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-white/70 mb-3">
          {{ $t('home.myAssets') }}
        </h2>
        <div v-if="assetsStore.loading" class="space-y-2">
          <div v-for="i in 3" :key="i" class="h-14 bg-white/10 rounded animate-pulse" />
        </div>
        <p v-else-if="!assetsStore.myAssets.length" class="text-sm text-white/70">
          {{ $t('home.noAssets') }}
        </p>
        <div v-else class="bg-white text-gray-900 rounded divide-y divide-gray-200 overflow-hidden">
          <div
            v-for="a in assetsStore.myAssets"
            :key="a.id"
            class="p-4 flex items-center justify-between gap-3 flex-wrap"
          >
            <router-link :to="`/assets/${a.id}`" class="min-w-0">
              <p class="font-semibold text-primary truncate">{{ a.name }}</p>
              <p class="text-xs text-gray-500">
                {{ a.asset_code }} · {{ a.department || '—' }} · {{ a.location || '—' }}
              </p>
            </router-link>
            <div class="flex gap-2 flex-shrink-0">
              <router-link
                :to="`/requests/new/transfer?assetId=${a.id}`"
                class="text-xs font-semibold text-primary hover:underline"
              >
                {{ $t('home.action.transfer') }}
              </router-link>
              <router-link
                :to="`/requests/new/liquidate?assetId=${a.id}`"
                class="text-xs font-semibold text-primary hover:underline"
              >
                {{ $t('home.action.liquidate') }}
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- My requests / pending approvals -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <h2 class="text-sm font-semibold uppercase tracking-wider text-white/70 mb-3">
            {{ $t('home.myRequests') }}
          </h2>
          <div v-if="mine.length" class="bg-white text-gray-900 rounded divide-y divide-gray-200 overflow-hidden">
            <router-link
              v-for="r in mine"
              :key="r.id"
              :to="`/requests/${r.id}`"
              class="flex items-center justify-between gap-3 p-3 text-sm hover:bg-gray-50"
            >
              <span class="font-medium">{{ $t(`requests.type.${r.type}`) }}</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                {{ $t(`requests.status.${r.status}`) }}
              </span>
            </router-link>
          </div>
          <p v-else class="text-sm text-white/70">{{ $t('requests.list.empty') }}</p>
        </div>

        <div v-if="auth.isAssetManager">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-white/70 mb-3">
            {{ $t('home.pendingForMe') }}
          </h2>
          <div v-if="pendingForMe.length" class="bg-white text-gray-900 rounded divide-y divide-gray-200 overflow-hidden">
            <router-link
              v-for="r in pendingForMe"
              :key="r.id"
              :to="`/requests/${r.id}`"
              class="flex items-center justify-between gap-3 p-3 text-sm hover:bg-gray-50"
            >
              <span class="font-medium">{{ $t(`requests.type.${r.type}`) }}</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                {{ $t(`requests.status.${r.status}`) }}
              </span>
            </router-link>
          </div>
          <p v-else class="text-sm text-white/70">{{ $t('requests.list.empty') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const assetsStore = useAssetsStore()
const auth = useAuthStore()

const mine = ref([])
const pendingForMe = ref([])

onMounted(async () => {
  assetsStore.fetchMine()
  const { data } = await api.get('/api/requests')
  mine.value = data.filter((r) => r.requester_id === auth.user?.id)
  pendingForMe.value = data.filter(
    (r) => r.status === 'pending' && r.approver_role === auth.user?.role
  )
})
</script>
