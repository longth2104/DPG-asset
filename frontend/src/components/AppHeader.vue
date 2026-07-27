<template>
  <header class="bg-brand text-white px-4 sm:px-6 py-0 flex items-center h-14 flex-shrink-0 shadow-md relative z-40">
    <div class="relative mr-4 sm:mr-8 flex-shrink-0" ref="logoRef">
      <button
        @click="dropdownOpen = !dropdownOpen"
        class="flex items-center gap-1.5 h-14 focus:outline-none group"
        aria-label="Account menu"
      >
        <img src="/logo.png" alt="DPG" class="h-8 w-auto" />
        <svg
          class="w-3 h-3 text-white/40 group-hover:text-white/70 transition-all duration-150"
          :style="{ transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)' }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <Transition name="dropdown">
        <div
          v-if="dropdownOpen"
          class="absolute top-full left-0 mt-1.5 w-60 bg-white text-gray-900 border border-gray-300 rounded-lg shadow-2xl overflow-hidden"
        >
          <div class="px-4 py-3.5 bg-gray-100 border-b border-gray-200 flex items-center gap-3">
            <UserAvatar :user="auth.user" class="w-9 h-9 text-sm flex-shrink-0" />
            <div class="min-w-0">
              <p class="text-sm font-semibold text-gray-900 truncate leading-tight">
                {{ auth.user?.full_name || auth.user?.email }}
              </p>
              <p v-if="auth.user?.full_name" class="text-xs text-gray-600 truncate leading-tight mt-0.5">
                {{ auth.user?.email }}
              </p>
              <span class="mt-1.5 inline-block text-xs font-semibold uppercase tracking-wider border border-gray-300 text-gray-500 px-1.5 py-px rounded">
                {{ auth.user?.role }}
              </span>
            </div>
          </div>

          <div class="py-1">
            <router-link
              to="/profile"
              @click="dropdownOpen = false"
              class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {{ $t('nav.profile') }}
            </router-link>

            <div class="my-1 border-t border-gray-200" />

            <button
              @click="logout"
              class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ $t('nav.signOut') }}
            </button>
          </div>
        </div>
      </Transition>
    </div>

    <nav class="hidden md:flex items-center gap-1 flex-1">
      <router-link
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        class="px-3 py-1.5 text-sm font-medium rounded transition-colors text-white/80 hover:text-white hover:bg-white/10"
        active-class="text-white bg-white/15"
      >
        {{ link.label }}
      </router-link>
    </nav>
    <div class="flex-1 md:hidden" />

    <div class="flex items-center gap-2 sm:gap-3">
      <button
        @click="toggleLang"
        class="flex items-center gap-1 text-xs font-semibold border border-white/25 hover:border-white/50 px-2.5 py-1 rounded transition-colors text-white/80 hover:text-white select-none"
        :title="locale === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'"
      >
        {{ locale === 'vi' ? '🇻🇳 VI' : '🇬🇧 EN' }}
      </button>

      <button
        @click="mobileOpen = !mobileOpen"
        class="md:hidden flex items-center justify-center w-8 h-8 rounded text-white/80 hover:text-white hover:bg-white/10 transition-colors"
        aria-label="Menu"
      >
        <svg v-if="!mobileOpen" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <Transition name="dropdown">
      <nav
        v-if="mobileOpen"
        class="md:hidden absolute top-full left-0 right-0 bg-white text-gray-900 border-b border-gray-300 shadow-2xl py-2"
      >
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          @click="mobileOpen = false"
          class="block px-5 py-2.5 text-sm font-medium text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
          active-class="text-primary bg-gray-100"
        >
          {{ link.label }}
        </router-link>
      </nav>
    </Transition>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const router = useRouter()
const { t, locale } = useI18n()

const dropdownOpen = ref(false)
const mobileOpen = ref(false)
const logoRef = ref(null)

const navLinks = computed(() => [
  { to: '/', label: t('nav.home') },
  { to: '/assets', label: t('nav.assets') },
])

function toggleLang() {
  setLocale(locale.value === 'vi' ? 'en' : 'vi')
}

async function logout() {
  dropdownOpen.value = false
  await auth.logout()
  router.push('/login')
}

function handleOutsideClick(e) {
  if (logoRef.value && !logoRef.value.contains(e.target)) {
    dropdownOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleOutsideClick, true))
onBeforeUnmount(() => document.removeEventListener('click', handleOutsideClick, true))
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
