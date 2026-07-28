<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-4xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-2">{{ $t('admin.users.title') }}</h1>
      <p class="text-sm text-white/70 mb-6">{{ $t('admin.users.hint') }}</p>

      <!-- HRIS search -->
      <div class="bg-white text-gray-900 rounded p-6 mb-6">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
          {{ $t('admin.users.searchHris') }}
        </h2>
        <div class="flex gap-2 mb-3">
          <input
            v-model="query"
            @keyup.enter="doSearch"
            :placeholder="$t('admin.users.searchPlaceholder')"
            class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <button
            @click="doSearch"
            :disabled="searching"
            class="bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-colors"
          >
            {{ $t('common.search') }}
          </button>
        </div>
        <p v-if="searchError" class="text-red-600 text-xs mb-2">{{ $t(searchError) }}</p>
        <ul v-if="results.length" class="divide-y divide-gray-200 border border-gray-200 rounded">
          <li
            v-for="r in results"
            :key="r.emp_code"
            class="flex items-center justify-between gap-3 p-3 text-sm hover:bg-gray-50 cursor-pointer"
            @click="pickResult(r)"
          >
            <div>
              <p class="font-medium">{{ r.name }}</p>
              <p class="text-xs text-gray-500">{{ r.email }} · {{ r.dept_name }} ({{ r.dept_code }})</p>
            </div>
            <span class="text-xs font-semibold text-primary">{{ $t('admin.users.usePicker') }}</span>
          </li>
        </ul>
      </div>

      <!-- Add user form -->
      <form @submit.prevent="submitCreate" class="bg-white text-gray-900 rounded p-6 mb-6 space-y-3">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500">
          {{ $t('admin.users.add') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            v-model="form.email"
            type="email"
            :placeholder="$t('auth.email')"
            required
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <input
            v-model="form.full_name"
            :placeholder="$t('admin.users.fullName')"
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <select v-model="form.role" required class="border border-gray-300 rounded px-3 py-2 text-sm">
            <option value="" disabled>{{ $t('admin.users.chooseRole') }}</option>
            <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
          </select>
          <select v-model="form.company_id" required class="border border-gray-300 rounded px-3 py-2 text-sm">
            <option value="" disabled>{{ $t('admin.users.chooseCompany') }}</option>
            <option v-for="c in companiesStore.companies" :key="c.id" :value="c.id">{{ c.code }} — {{ c.name }}</option>
          </select>
        </div>
        <p v-if="form.hris_emp_code" class="text-xs text-gray-500">
          {{ $t('admin.users.linkedHris') }}: {{ form.hris_emp_code }}
        </p>
        <button
          type="submit"
          :disabled="!form.email || !form.role || !form.company_id || submitting"
          class="bg-brand hover:opacity-90 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-opacity"
        >
          {{ $t('admin.users.add') }}
        </button>
        <p v-if="createError" class="text-red-600 text-xs">{{ $t(createError) }}</p>
      </form>

      <div v-if="usersStore.loading" class="text-sm text-white/70">{{ $t('common.loading') }}</div>
      <div v-else class="bg-white text-gray-900 rounded overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3">{{ $t('auth.email') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.users.fullName') }}</th>
              <th class="text-left px-4 py-3">{{ $t('profile.role') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.companies.title') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in usersStore.users" :key="u.id" class="border-b border-gray-200">
              <td class="px-4 py-3">{{ u.email }}</td>
              <td class="px-4 py-3">{{ u.full_name || '—' }}</td>
              <td class="px-4 py-3">{{ u.role }}</td>
              <td class="px-4 py-3">{{ companyLabel(u.company_id) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useCompaniesStore } from '@/stores/companies'
import { useUsersStore } from '@/stores/users'

const ROLES = ['cbnv', 'phong_thiet_bi', 'hcns_truong_phong', 'lanh_dao_noi_chinh', 'tgd', 'admin']

const usersStore = useUsersStore()
const companiesStore = useCompaniesStore()

const query = ref('')
const results = ref([])
const searching = ref(false)
const searchError = ref('')

const form = reactive({ email: '', full_name: '', role: '', company_id: '', hris_emp_code: null })
const submitting = ref(false)
const createError = ref('')

onMounted(() => {
  usersStore.fetchAll()
  companiesStore.fetchAll()
})

async function doSearch() {
  searching.value = true
  searchError.value = ''
  try {
    results.value = await usersStore.searchHris(query.value)
  } catch (e) {
    searchError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    searching.value = false
  }
}

function pickResult(r) {
  form.email = r.email || ''
  form.full_name = r.name || ''
  form.hris_emp_code = r.emp_code || null
  const match = companiesStore.companies.find((c) => c.code === r.suggested_company_code)
  if (match) form.company_id = match.id
}

async function submitCreate() {
  submitting.value = true
  createError.value = ''
  try {
    await usersStore.create({ ...form })
    form.email = ''
    form.full_name = ''
    form.role = ''
    form.company_id = ''
    form.hris_emp_code = null
  } catch (e) {
    createError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}

function companyLabel(companyId) {
  const c = companiesStore.companies.find((x) => x.id === companyId)
  return c ? `${c.code} — ${c.name}` : '—'
}
</script>
