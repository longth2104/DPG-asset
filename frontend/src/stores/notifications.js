import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/utils/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)

  const hasUnread = computed(() => unreadCount.value > 0)

  async function fetchAll() {
    const { data } = await api.get('/api/notifications')
    items.value = data
  }

  async function fetchUnreadCount() {
    const { data } = await api.get('/api/notifications/unread-count')
    unreadCount.value = data.count
  }

  async function markRead(id) {
    await api.post(`/api/notifications/${id}/read`)
    const n = items.value.find((x) => x.id === id)
    if (n && !n.is_read) {
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  async function markAllRead() {
    await api.post('/api/notifications/read-all')
    items.value.forEach((n) => (n.is_read = true))
    unreadCount.value = 0
  }

  return { items, unreadCount, hasUnread, fetchAll, fetchUnreadCount, markRead, markAllRead }
})
