<template>
  <canvas
    ref="canvasRef"
    width="400"
    height="150"
    class="border border-gray-300 rounded bg-white touch-none w-full max-w-sm cursor-crosshair"
    @pointerdown="start"
    @pointermove="draw"
    @pointerup="end"
    @pointerleave="end"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'

const canvasRef = ref(null)
let ctx = null
let drawing = false
let hasDrawing = false

onMounted(() => {
  ctx = canvasRef.value.getContext('2d')
  ctx.strokeStyle = '#111827'
  ctx.lineWidth = 2
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
})

function pos(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height
  return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY }
}

function start(e) {
  drawing = true
  const { x, y } = pos(e)
  ctx.beginPath()
  ctx.moveTo(x, y)
}

function draw(e) {
  if (!drawing) return
  const { x, y } = pos(e)
  ctx.lineTo(x, y)
  ctx.stroke()
  hasDrawing = true
}

function end() {
  drawing = false
}

function clear() {
  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  hasDrawing = false
}

function getBlob() {
  return new Promise((resolve) => {
    if (!hasDrawing) {
      resolve(null)
      return
    }
    canvasRef.value.toBlob((blob) => resolve(blob), 'image/png')
  })
}

defineExpose({ clear, getBlob })
</script>
