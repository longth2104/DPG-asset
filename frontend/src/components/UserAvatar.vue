<template>
  <div class="rounded-full bg-primary text-white flex items-center justify-center font-semibold uppercase">
    {{ initials }}
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
})

const initials = computed(() => {
  const label = props.user?.full_name || props.user?.email || '?'
  return label.trim().slice(0, 1)
})
</script>
