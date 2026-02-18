<template>
  <!-- Full-viewport background (fixed, covers everything including behind navbar) -->
  <div class="fixed inset-0 z-0">
    <div class="absolute inset-0 bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900" />
    <canvas ref="canvasRef" class="absolute inset-0 w-full h-full" />
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-gradient-to-r from-blue-500/[0.05] to-violet-500/[0.03] dark:from-blue-500/[0.07] dark:to-violet-500/[0.05] rounded-full blur-3xl pointer-events-none" />
  </div>

  <!-- Content -->
  <div class="relative z-10 h-full flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Card -->
      <div class="bg-white/80 dark:bg-white/[0.04] backdrop-blur-sm border border-gray-200/80 dark:border-white/10 rounded-2xl shadow-sm shadow-black/5 dark:shadow-none ring-1 ring-transparent dark:ring-white/[0.05] p-8">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)

let animationId = null
let onResize = null

onMounted(() => {
  const cvs = canvasRef.value
  if (!cvs) return
  const ctx = cvs.getContext('2d')

  let w = 0
  let h = 0

  const NODE_COUNT = 45
  const MAX_DIST = 140
  const nodes = []

  function resize() {
    w = cvs.offsetWidth
    h = cvs.offsetHeight
    const dpr = window.devicePixelRatio || 1
    cvs.width = w * dpr
    cvs.height = h * dpr
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    for (const n of nodes) {
      n.x = Math.min(n.x, w)
      n.y = Math.min(n.y, h)
    }
  }

  w = cvs.offsetWidth
  h = cvs.offsetHeight
  for (let i = 0; i < NODE_COUNT; i++) {
    nodes.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: 1.5 + Math.random() * 1,
    })
  }
  resize()
  onResize = resize
  window.addEventListener('resize', onResize)

  function isDark() {
    return document.documentElement.classList.contains('dark')
  }

  function draw() {
    ctx.clearRect(0, 0, w, h)
    const dark = isDark()
    const lineRgb = dark ? '129,140,248' : '99,102,241'
    const dotRgb = dark ? '167,139,250' : '99,102,241'
    const baseAlpha = dark ? 0.14 : 0.2

    for (const n of nodes) {
      n.x += n.vx
      n.y += n.vy
      if (n.x <= 0 || n.x >= w) n.vx *= -1
      if (n.y <= 0 || n.y >= h) n.vy *= -1
      n.x = Math.max(0, Math.min(w, n.x))
      n.y = Math.max(0, Math.min(h, n.y))
    }

    ctx.lineWidth = 1
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x
        const dy = nodes[i].y - nodes[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < MAX_DIST) {
          const alpha = (1 - dist / MAX_DIST) * baseAlpha
          ctx.beginPath()
          ctx.moveTo(nodes[i].x, nodes[i].y)
          ctx.lineTo(nodes[j].x, nodes[j].y)
          ctx.strokeStyle = `rgba(${lineRgb},${alpha})`
          ctx.stroke()
        }
      }
    }

    for (const n of nodes) {
      ctx.beginPath()
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${dotRgb},${baseAlpha * 1.6})`
      ctx.fill()
    }

    animationId = requestAnimationFrame(draw)
  }

  draw()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (onResize) window.removeEventListener('resize', onResize)
})
</script>
