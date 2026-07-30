import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useCouncilStore = defineStore('council', () => {
  const members = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/council-members')
      members.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/api/council-members', payload)
    members.value.push(data)
    return data
  }

  async function update(id, payload) {
    const { data } = await api.put(`/api/council-members/${id}`, payload)
    const idx = members.value.findIndex((m) => m.id === id)
    if (idx !== -1) members.value[idx] = data
    return data
  }

  return { members, loading, error, fetchAll, create, update }
})
