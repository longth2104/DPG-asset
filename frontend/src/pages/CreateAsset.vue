<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-2xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-8">{{ $t('createAsset.title') }}</h1>

      <form @submit.prevent="submit" class="space-y-4 bg-white text-gray-900 rounded p-6">
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('createAsset.name') }}
          </label>
          <input v-model="form.name" required class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.category') }}
            </label>
            <input v-model="form.category" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.manufacturer') }}
            </label>
            <input v-model="form.manufacturer" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.department') }}
            </label>
            <input v-model="form.department" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.holder') }}
            </label>
            <input v-model="form.holder" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.location') }}
            </label>
            <input v-model="form.location" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('createAsset.originalCost') }}
            </label>
            <input v-model.number="form.original_cost" type="number" min="0" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('createAsset.company') }}
          </label>
          <select
            v-model="form.company_id"
            required
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option v-for="c in companiesStore.companies" :key="c.id" :value="c.id">{{ c.code }} — {{ c.name }}</option>
          </select>
        </div>

        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {{ $t('createAsset.customFields') }}
            </label>
            <button type="button" @click="addCustomField" class="text-xs font-semibold text-primary hover:underline">
              + {{ $t('createAsset.addField') }}
            </button>
          </div>
          <div v-for="(f, idx) in customFields" :key="idx" class="flex items-center gap-2 mb-2">
            <input
              v-model="f.key"
              :placeholder="$t('createAsset.fieldName')"
              class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
            <input
              v-model="f.value"
              :placeholder="$t('createAsset.fieldValue')"
              class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
            <button type="button" @click="customFields.splice(idx, 1)" class="text-xs text-red-600 hover:underline flex-shrink-0">
              {{ $t('requests.fields.removeItem') }}
            </button>
          </div>
        </div>

        <p v-if="error" class="text-red-600 text-xs">{{ $t(error) }}</p>

        <button
          type="submit"
          :disabled="!form.name || submitting"
          class="w-full bg-brand hover:opacity-90 disabled:opacity-50 text-white font-semibold py-2.5 text-sm rounded transition-opacity"
        >
          {{ $t('createAsset.submit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import { useCompaniesStore } from '@/stores/companies'

const router = useRouter()
const store = useAssetsStore()
const companiesStore = useCompaniesStore()
const auth = useAuthStore()

const form = ref({
  name: '',
  category: '',
  manufacturer: '',
  department: '',
  holder: '',
  location: '',
  original_cost: null,
  company_id: auth.user?.company_id || '',
})
const customFields = ref([])
const submitting = ref(false)
const error = ref('')

function addCustomField() {
  customFields.value.push({ key: '', value: '' })
}

onMounted(() => {
  if (!companiesStore.companies.length) companiesStore.fetchAll()
})

async function submit() {
  if (!form.value.name || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const extra_fields = {}
    for (const f of customFields.value) {
      if (f.key.trim()) extra_fields[f.key.trim()] = f.value
    }
    const payload = { ...form.value }
    if (Object.keys(extra_fields).length) payload.extra_fields = extra_fields
    const asset = await store.createAsset(payload)
    router.push(`/assets/${asset.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}
</script>
