import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/users')
      users.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function searchHris(q) {
    const { data } = await api.get('/api/users/hris-search', { params: { q } })
    return data
  }

  async function create(payload) {
    const { data } = await api.post('/api/users', payload)
    users.value.push(data)
    return data
  }

  return { users, loading, error, fetchAll, searchHris, create }
})
