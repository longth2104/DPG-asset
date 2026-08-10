<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />
    <div class="px-4 sm:px-8 py-10 max-w-3xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-1">{{ $t(`assetActions.form.${type}Title`) }}</h1>
      <p class="text-sm text-white/70 mb-8">{{ $t('assetActions.form.hint') }}</p>

      <form @submit.prevent="submit" class="flex flex-col gap-4 bg-white text-gray-900 rounded p-6">
        <!-- Item rows -->
        <div :class="itemsFirst ? 'order-1' : 'order-3'">
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
              <input
                v-model.number="item.approved_sale_price"
                type="number"
                min="0"
                :placeholder="$t('requests.detail.approvedSalePrice')"
                class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary bg-amber-50"
              />
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

        <!-- Acting-on-behalf-of identity -->
        <div :class="itemsFirst ? 'order-2' : 'order-1'" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('assetActions.fields.actingDepartment') }}
            </label>
            <select
              v-model="form.requester_department"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            >
              <option value="">{{ $t('requests.fields.chooseDepartment') }}</option>
              <option v-for="d in departmentOptions" :key="d.dept_code" :value="d.dept_name">{{ d.dept_name }}</option>
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
        </div>

        <!-- Type-specific fields -->
        <div :class="itemsFirst ? 'order-3' : 'order-2'">
          <template v-if="type === 'transfer'">
            <div v-if="form.scope === 'individual'">
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                {{ $t('requests.fields.toHolder') }}
              </label>

              <div v-if="selectedRecipient" class="flex items-center justify-between gap-3 border border-gray-300 rounded px-3 py-2 text-sm">
                <div class="min-w-0">
                  <p class="font-medium truncate">{{ selectedRecipient.name }}</p>
                  <p class="text-xs text-gray-500 truncate">
                    {{ selectedRecipient.email }} · {{ selectedRecipient.job_title }} · {{ selectedRecipient.dept_name }}
                  </p>
                </div>
                <button type="button" @click="clearRecipient" class="text-xs font-semibold text-primary hover:underline flex-shrink-0">
                  {{ $t('requests.fields.recipientChange') }}
                </button>
              </div>
              <div v-else class="relative" ref="recipientBoxRef">
                <input
                  v-model="recipientQuery"
                  @focus="recipientDropdownOpen = true"
                  :placeholder="$t('requests.fields.recipientSearchPlaceholder')"
                  :disabled="loadingDirectory"
                  class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
                <p v-if="loadingDirectory" class="text-xs text-gray-400 mt-1">{{ $t('admin.users.loadingDirectory') }}</p>

                <div
                  v-if="recipientDropdownOpen && recipientQuery.trim() && filteredRecipients.length"
                  class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg max-h-80 overflow-y-auto"
                >
                  <button
                    v-for="r in filteredRecipients"
                    :key="r.emp_code"
                    type="button"
                    @click="selectRecipient(r)"
                    class="w-full flex items-center justify-between gap-3 p-3 text-sm text-left hover:bg-gray-50 border-b border-gray-100 last:border-0"
                  >
                    <div class="min-w-0">
                      <p class="font-medium truncate">{{ r.name }}</p>
                      <p class="text-xs text-gray-500 truncate">{{ r.email }} · {{ r.job_title }} · {{ r.dept_name }}</p>
                    </div>
                  </button>
                </div>
                <p
                  v-else-if="recipientDropdownOpen && recipientQuery.trim() && !filteredRecipients.length && !loadingDirectory"
                  class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg p-3 text-sm text-gray-400"
                >
                  {{ $t('common.noResults') }}
                </p>
              </div>
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

            <div class="grid grid-cols-2 gap-4 mt-4">
              <template v-if="form.scope !== 'individual'">
                <div>
                  <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    {{ $t('requests.fields.company') }}
                  </label>
                  <select v-model="toCompanyCode" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                    <option value="">{{ $t('requests.fields.chooseCompany') }}</option>
                    <option v-for="c in companiesStore.companies" :key="c.id" :value="c.code">{{ c.code }} — {{ c.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    {{ $t('requests.fields.toDepartment') }}
                  </label>
                  <select v-model="form.to_department" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                    <option value="">{{ $t('requests.fields.chooseDepartment') }}</option>
                    <option v-for="d in toDeptOptions" :key="d.dept_code" :value="d.dept_name">{{ d.dept_name }}</option>
                  </select>
                </div>
              </template>
              <div>
                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  {{ $t('requests.fields.toLocation') }}
                </label>
                <input v-model="form.to_location" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary" />
              </div>
            </div>
          </template>

          <template v-if="type === 'acquire'">
            <div v-if="form.scope !== 'individual'" class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  {{ $t('requests.fields.company') }}
                </label>
                <select v-model="toCompanyCode" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                  <option value="">{{ $t('requests.fields.chooseCompany') }}</option>
                  <option v-for="c in companiesStore.companies" :key="c.id" :value="c.code">{{ c.code }} — {{ c.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  {{ $t('requests.fields.toDepartment') }}
                </label>
                <select v-model="form.to_department" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary">
                  <option value="">{{ $t('requests.fields.chooseDepartment') }}</option>
                  <option v-for="d in toDeptOptions" :key="d.dept_code" :value="d.dept_name">{{ d.dept_name }}</option>
                </select>
              </div>
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
        </div>

        <p class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 order-4">
          {{ $t('assetActions.form.warning') }}
        </p>

        <p v-if="error" class="text-red-600 text-xs order-4">{{ $t(error) }}</p>

        <button
          type="submit"
          :disabled="!canSubmit"
          class="w-full bg-brand hover:opacity-90 disabled:opacity-50 text-white font-semibold py-2.5 text-sm rounded transition-opacity order-4"
        >
          {{ submitting ? $t('assetActions.form.submitting') : $t('assetActions.form.submit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useAssetActionsStore } from '@/stores/assetActions'
import { useAssetsStore } from '@/stores/assets'
import { useCompaniesStore } from '@/stores/companies'
import { useUsersStore } from '@/stores/users'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()
const assetsStore = useAssetsStore()
const assetActionsStore = useAssetActionsStore()
const companiesStore = useCompaniesStore()
const usersStore = useUsersStore()

const type = computed(() => route.params.type)
const submitting = ref(false)
const error = ref('')

const SCOPE_OPTIONS_BY_TYPE = {
  transfer: ['individual', 'department', 'branch'],
  acquire: ['individual', 'department', 'branch', 'project'],
}
const scopeOptions = computed(() => SCOPE_OPTIONS_BY_TYPE[type.value] || [])
const itemsFirst = computed(() => type.value === 'transfer' || type.value === 'liquidate')

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
      approved_sale_price: null,
      condition_note: '',
    }
  }
  return { asset_id: preselected }
}

const form = reactive(blankForm())
const items = ref([blankItem()])

const hrisDirectory = ref([])
const loadingDirectory = ref(false)

const departmentOptions = computed(() => {
  const seen = new Map()
  for (const e of hrisDirectory.value) {
    if (!e.dept_code || !e.dept_name || seen.has(e.dept_code)) continue
    seen.set(e.dept_code, { dept_code: e.dept_code, dept_name: e.dept_name, company_code: e.suggested_company_code })
  }
  return [...seen.values()].sort((a, b) => a.dept_name.localeCompare(b.dept_name))
})

const toCompanyCode = ref('')
const toDeptOptions = computed(() =>
  toCompanyCode.value ? departmentOptions.value.filter((d) => d.company_code === toCompanyCode.value) : []
)
watch(toCompanyCode, () => {
  form.to_department = ''
})

// --- Recipient search (transfer, scope=individual) ---
const recipientQuery = ref('')
const recipientDropdownOpen = ref(false)
const recipientBoxRef = ref(null)
const selectedRecipient = ref(null)

const filteredRecipients = computed(() => {
  const q = recipientQuery.value.trim().toLowerCase()
  if (!q) return []
  return hrisDirectory.value
    .filter(
      (e) =>
        (e.name || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q) ||
        (e.emp_code || '').toLowerCase().includes(q)
    )
    .slice(0, 20)
})

function selectRecipient(emp) {
  selectedRecipient.value = emp
  recipientQuery.value = ''
  recipientDropdownOpen.value = false
}

function clearRecipient() {
  selectedRecipient.value = null
  recipientQuery.value = ''
}

function handleOutsideClick(e) {
  if (recipientBoxRef.value && !recipientBoxRef.value.contains(e.target)) {
    recipientDropdownOpen.value = false
  }
}

watch(type, () => {
  Object.assign(form, blankForm())
  items.value = [blankItem()]
  toCompanyCode.value = ''
  clearRecipient()
})

watch(
  () => form.scope,
  () => {
    toCompanyCode.value = ''
    form.to_department = ''
    clearRecipient()
  }
)

onMounted(async () => {
  if (!assetsStore.assets.length) assetsStore.fetchAssets()
  if (!companiesStore.companies.length) companiesStore.fetchAll()
  document.addEventListener('click', handleOutsideClick, true)

  loadingDirectory.value = true
  try {
    hrisDirectory.value = await usersStore.searchHris()
  } catch {
    // HRIS temporarily unreachable — dropdowns just come back empty; none
    // of these fields are required server-side, so the form still submits.
  } finally {
    loadingDirectory.value = false
  }
})

onBeforeUnmount(() => document.removeEventListener('click', handleOutsideClick, true))

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
  if (form.scope === 'individual' && !selectedRecipient.value && !recipientQuery.value.includes('@')) return false
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
      payload.to_location = form.to_location || null

      if (form.scope === 'individual') {
        const email = selectedRecipient.value?.email || recipientQuery.value.trim()
        let localUser = null
        try {
          const { data } = await api.get('/api/users/lookup', { params: { email } })
          localUser = data
        } catch {
          localUser = null
        }
        if (localUser) {
          payload.to_holder_user_id = localUser.id
        } else if (selectedRecipient.value) {
          payload.to_contact_name = selectedRecipient.value.name || null
          payload.to_contact_title = selectedRecipient.value.job_title || null
          payload.to_contact_phone = selectedRecipient.value.phone || null
          payload.to_contact_email = selectedRecipient.value.email || null
        } else {
          payload.to_contact_email = email || null
        }
        payload.to_department = selectedRecipient.value?.dept_name || null
      } else {
        payload.to_department = form.to_department || null
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
        approved_sale_price: i.approved_sale_price,
        condition_note: i.condition_note || null,
      }))
    }

    const created = await assetActionsStore.create(payload)
    router.push(`/requests/${created.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}
</script>
