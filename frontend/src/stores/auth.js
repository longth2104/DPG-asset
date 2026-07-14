import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/utils/api'

const ASSET_MANAGER_ROLES = ['phong_thiet_bi', 'hcns_truong_phong', 'lanh_dao_noi_chinh', 'tgd', 'admin']

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  // Centralized here rather than duplicating role-array checks across
  // components/router — the LMS codebase repeats this pattern in 3 places.
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isAssetManager = computed(() => ASSET_MANAGER_ROLES.includes(user.value?.role))

  function setTokens(data) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
  }

  async function login(email, password) {
    const { data } = await api.post('/api/auth/login', { email, password })
    setTokens(data)
    await fetchMe()
  }

  async function loginWithGoogle(credential) {
    const { data } = await api.post('/api/auth/google', { credential })
    setTokens(data)
    await fetchMe()
  }

  async function fetchMe() {
    const { data } = await api.get('/api/auth/me')
    user.value = data
  }

  async function logout() {
    try {
      if (refreshToken.value) {
        await api.post('/api/auth/logout', { refresh_token: refreshToken.value })
      }
    } catch {
      // swallow — server may already have revoked the token
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function init() {
    if (accessToken.value) {
      try {
        await fetchMe()
      } catch {
        await logout()
      }
    }
  }

  // Memoized so the router guard and main.js can both await session restore
  // without triggering /api/auth/me twice or racing each other.
  let initPromise = null
  function ensureInit() {
    if (!initPromise) initPromise = init()
    return initPromise
  }

  return {
    user, accessToken, refreshToken, isAuthenticated, isAdmin, isAssetManager,
    login, loginWithGoogle, logout, fetchMe, init, ensureInit,
  }
})
