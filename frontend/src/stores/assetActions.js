import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useAssetActionsStore = defineStore('assetActions', () => {
  async function create(payload) {
    const { data } = await api.post('/api/asset-actions', payload)
    return data
  }

  return { create }
})
