<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />
    <div class="px-4 sm:px-8 py-10 max-w-2xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-8">{{ $t(`requests.form.${type}Title`) }}</h1>

      <form @submit.prevent="submit" class="space-y-4 bg-white text-gray-900 rounded p-6">
        <div v-if="type === 'transfer' || type === 'liquidate'">
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('requests.fields.asset') }}
          </label>
          <select
            v-model="form.asset_id"
            required
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option value="" disabled>{{ $t('requests.form.chooseAsset') }}</option>
            <option v-for="a in assetsStore.assets" :key="a.id" :value="a.id">
              {{ a.asset_code }} — {{ a.name }}
            </option>
          </select>
        </div>

        <div v-if="scopeOptions.length">
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('requests.fields.scope') }}
          </label>
          <select
            v-model="form.scope"
            required
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option v-for="s in scopeOptions" :key="s" :value="s">{{ $t(`requests.scope.${s}`) }}</option>
          </select>
        </div>

        <template v-if="type === 'transfer'">
          <div v-if="form.scope === 'individual'">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.toHolder') }}
            </label>
            <input
              v-model="toHolderEmail"
              type="email"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toDepartment') }}
              </label>
              <input v-model="form.to_department" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toLocation') }}
              </label>
              <input v-model="form.to_location" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
          </div>
        </template>

        <template v-if="type === 'acquire'">
          <div v-if="form.scope !== 'individual'">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.toDepartment') }}
            </label>
            <input v-model="form.to_department" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.justification') }}
            </label>
            <textarea
              v-model="form.justification"
              rows="3"
              required
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.estimatedCost') }}
            </label>
            <input
              v-model.number="form.estimated_cost"
              type="number"
              min="0"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
        </template>

        <template v-if="type === 'liquidate'">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.reason') }}
            </label>
            <textarea
              v-model="form.reason"
              rows="3"
              required
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.fields.conditionNote') }}
            </label>
            <textarea
              v-model="form.condition_note"
              rows="3"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
        </template>

        <p v-if="error" class="text-red-600 text-xs">{{ $t(error) }}</p>

        <button
          type="submit"
          :disabled="!canSubmit"
          class="w-full bg-brand hover:opacity-90 disabled:opacity-50 text-white font-semibold py-2.5 text-sm rounded transition-opacity"
        >
          {{ submitting ? $t('requests.form.submitting') : $t('requests.form.submit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetsStore } from '@/stores/assets'
import { useRequestsStore } from '@/stores/requests'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()
const assetsStore = useAssetsStore()
const requestsStore = useRequestsStore()

const type = computed(() => route.params.type)
const toHolderEmail = ref('')
const submitting = ref(false)
const error = ref('')

const SCOPE_OPTIONS_BY_TYPE = {
  transfer: ['individual', 'department', 'branch'],
  acquire: ['individual', 'department', 'branch', 'project'],
}
const scopeOptions = computed(() => SCOPE_OPTIONS_BY_TYPE[type.value] || [])

function blankForm() {
  return {
    asset_id: route.query.assetId || '',
    scope: scopeOptions.value[0] || null,
    to_department: '',
    to_location: '',
    justification: '',
    estimated_cost: null,
    reason: '',
    condition_note: '',
  }
}

const form = reactive(blankForm())

watch(type, () => Object.assign(form, blankForm()))

onMounted(() => {
  if (!assetsStore.assets.length) assetsStore.fetchAssets()
})

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (type.value === 'transfer') return !!form.asset_id
  if (type.value === 'acquire') return !!form.justification
  if (type.value === 'liquidate') return !!form.asset_id && !!form.reason
  return false
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const payload = { type: type.value }

    if (type.value === 'transfer' || type.value === 'liquidate') {
      payload.asset_id = form.asset_id
    }
    if (type.value === 'transfer' || type.value === 'acquire') {
      payload.scope = form.scope
    }
    if (type.value === 'transfer') {
      payload.to_department = form.to_department || null
      payload.to_location = form.to_location || null
      if (form.scope === 'individual' && toHolderEmail.value) {
        const { data } = await api.get('/api/users/lookup', { params: { email: toHolderEmail.value } })
        payload.to_holder_user_id = data.id
      }
    }
    if (type.value === 'acquire') {
      payload.to_department = form.to_department || null
      payload.justification = form.justification
      payload.estimated_cost = form.estimated_cost
    }
    if (type.value === 'liquidate') {
      payload.reason = form.reason
      payload.condition_note = form.condition_note || null
    }

    const created = await requestsStore.create(payload)
    router.push(`/requests/${created.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}
</script>
