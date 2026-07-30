<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />
    <div class="px-4 sm:px-8 py-10 max-w-3xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-8">{{ $t(`requests.form.${type}Title`) }}</h1>

      <form @submit.prevent="submit" class="space-y-4 bg-white text-gray-900 rounded p-6">
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('requests.fields.requesterDepartment') }}
          </label>
          <input
            v-model="form.requester_department"
            :placeholder="$t('requests.fields.requesterDepartmentPlaceholder')"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
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
          <div v-else class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toContactName') }}
              </label>
              <input v-model="form.to_contact_name" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toContactTitle') }}
              </label>
              <input v-model="form.to_contact_title" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toContactPhone') }}
              </label>
              <input v-model="form.to_contact_phone" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toContactIdCard') }}
              </label>
              <input v-model="form.to_contact_id_card" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </div>
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
              rows="2"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
        </template>

        <div v-if="type === 'liquidate'">
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            {{ $t('requests.fields.reason') }}
          </label>
          <textarea
            v-model="form.reason"
            rows="2"
            required
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>

        <!-- Item rows -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {{ $t('requests.fields.items') }}
            </label>
            <button
              type="button"
              @click="addItem"
              class="text-xs font-semibold text-primary hover:underline"
            >
              + {{ $t('requests.fields.addItem') }}
            </button>
          </div>

          <div
            v-for="(item, idx) in items"
            :key="idx"
            class="border border-gray-200 rounded p-3 mb-2 space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-400">#{{ idx + 1 }}</span>
              <button
                v-if="items.length > 1"
                type="button"
                @click="removeItem(idx)"
                class="text-xs text-red-600 hover:underline"
              >
                {{ $t('requests.fields.removeItem') }}
              </button>
            </div>

            <template v-if="type === 'acquire'">
              <input
                v-model="item.name"
                :placeholder="$t('requests.fields.itemName')"
                required
                class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
              <div class="grid grid-cols-3 gap-2">
                <input v-model="item.unit" :placeholder="$t('requests.fields.itemUnit')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
                <input v-model.number="item.quantity" type="number" min="1" :placeholder="$t('requests.fields.itemQuantity')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
                <input v-model.number="item.unit_price" type="number" min="0" :placeholder="$t('requests.fields.itemUnitPrice')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <input v-model="item.manufacturer" :placeholder="$t('requests.fields.itemManufacturer')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
                <input v-model="item.purpose" :placeholder="$t('requests.fields.itemPurpose')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
              </div>
            </template>

            <template v-else-if="type === 'liquidate'">
              <select v-model="item.asset_id" required class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                <option value="" disabled>{{ $t('requests.form.chooseAsset') }}</option>
                <option v-for="a in assetsStore.assets" :key="a.id" :value="a.id">{{ a.asset_code }} — {{ a.name }}</option>
              </select>
              <div class="grid grid-cols-3 gap-2">
                <input v-model.number="item.remaining_value" type="number" min="0" :placeholder="$t('requests.fields.itemRemainingValue')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
                <input v-model.number="item.market_value" type="number" min="0" :placeholder="$t('requests.fields.itemMarketValue')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
                <input v-model.number="item.proposed_value" type="number" min="0" :placeholder="$t('requests.fields.itemProposedValue')" class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
              </div>
              <textarea v-model="item.condition_note" rows="2" :placeholder="$t('requests.fields.itemConditionNote')" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            </template>

            <template v-else>
              <select v-model="item.asset_id" required class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                <option value="" disabled>{{ $t('requests.form.chooseAsset') }}</option>
                <option v-for="a in assetsStore.assets" :key="a.id" :value="a.id">{{ a.asset_code }} — {{ a.name }}</option>
              </select>
            </template>
          </div>
        </div>

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
    requester_department: '',
    scope: scopeOptions.value[0] || null,
    to_department: '',
    to_location: '',
    to_contact_name: '',
    to_contact_title: '',
    to_contact_phone: '',
    to_contact_id_card: '',
    justification: '',
    reason: '',
  }
}

function blankItem() {
  const preselected = route.query.assetId || ''
  if (type.value === 'acquire') {
    return { name: '', unit: '', quantity: 1, unit_price: null, manufacturer: '', purpose: '' }
  }
  if (type.value === 'liquidate') {
    return {
      asset_id: preselected,
      remaining_value: null,
      market_value: null,
      proposed_value: null,
      condition_note: '',
    }
  }
  return { asset_id: preselected }
}

const form = reactive(blankForm())
const items = ref([blankItem()])

watch(type, () => {
  Object.assign(form, blankForm())
  items.value = [blankItem()]
})

onMounted(() => {
  if (!assetsStore.assets.length) assetsStore.fetchAssets()
})

function addItem() {
  items.value.push(blankItem())
}

function removeItem(idx) {
  items.value.splice(idx, 1)
}

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (type.value === 'acquire') return items.value.every((i) => i.name)
  if (type.value === 'liquidate') return !!form.reason && items.value.every((i) => i.asset_id)
  return items.value.every((i) => i.asset_id)
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const payload = {
      type: type.value,
      requester_department: form.requester_department || null,
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
      } else {
        payload.to_contact_name = form.to_contact_name || null
        payload.to_contact_title = form.to_contact_title || null
        payload.to_contact_phone = form.to_contact_phone || null
        payload.to_contact_id_card = form.to_contact_id_card || null
      }
      payload.items = items.value.map((i) => ({ asset_id: i.asset_id }))
    }
    if (type.value === 'acquire') {
      payload.to_department = form.to_department || null
      payload.justification = form.justification || null
      payload.items = items.value.map((i) => ({
        name: i.name,
        unit: i.unit || null,
        quantity: i.quantity || 1,
        unit_price: i.unit_price,
        manufacturer: i.manufacturer || null,
        purpose: i.purpose || null,
      }))
    }
    if (type.value === 'liquidate') {
      payload.reason = form.reason
      payload.items = items.value.map((i) => ({
        asset_id: i.asset_id,
        remaining_value: i.remaining_value,
        market_value: i.market_value,
        proposed_value: i.proposed_value,
        condition_note: i.condition_note || null,
      }))
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
