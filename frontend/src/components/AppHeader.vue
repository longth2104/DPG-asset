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

            <router-link
              v-if="auth.isAssetManager"
              to="/requests/archive"
              @click="dropdownOpen = false"
              class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {{ $t('nav.requestsArchive') }}
            </router-link>

            <template v-if="auth.isAdmin">
              <router-link
                to="/admin/council-members"
                @click="dropdownOpen = false"
                class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              >
                <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-3.13a4 4 0 10-4-4 4 4 0 004 4zm6 0a4 4 0 10-4-4M12 12a4 4 0 100-8 4 4 0 000 8z" />
                </svg>
                {{ $t('nav.adminCouncil') }}
              </router-link>
              <router-link
                to="/admin/users"
                @click="dropdownOpen = false"
                class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              >
                <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-3.13a4 4 0 10-4-4 4 4 0 004 4zm6 0a4 4 0 10-4-4" />
                </svg>
                {{ $t('nav.adminUsers') }}
              </router-link>
              <router-link
                to="/admin/companies"
                @click="dropdownOpen = false"
                class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-800 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              >
                <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0H5m14 0h2M5 21H3m8-14h2m-2 4h2m-6-4h.01M9 11h.01M9 15h.01M9 19h.01M15 15h.01M15 19h.01" />
                </svg>
                {{ $t('nav.adminCompanies') }}
              </router-link>
            </template>

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
      <div class="relative" ref="bellRef">
        <button
          @click="toggleNotifDropdown"
          class="relative flex items-center justify-center w-8 h-8 rounded text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          :aria-label="$t('notifications.title')"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span
            v-if="notifications.hasUnread"
            class="absolute top-0.5 right-0.5 min-w-[16px] h-4 px-1 flex items-center justify-center text-[10px] font-bold leading-none rounded-full bg-red-500 text-white"
          >
            {{ notifications.unreadCount > 9 ? '9+' : notifications.unreadCount }}
          </span>
        </button>

        <Transition name="dropdown">
          <div
            v-if="notifOpen"
            class="absolute top-full right-0 mt-1.5 w-80 max-w-[90vw] bg-white text-gray-900 border border-gray-300 rounded-lg shadow-2xl overflow-hidden"
          >
            <div class="px-4 py-2.5 bg-gray-100 border-b border-gray-200 flex items-center justify-between">
              <span class="text-sm font-semibold text-gray-900">{{ $t('notifications.title') }}</span>
              <button
                v-if="notifications.hasUnread"
                @click="notifications.markAllRead()"
                class="text-xs font-semibold text-primary hover:underline"
              >
                {{ $t('notifications.markAllRead') }}
              </button>
            </div>
            <div class="max-h-96 overflow-y-auto divide-y divide-gray-100">
              <p v-if="!notifications.items.length" class="px-4 py-6 text-sm text-gray-500 text-center">
                {{ $t('notifications.empty') }}
              </p>
              <button
                v-for="n in notifications.items"
                :key="n.id"
                @click="openNotification(n)"
                class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 transition-colors flex items-start gap-2"
                :class="{ 'bg-primary/5': !n.is_read }"
              >
                <span
                  class="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                  :class="n.is_read ? 'bg-transparent' : 'bg-primary'"
                />
                <span class="min-w-0">
                  <span class="block text-gray-800">{{ notificationText(n) }}</span>
                  <span class="block text-xs text-gray-400 mt-0.5">
                    {{ new Date(n.created_at).toLocaleString() }}
                  </span>
                </span>
              </button>
            </div>
          </div>
        </Transition>
      </div>

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
import { useNotificationsStore } from '@/stores/notifications'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const notifications = useNotificationsStore()
const router = useRouter()
const { t, locale } = useI18n()

const dropdownOpen = ref(false)
const notifOpen = ref(false)
const mobileOpen = ref(false)
const logoRef = ref(null)
const bellRef = ref(null)
let pollInterval = null

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
  if (bellRef.value && !bellRef.value.contains(e.target)) {
    notifOpen.value = false
  }
}

function notificationText(n) {
  const type = t(`requests.type.${n.request_type}`)
  if (n.type === 'pending_approval') return t('notifications.pendingApproval', { type })
  return t(n.request_status === 'rejected' ? 'notifications.rejected' : 'notifications.approved', { type })
}

function toggleNotifDropdown() {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) notifications.fetchAll()
}

async function openNotification(n) {
  notifOpen.value = false
  if (!n.is_read) await notifications.markRead(n.id)
  router.push(`/requests/${n.request_id}`)
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick, true)
  notifications.fetchUnreadCount()
  pollInterval = setInterval(() => notifications.fetchUnreadCount(), 30000)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick, true)
  if (pollInterval) clearInterval(pollInterval)
})
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
