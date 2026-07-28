import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useCompaniesStore = defineStore('companies', () => {
  const companies = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/companies')
      companies.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/api/companies', payload)
    companies.value.push(data)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/api/companies/${id}`, payload)
    const idx = companies.value.findIndex((c) => c.id === id)
    if (idx !== -1) companies.value[idx] = data
    return data
  }

  return { companies, loading, error, fetchAll, create, update }
})
