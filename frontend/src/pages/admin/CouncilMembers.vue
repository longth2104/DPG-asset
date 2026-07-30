<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-3xl mx-auto w-full">
      <h1 class="text-2xl font-bold tracking-tight mb-2">{{ $t('admin.council.title') }}</h1>
      <p class="text-sm text-white/70 mb-6">{{ $t('admin.council.hint') }}</p>

      <form @submit.prevent="submitCreate" class="bg-white text-gray-900 rounded p-6 mb-6 space-y-3">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500">{{ $t('admin.council.add') }}</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            v-model="form.full_name"
            :placeholder="$t('admin.council.fullName')"
            required
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <input
            v-model="form.position"
            :placeholder="$t('admin.council.position')"
            class="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <select v-model="form.council_role" class="border border-gray-300 rounded px-3 py-2 text-sm">
            <option v-for="r in ROLES" :key="r" :value="r">{{ $t(`admin.council.role.${r}`) }}</option>
          </select>
        </div>
        <button
          type="submit"
          :disabled="!form.full_name || submitting"
          class="bg-brand hover:opacity-90 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded transition-opacity"
        >
          {{ $t('admin.council.add') }}
        </button>
        <p v-if="createError" class="text-red-600 text-xs">{{ $t(createError) }}</p>
      </form>

      <div v-if="store.loading" class="text-sm text-white/70">{{ $t('common.loading') }}</div>
      <div v-else class="bg-white text-gray-900 rounded overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th class="text-left px-4 py-3">{{ $t('admin.council.fullName') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.council.position') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.council.roleLabel') }}</th>
              <th class="text-left px-4 py-3">{{ $t('admin.council.active') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in store.members" :key="m.id" class="border-b border-gray-200">
              <td class="px-4 py-3">{{ m.full_name }}</td>
              <td class="px-4 py-3">{{ m.position || '—' }}</td>
              <td class="px-4 py-3">
                <select
                  :value="m.council_role"
                  @change="update(m, { council_role: $event.target.value })"
                  class="border border-gray-300 rounded px-2 py-1 text-xs"
                >
                  <option v-for="r in ROLES" :key="r" :value="r">{{ $t(`admin.council.role.${r}`) }}</option>
                </select>
              </td>
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="m.is_active"
                  @change="update(m, { is_active: $event.target.checked })"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useCouncilStore } from '@/stores/council'

const ROLES = ['chu_tich', 'pho_chu_tich', 'thanh_vien']

const store = useCouncilStore()
const form = reactive({ full_name: '', position: '', council_role: 'thanh_vien' })
const submitting = ref(false)
const createError = ref('')

onMounted(() => store.fetchAll())

async function submitCreate() {
  submitting.value = true
  createError.value = ''
  try {
    await store.create({ ...form })
    form.full_name = ''
    form.position = ''
    form.council_role = 'thanh_vien'
  } catch (e) {
    createError.value = e.response?.data?.detail ?? 'common.genericError'
  } finally {
    submitting.value = false
  }
}

async function update(member, payload) {
  try {
    await store.update(member.id, payload)
  } catch {
    await store.fetchAll()
  }
}
</script>
