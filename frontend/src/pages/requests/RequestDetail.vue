<template>
  <div class="min-h-screen bg-primary text-white flex flex-col">
    <AppHeader />

    <div class="px-4 sm:px-8 py-10 max-w-2xl mx-auto w-full">
      <div v-if="store.loading" class="text-muted text-sm">{{ $t('common.loading') }}</div>

      <template v-else-if="request">
        <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
              {{ $t(`requests.type.${request.type}`) }}
            </p>
            <h1 class="text-2xl font-bold tracking-tight">{{ $t('requests.detail.title') }}</h1>
          </div>
          <span class="text-xs font-semibold px-3 py-1 rounded-full bg-white text-primary">
            {{ $t(`requests.status.${request.status}`) }}
          </span>
        </div>

        <div class="bg-white text-gray-900 rounded p-6 mb-6">
          <dl class="space-y-3 text-sm">
            <div v-if="asset" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.asset') }}</dt>
              <dd>{{ asset.asset_code }} — {{ asset.name }}</dd>
            </div>
            <div v-if="request.scope" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.scope') }}</dt>
              <dd>{{ $t(`requests.scope.${request.scope}`) }}</dd>
            </div>
            <div v-if="request.to_department" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.toDepartment') }}</dt>
              <dd>{{ request.to_department }}</dd>
            </div>
            <div v-if="request.to_location" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.toLocation') }}</dt>
              <dd>{{ request.to_location }}</dd>
            </div>
            <div v-if="request.justification" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.justification') }}</dt>
              <dd class="break-words">{{ request.justification }}</dd>
            </div>
            <div v-if="request.estimated_cost != null" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.estimatedCost') }}</dt>
              <dd>{{ formatCurrency(request.estimated_cost) }}</dd>
            </div>
            <div v-if="request.reason" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.reason') }}</dt>
              <dd class="break-words">{{ request.reason }}</dd>
            </div>
            <div v-if="request.condition_note" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.fields.conditionNote') }}</dt>
              <dd class="break-words">{{ request.condition_note }}</dd>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.detail.approverRole') }}</dt>
              <dd>{{ request.approver_role }}</dd>
            </div>
            <div v-if="request.decision_note" class="grid grid-cols-2 gap-2">
              <dt class="text-gray-500">{{ $t('requests.detail.decisionNote') }}</dt>
              <dd class="break-words">{{ request.decision_note }}</dd>
            </div>
          </dl>

          <button
            @click="downloadPdf"
            class="mt-5 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-4 py-2 rounded transition-colors"
          >
            {{ $t('requests.detail.downloadPdf') }}
          </button>
        </div>

        <!-- Approve / reject -->
        <div v-if="canDecide" class="bg-white text-gray-900 rounded p-6 mb-6">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
            {{ $t('requests.detail.approve') }} / {{ $t('requests.detail.reject') }}
          </h2>
          <textarea
            v-model="decisionNote"
            :placeholder="$t('requests.detail.decisionNotePlaceholder')"
            rows="2"
            class="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-3 focus:outline-none focus:border-primary"
          />
          <div class="flex gap-2">
            <button
              @click="decide(true)"
              :disabled="deciding"
              class="flex-1 bg-brand hover:opacity-90 disabled:opacity-50 text-white text-sm font-semibold py-2 rounded transition-opacity"
            >
              {{ $t('requests.detail.approve') }}
            </button>
            <button
              @click="decide(false)"
              :disabled="deciding"
              class="flex-1 border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-semibold py-2 rounded transition-colors"
            >
              {{ $t('requests.detail.reject') }}
            </button>
          </div>
        </div>

        <!-- Sign -->
        <div v-if="canSign" class="bg-white text-gray-900 rounded p-6">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
            {{ $t('requests.detail.signSection') }}
          </h2>
          <div class="mb-3">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.detail.signedName') }}
            </label>
            <input
              v-model="signedName"
              class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div class="mb-3">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.detail.signaturePad') }}
            </label>
            <SignaturePad ref="padRef" />
            <button
              type="button"
              @click="padRef?.clear()"
              class="text-xs text-gray-500 hover:text-gray-700 mt-1"
            >
              {{ $t('requests.detail.clearSignature') }}
            </button>
          </div>
          <div class="mb-4">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              {{ $t('requests.detail.uploadInstead') }}
            </label>
            <input type="file" accept="image/*" @change="onUploadPick" class="text-xs" />
          </div>
          <button
            @click="submitSignature"
            :disabled="!signedName.trim() || signing"
            class="w-full bg-brand hover:opacity-90 disabled:opacity-50 text-white font-semibold py-2.5 text-sm rounded transition-opacity"
          >
            {{ signing ? $t('requests.detail.signing') : $t('requests.detail.signSubmit') }}
          </button>
        </div>
        <p v-else-if="signOffMessage" class="text-sm text-white/70 mt-2">{{ signOffMessage }}</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import SignaturePad from '@/components/SignaturePad.vue'
