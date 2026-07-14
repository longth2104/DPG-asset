<template>
  <div class="min-h-screen bg-primary flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="flex flex-col items-center mb-10">
        <img src="/logo.png" alt="DPG" class="h-16 w-auto mb-4" />
        <span class="text-white font-semibold text-lg tracking-wide">{{ siteName }}</span>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-white/70 uppercase tracking-widest mb-2">
            {{ $t('auth.email') }}
          </label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="w-full bg-white text-gray-900 border border-gray-200 px-4 py-2.5 text-sm
                   focus:outline-none focus:border-primary transition-colors"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-white/70 uppercase tracking-widest mb-2">
            {{ $t('auth.password') }}
          </label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full bg-white text-gray-900 border border-gray-200 px-4 py-2.5 text-sm
                   focus:outline-none focus:border-primary transition-colors"
          />
        </div>

        <p v-if="error" class="text-red-400 text-xs pt-1">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-brand hover:opacity-90 disabled:opacity-50 text-white
                 font-semibold py-2.5 text-sm transition-opacity mt-2"
        >
          {{ loading ? $t('auth.signingIn') : $t('auth.login') }}
        </button>
      </form>

      <template v-if="googleClientId">
        <div class="flex items-center gap-3 my-6">
          <div class="flex-1 h-px bg-white/20" />
          <span class="text-xs text-white/60 uppercase tracking-wider">{{ $t('auth.or') }}</span>
          <div class="flex-1 h-px bg-white/20" />
        </div>
        <div ref="googleBtn" class="flex justify-center" />
        <p class="text-xs text-white/60 text-center mt-3">{{ $t('auth.googleHint') }}</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const siteName = ref('DPG Asset Management')
const googleClientId = ref('')
const googleAllowedDomain = ref('')
const googleBtn = ref(null)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail ?? t('auth.invalidCredentials')
  } finally {
    loading.value = false
  }
}

function loadGisScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve()
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.defer = true
    s.onload = resolve
    s.onerror = reject
    document.head.appendChild(s)
  })
}

async function onGoogleCredential(response) {
  error.value = ''
  loading.value = true
  try {
    await auth.loginWithGoogle(response.credential)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail ?? t('auth.invalidCredentials')
  } finally {
    loading.value = false
  }
}

async function initGoogle() {
  try {
    await loadGisScript()
    window.google.accounts.id.initialize({
      client_id: googleClientId.value,
      callback: onGoogleCredential,
      ...(googleAllowedDomain.value ? { hd: googleAllowedDomain.value } : {}),
    })
    if (googleBtn.value) {
      window.google.accounts.id.renderButton(googleBtn.value, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        width: 320,
      })
    }
  } catch {
    /* GIS blocked or offline — password login still works */
  }
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/settings')
    if (data.site_name) siteName.value = data.site_name
    if (data.google_client_id) {
      googleClientId.value = data.google_client_id
      googleAllowedDomain.value = data.google_allowed_domain
      await nextTick()
      initGoogle()
    }
  } catch {
    /* keep defaults — password login still works */
  }
})
</script>
