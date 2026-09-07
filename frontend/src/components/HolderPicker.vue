<!--
  Ô chọn NGƯỜI GIỮ tài sản từ danh bạ HRIS.

  Gõ để tìm nhân viên (tên/email/mã NV) trong danh bạ HRIS rồi chọn → phát ra cả
  tên hiển thị (holder) lẫn email (holderEmail). Backend dùng email để liên kết
  tài sản với TÀI KHOẢN thật (holder_user_id, tự tạo từ HRIS nếu chưa có).

  Vẫn cho gõ tự do: nếu người dùng gõ tên mà không chọn ai, holder giữ nguyên
  chữ đã gõ và holderEmail được xoá → tài sản chỉ có tên text (hành vi cũ).

  Tái dùng usersStore.searchHris() + đúng mẫu autocomplete ở admin/Users.vue.
-->
<template>
  <div class="relative" ref="boxRef">
    <input
      v-model="text"
      @focus="open = true"
      @input="onType"
      :placeholder="placeholder"
      class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
    />
    <div
      v-if="open && text.trim() && results.length"
      class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg max-h-72 overflow-y-auto"
    >
      <button
        v-for="r in results"
        :key="r.emp_code"
        type="button"
        @click="pick(r)"
        class="w-full flex flex-col gap-0.5 p-2.5 text-left hover:bg-gray-50 border-b border-gray-100 last:border-0"
      >
        <span class="text-sm font-medium truncate">{{ r.name }}</span>
        <span class="text-xs text-gray-500 truncate">{{ [r.email, r.job_title, r.dept_name].filter(Boolean).join(' · ') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useUsersStore } from '@/stores/users'

const props = defineProps({
  holder: { type: String, default: '' },
  holderEmail: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:holder', 'update:holderEmail'])

const usersStore = useUsersStore()
const text = ref(props.holder || '')
const open = ref(false)
const boxRef = ref(null)
const directory = ref([])

onMounted(async () => {
  document.addEventListener('click', outside, true)
  try {
    directory.value = await usersStore.searchHris()
  } catch {
    directory.value = [] // HRIS không truy cập được → vẫn cho gõ tay
  }
})
onBeforeUnmount(() => document.removeEventListener('click', outside, true))

function outside(e) {
  if (boxRef.value && !boxRef.value.contains(e.target)) open.value = false
}

const results = computed(() => {
  const q = text.value.trim().toLowerCase()
  if (!q) return []
  return directory.value
    .filter(
      (e) =>
        (e.name || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q) ||
        (e.emp_code || '').toLowerCase().includes(q),
    )
    .slice(0, 20)
})

// Gõ tay: giữ tên, bỏ liên kết tài khoản (đến khi chọn ai đó).
function onType() {
  open.value = true
  emit('update:holder', text.value)
  if (props.holderEmail) emit('update:holderEmail', '')
}

function pick(r) {
  text.value = r.name
  open.value = false
  emit('update:holder', r.name)
  emit('update:holderEmail', r.email || '')
}
</script>
