<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="bg-white shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-2 text-center">Подтверждение email</h2>
      <p class="text-gray-600 text-sm text-center mb-6">
        Мы отправили 6-значный код на<br />
        <span class="font-medium text-gray-900">{{ email }}</span>
      </p>

      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">
        {{ error }}
      </div>

      <div v-if="successMessage" class="bg-green-50 text-green-600 p-3 rounded mb-4 text-sm">
        {{ successMessage }}
      </div>

      <form @submit.prevent="handleVerify">
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-1">Код подтверждения</label>
          <input
            v-model="code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            required
            class="w-full border rounded px-3 py-3 text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="000000"
            autocomplete="one-time-code"
          />
        </div>

        <button
          type="submit"
          :disabled="loading || code.length !== 6"
          class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ loading ? 'Проверка...' : 'Подтвердить' }}
        </button>
      </form>

      <div class="text-center mt-4">
        <button
          @click="handleResend"
          :disabled="resendCooldown > 0"
          class="text-sm text-blue-600 hover:underline disabled:text-gray-400 disabled:no-underline"
        >
          {{ resendCooldown > 0 ? `Отправить повторно (${resendCooldown}с)` : 'Отправить код повторно' }}
        </button>
      </div>

      <p class="text-sm text-center mt-4 text-gray-600">
        <router-link to="/register" class="text-blue-600 hover:underline">
          Вернуться к регистрации
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref(route.query.email || '')
const code = ref('')
const error = ref('')
const successMessage = ref('')
const loading = ref(false)
const resendCooldown = ref(0)
let cooldownInterval = null

onMounted(() => {
  if (!email.value) {
    router.push('/register')
    return
  }
  startCooldown()
})

onUnmounted(() => {
  if (cooldownInterval) clearInterval(cooldownInterval)
})

function startCooldown() {
  resendCooldown.value = 60
  cooldownInterval = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(cooldownInterval)
      cooldownInterval = null
    }
  }, 1000)
}

async function handleVerify() {
  error.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    await auth.verifyEmail(email.value, code.value)
    successMessage.value = 'Email успешно подтверждён! Перенаправление...'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка подтверждения'
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  error.value = ''
  successMessage.value = ''

  try {
    const data = await auth.resendCode(email.value)
    successMessage.value = data.message
    startCooldown()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка отправки кода'
  }
}
</script>
