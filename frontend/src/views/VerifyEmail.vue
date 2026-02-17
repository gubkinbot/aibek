<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-2 text-center">{{ t('verifyEmail.title') }}</h2>
      <p class="text-gray-600 dark:text-gray-400 text-sm text-center mb-6">
        {{ t('verifyEmail.codeSentTo') }}<br />
        <span class="font-medium text-gray-900 dark:text-white">{{ email }}</span>
      </p>

      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">
        {{ error }}
      </div>

      <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded mb-4 text-sm">
        {{ successMessage }}
      </div>

      <form @submit.prevent="handleVerify">
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('verifyEmail.codeLabel') }}</label>
          <input
            v-model="code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-3 text-center text-2xl tracking-widest bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('verifyEmail.codePlaceholder')"
            autocomplete="one-time-code"
          />
        </div>

        <button
          type="submit"
          :disabled="loading || code.length !== 6"
          class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ loading ? t('verifyEmail.submitting') : t('verifyEmail.submit') }}
        </button>
      </form>

      <div class="text-center mt-4">
        <button
          @click="handleResend"
          :disabled="resendCooldown > 0"
          class="text-sm text-blue-600 dark:text-blue-400 hover:underline disabled:text-gray-400 dark:disabled:text-gray-600 disabled:no-underline"
        >
          {{ resendCooldown > 0 ? t('verifyEmail.resendCountdown', { seconds: resendCooldown }) : t('verifyEmail.resend') }}
        </button>
      </div>

      <p class="text-sm text-center mt-4 text-gray-600 dark:text-gray-400">
        <router-link to="/register" class="text-blue-600 dark:text-blue-400 hover:underline">
          {{ t('verifyEmail.backToRegister') }}
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

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
    successMessage.value = t('verifyEmail.success')
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || t('verifyEmail.defaultError')
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
    error.value = e.response?.data?.detail || t('verifyEmail.resendError')
  }
}
</script>
