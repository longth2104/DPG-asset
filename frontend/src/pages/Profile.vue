<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-12 max-w-xl mx-auto w-full">
      <div class="flex items-center gap-5 mb-8">
        <UserAvatar :user="auth.user" class="w-16 h-16 text-2xl flex-shrink-0" />
        <div>
          <h1 class="text-2xl font-bold tracking-tight">
            {{ auth.user?.full_name || auth.user?.email }}
          </h1>
          <p class="text-sm text-muted">{{ auth.user?.email }}</p>
          <span class="mt-2 inline-block text-xs font-semibold uppercase tracking-wider border border-white/30 text-white/70 px-2 py-0.5 rounded">
            {{ $t('profile.role') }}: {{ auth.user?.role }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>
