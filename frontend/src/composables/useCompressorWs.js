import { ref, onUnmounted, watch } from 'vue'
import { useCompressorStore } from '../stores/compressor'

/**
 * WebSocket composable для реалтайм-данных компрессорной станции.
 *
 * @param {import('vue').Ref<string>} stationCode — реактивный код станции
 * @returns {{ connected: Ref<boolean>, error: Ref<string|null> }}
 */
export function useCompressorWs(stationCode) {
  const connected = ref(false)
  const error = ref(null)
  const store = useCompressorStore()

  let ws = null
  let reconnectTimer = null
  let backoff = 1000

  function connect(code) {
    if (!code) return
    cleanup()

    const token = localStorage.getItem('token')
    if (!token) {
      error.value = 'No auth token'
      return
    }

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${proto}//${location.host}/api/modules/compressor/ws/${code}?token=${token}`

    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      error.value = null
      backoff = 1000
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        store.handleWsMessage(msg)
      } catch (e) {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      error.value = 'WebSocket error'
    }

    ws.onclose = (event) => {
      connected.value = false
      if (event.code === 4001) {
        error.value = 'Unauthorized'
        return
      }
      if (event.code === 4004) {
        error.value = 'Station not found'
        return
      }
      // Auto-reconnect
      reconnectTimer = setTimeout(() => {
        backoff = Math.min(backoff * 2, 30000)
        connect(code)
      }, backoff)
    }
  }

  function cleanup() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    connected.value = false
  }

  // Следим за изменением кода станции
  watch(
    () => (typeof stationCode === 'function' ? stationCode() : stationCode.value),
    (newCode) => {
      if (newCode) {
        connect(newCode)
      } else {
        cleanup()
      }
    },
    { immediate: true },
  )

  onUnmounted(cleanup)

  return { connected, error }
}
