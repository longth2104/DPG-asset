<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-4xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-2">{{ $t('admin.companies.title') }}</h1>
      <p class="text-sm text-white/70 mb-6">{{ $t('admin.companies.hint') }}</p>

      <!-- Add company -->
      <form @submit.prevent="submitCreate" class="bg-white text-gray-900 rounded p-6 mb-6 space-y-3">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500">
          {{ $t('admin.companies.add') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            v-model="form.code"
            :placeholder="$t('admin.companies.code')"
            required
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <input
            v-model="form.name"
            :placeholder="$t('admin.companies.name')"
            required
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary sm:col-span-2"
          />
        </div>
        <select v-model="form.parent_id" class="w-full border border-gray-300 rounded px-3 py-2 text-sm">
          <option :value="null">{{ $t('admin.companies.noParent') }}</option>
          <option v-for="c in store.companies" :key="c.id" :value="c.id">{{ c.code }} — {{ c.name }}</option>
        </select>
        <button
          type="submit"
          :disabled="!form.code || !form.name || submitting"
          class="bg-brand hover:opacity-90 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-opacity"
        >
          {{ $t('admin.companies.add') }}
        </button>
        <p v-if="createError" class="text-red-600 text-xs">{{ $t(createError) }}</p>
      </form>

      <div v-if="store.loading" class="text-sm text-white/70">{{ $t('common.loading') }}</div>

      <div v-else class="bg-white text-gray-900 rounded overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3">{{ $t('admin.companies.code') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.companies.name') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.companies.parent') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.companies.globalAccess') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in store.companies" :key="c.id" class="border-b border-gray-200">
              <td class="px-4 py-3 font-medium">{{ c.code }}</td>
              <td class="px-4 py-3">
                {{ c.name }}
                <p class="text-xs text-gray-400">{{ c.path }}</p>
              </td>
              <td class="px-4 py-3">
                <select
                  :value="c.parent_id"
                  @change="reparent(c, $event.target.value || null)"
                  class="border border-gray-300 rounded px-2 py-1 text-xs"
                >
                  <option :value="null">{{ $t('admin.companies.noParent') }}</option>
                  <option v-for="p in store.companies.filter((x) => x.id !== c.id)" :key="p.id" :value="p.id">
                    {{ p.code }}
                  </option>
                </select>
              </td>
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="c.grants_global_access"
                  @change="toggleGlobal(c, $event.target.checked)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="updateError" class="text-red-400 text-xs mt-2">{{ $t(updateError) }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useCompaniesStore } from '@/stores/companies'

const store = useCompaniesStore()
const form = reactive({ code: '', name: '', parent_id: null })
const submitting = ref(false)
const createError = ref('')
const updateError = ref('')

onMounted(() => store.fetchAll())

async function submitCreate() {
  submitting.value = true
  createError.value = ''
  try {
    await store.create({ ...form })
    form.code = ''
    form.name = ''
    form.parent_id = null
  } catch (e) {
    createError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}

async function reparent(company, parentId) {
  updateError.value = ''
  try {
    await store.update(company.id, { parent_id: parentId })
  } catch (e) {
    updateError.value = e.response?.data?.detail ?? 'common.genericError'
    await store.fetchAll()
  }
}

async function toggleGlobal(company, checked) {
  updateError.value = ''
  try {
    await store.update(company.id, { grants_global_access: checked })
  } catch (e) {
    updateError.value = e.response?.data?.detail ?? 'common.genericError'
    await store.fetchAll()
  }
}
</script>
