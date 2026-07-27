import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useAssetsStore = defineStore('assets', () => {
  const assets = ref([])
  const currentAsset = ref(null)
  const myAssets = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchMine() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/assets/mine')
      myAssets.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function fetchAssets(params = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/assets', { params })
      assets.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function fetchAsset(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/api/assets/${id}`)
      currentAsset.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function createAsset(payload) {
    const { data } = await api.post('/api/assets', payload)
    return data
  }

  async function updateAsset(id, payload) {
    const { data } = await api.put(`/api/assets/${id}`, payload)
    if (currentAsset.value?.id === id) await fetchAsset(id)
    return data
  }

  async function addEvent(id, note) {
    const { data } = await api.post(`/api/assets/${id}/events`, { note })
    if (currentAsset.value?.id === id) currentAsset.value.events.unshift(data)
    return data
  }

  async function uploadDocument(id, file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`/api/assets/${id}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (currentAsset.value?.id === id) currentAsset.value.documents.unshift(data)
    return data
  }

  return {
    assets, currentAsset, myAssets, loading, error,
    fetchAssets, fetchAsset, fetchMine, createAsset, updateAsset, addEvent, uploadDocument,
  }
})