import { useAssetsStore } from '@/stores/assets'
import { useAuthStore } from '@/stores/auth'
import { useRequestsStore } from '@/stores/requests'
import { openBlobInNewTab } from '@/utils/download'

const route = useRoute()
const store = useRequestsStore()
const assetsStore = useAssetsStore()
const auth = useAuthStore()
const { t } = useI18n()

const request = computed(() => store.currentRequest)
const asset = ref(null)
const decisionNote = ref('')
const deciding = ref(false)
const signedName = ref(auth.user?.full_name || '')
const uploadedFile = ref(null)
const padRef = ref(null)
const signing = ref(false)

function load() {
  store.fetchOne(route.params.id)
}

onMounted(load)
watch(() => route.params.id, load)

watch(
  () => request.value?.asset_id,
  async (assetId) => {
    asset.value = assetId ? (await fetchAssetById(assetId)) : null
  }
)

async function fetchAssetById(assetId) {
  await assetsStore.fetchAsset(assetId)
  return assetsStore.currentAsset
}

const isRequester = computed(() => request.value && auth.user?.id === request.value.requester_id)
const isApprover = computed(
  () =>
    request.value &&
    (auth.user?.role === request.value.approver_role || auth.user?.role === 'admin')
)

const canDecide = computed(() => isApprover.value && request.value?.status === 'pending')

const hasSignedAsRequester = computed(() =>
  request.value?.signatures?.some((s) => s.role_in_flow === 'requester')
)
const hasSignedAsApprover = computed(() =>
  request.value?.signatures?.some((s) => s.role_in_flow === 'approver')
)

const canSign = computed(() => {
  if (!request.value) return false
  if (isRequester.value && !hasSignedAsRequester.value) return true
  if (isApprover.value && !hasSignedAsApprover.value) return true
  return false
})

const signOffMessage = computed(() => {
  if (!request.value) return ''
  if (isRequester.value && hasSignedAsRequester.value) return t('requests.detail.alreadySignedRequester')
  if (isApprover.value && hasSignedAsApprover.value) return t('requests.detail.alreadySignedApprover')
  if (!isRequester.value && !isApprover.value) return t('requests.detail.notYourTurn')
  return ''
})

function formatCurrency(value) {
  return new Intl.NumberFormat('vi-VN').format(value) + 'đ'
}

async function decide(approve) {
  deciding.value = true
  try {
    await store.decide(route.params.id, approve, decisionNote.value || null)
  } finally {
    deciding.value = false
  }
}

function onUploadPick(e) {
  uploadedFile.value = e.target.files?.[0] || null
}

async function submitSignature() {
  if (!signedName.value.trim()) return
  signing.value = true
  try {
    const drawnBlob = await padRef.value?.getBlob()
    const imageBlob = uploadedFile.value || drawnBlob || null
    await store.sign(route.params.id, signedName.value.trim(), imageBlob)
  } finally {
    signing.value = false
  }
}

async function downloadPdf() {
  const blob = await store.fetchPdfBlob(route.params.id)
  openBlobInNewTab(blob)
}
</script>
