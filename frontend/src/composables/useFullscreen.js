import { ref, onMounted, onUnmounted } from 'vue'

const isFullscreen = ref(false)

function update() {
  isFullscreen.value = !!(
    document.fullscreenElement ||
    document.webkitFullscreenElement
  )
}

export function useFullscreen() {
  function toggle() {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      ;(document.exitFullscreen || document.webkitExitFullscreen).call(document)
    } else {
      const el = document.documentElement
      ;(el.requestFullscreen || el.webkitRequestFullscreen).call(el)
    }
  }

  function exit() {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      ;(document.exitFullscreen || document.webkitExitFullscreen).call(document)
    }
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', update)
    document.addEventListener('webkitfullscreenchange', update)
  })

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', update)
    document.removeEventListener('webkitfullscreenchange', update)
  })

  return { isFullscreen, toggle, exit }
}
