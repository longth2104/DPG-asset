import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useRequestsStore = defineStore('requests', () => {
  const requests = ref([])
  const currentRequest = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchList(params = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/requests', { params })
      requests.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/api/requests/${id}`)
      currentRequest.value = data
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'common.genericError'
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await api.post('/api/requests', payload)
    return data
  }

  async function decide(id, approve, note, items = []) {
    const { data } = await api.post(`/api/requests/${id}/decide`, { approve, note, items })
    if (currentRequest.value?.id === id) currentRequest.value = data
    return data
  }

  async function deleteMany(ids) {
    const { data } = await api.post('/api/requests/delete', { ids })
    return data
  }

  async function sign(id, signedName, signatureBlob) {
    const form = new FormData()
    form.append('signed_name', signedName)
    if (signatureBlob) form.append('signature_image', signatureBlob, 'signature.png')
    const { data } = await api.post(`/api/requests/${id}/sign`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (currentRequest.value?.id === id) currentRequest.value.signatures.push(data)
    return data
  }

  async function fetchPdfBlob(id) {
    const { data } = await api.get(`/api/requests/${id}/pdf`, { responseType: 'blob' })
    return data
  }

  return {
    requests, currentRequest, loading, error,
    fetchList, fetchOne, create, decide, sign, fetchPdfBlob, deleteMany,
  }
})
