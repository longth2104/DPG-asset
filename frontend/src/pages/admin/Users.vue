<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-4xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-2">{{ $t('admin.users.title') }}</h1>
      <p class="text-sm text-white/70 mb-6">{{ $t('admin.users.hint') }}</p>

      <!-- HRIS live search -->
      <div class="bg-white text-gray-900 rounded p-6 mb-6">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
          {{ $t('admin.users.searchHris') }}
        </h2>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div class="relative sm:col-span-2" ref="searchBoxRef">
            <input
              v-model="query"
              @focus="dropdownOpen = true"
              :placeholder="$t('admin.users.searchPlaceholder')"
              :disabled="loadingDirectory"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
            <p v-if="loadingDirectory" class="text-xs text-gray-400 mt-1">{{ $t('admin.users.loadingDirectory') }}</p>

            <div
              v-if="dropdownOpen && query.trim() && filteredResults.length"
              class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg max-h-80 overflow-y-auto"
            >
              <button
                v-for="r in filteredResults"
                :key="r.emp_code"
                type="button"
                :disabled="adding === r.emp_code"
                @click="addFromHris(r)"
                class="w-full flex items-center justify-between gap-3 p-3 text-sm text-left hover:bg-gray-50 disabled:opacity-50 border-b border-gray-100 last:border-0"
              >
                <div class="min-w-0">
                  <p class="font-medium truncate">{{ r.name }}</p>
                  <p class="text-xs text-gray-500 truncate">
                    {{ r.email }} · {{ r.job_title }} · {{ r.dept_name }}
                  </p>
                </div>
                <span class="text-xs font-semibold text-primary flex-shrink-0">
                  {{ adding === r.emp_code ? $t('admin.users.adding') : companyBadge(r.suggested_company_code) }}
                </span>
              </button>
            </div>
            <p
              v-else-if="dropdownOpen && query.trim() && !filteredResults.length && !loadingDirectory"
              class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg p-3 text-sm text-gray-400"
            >
              {{ $t('common.noResults') }}
            </p>
          </div>

          <select v-model="defaultRole" class="border border-gray-300 rounded px-3 py-2 text-sm">
            <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
        <p class="text-xs text-gray-500 mb-2">{{ $t('admin.users.defaultRoleHint') }}</p>
        <p v-if="addError" class="text-red-600 text-xs">{{ $t(addError) }}</p>
      </div>

      <p v-if="rowError" class="text-red-400 text-xs mb-3">{{ rowError }}</p>

      <div v-if="usersStore.loading" class="text-sm text-white/70">{{ $t('common.loading') }}</div>
      <div v-else class="bg-white text-gray-900 rounded overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3">{{ $t('auth.email') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.users.fullName') }}</th>
              <th class="text-left px-4 py-3">{{ $t('profile.role') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.companies.title') }}</th>
              <th class="text-left px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in usersStore.users" :key="u.id" class="border-b border-gray-200">
              <td class="px-4 py-3">{{ u.email }}</td>
              <td class="px-4 py-3">{{ u.full_name || '—' }}</td>
              <td class="px-4 py-3">
                <select
                  :value="u.role"
                  :disabled="u.id === auth.user?.id || rowUpdating === u.id"
                  @change="changeRole(u, $event.target.value)"
                  :title="u.id === auth.user?.id ? $t('admin.users.cannotEditOwnRole') : ''"
                  class="border border-gray-300 rounded px-2 py-1 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
                </select>
              </td>
              <td class="px-4 py-3">{{ companyLabel(u.company_id) }}</td>
              <td class="px-4 py-3">
                <button
                  v-if="u.id !== auth.user?.id"
                  @click="removeUser(u)"
                  :disabled="rowUpdating === u.id"
                  class="text-xs font-semibold text-red-600 hover:underline disabled:opacity-50"
                >
                  {{ $t('admin.users.remove') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useCompaniesStore } from '@/stores/companies'
import { useUsersStore } from '@/stores/users'

const ROLES = ['cbnv', 'phong_thiet_bi', 'hcns_truong_phong', 'lanh_dao_noi_chinh', 'tgd', 'admin']

const usersStore = useUsersStore()
const companiesStore = useCompaniesStore()
const auth = useAuthStore()
const { t } = useI18n()
const rowUpdating = ref(null)
const rowError = ref('')

const query = ref('')
const dropdownOpen = ref(false)
const searchBoxRef = ref(null)
const hrisDirectory = ref([])
const loadingDirectory = ref(false)
const defaultRole = ref('cbnv')
const adding = ref(null)
const addError = ref('')

onMounted(async () => {
  usersStore.fetchAll()
  companiesStore.fetchAll()
  document.addEventListener('click', handleOutsideClick, true)

  loadingDirectory.value = true
  try {
    hrisDirectory.value = await usersStore.searchHris()
  } catch (e) {
    addError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    loadingDirectory.value = false
  }
})

onBeforeUnmount(() => document.removeEventListener('click', handleOutsideClick, true))

function handleOutsideClick(e) {
  if (searchBoxRef.value && !searchBoxRef.value.contains(e.target)) {
    dropdownOpen.value = false
  }
}

// HRIS employees already added as local users — hide them from the picker
// so a match can't be clicked twice into a 409.
const addedEmpCodes = computed(
  () => new Set(usersStore.users.map((u) => u.hris_emp_code).filter(Boolean))
)

const filteredResults = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return hrisDirectory.value
    .filter((e) => !addedEmpCodes.value.has(e.emp_code))
    .filter(
      (e) =>
        (e.name || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q) ||
        (e.emp_code || '').toLowerCase().includes(q)
    )
    .slice(0, 20)
})

function companyBadge(code) {
  const c = companiesStore.companies.find((x) => x.code === code)
  return c ? c.code : t('admin.users.unmappedCompany')
}

async function addFromHris(emp) {
  if (adding.value) return
  addError.value = ''

  const company = companiesStore.companies.find((c) => c.code === emp.suggested_company_code)
  if (!company) {
    addError.value = t('admin.users.companyNotFound', { code: emp.suggested_company_code || '?' })
    return
  }

  adding.value = emp.emp_code
  try {
    await usersStore.create({
      email: emp.email,
      full_name: emp.name,
      role: defaultRole.value,
      company_id: company.id,
      hris_emp_code: emp.emp_code,
    })
    query.value = ''
    dropdownOpen.value = false
  } catch (e) {
    addError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    adding.value = null
  }
}

async function changeRole(user, role) {
  if (role === user.role) return
  rowUpdating.value = user.id
  rowError.value = ''
  try {
    await usersStore.update(user.id, { role })
  } catch (e) {
    rowError.value = e.response?.data?.detail ?? t('common.genericError')
  } finally {
    rowUpdating.value = null
  }
}

async function removeUser(user) {
  if (!confirm(t('admin.users.confirmRemove', { email: user.email }))) return

  rowUpdating.value = user.id
  rowError.value = ''
  try {
    await usersStore.remove(user.id)
  } catch (e) {
    rowError.value = e.response?.data?.detail ?? t('common.genericError')
  } finally {
    rowUpdating.value = null
  }
}

function companyLabel(companyId) {
  const c = companiesStore.companies.find((x) => x.id === companyId)
  return c ? `${c.code} — ${c.name}` : '—'
}
</script>
