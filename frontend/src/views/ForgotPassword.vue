<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('forgotPassword.title') }}</h2>

      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">
        {{ error }}
      </div>
      <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded mb-4 text-sm">
        {{ successMessage }}
      </div>

      <!-- Шаг 1: Ввод email -->
      <form v-if="step === 1" @submit.prevent="handleRequestCode">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('forgotPassword.corporateEmail') }}</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('forgotPassword.emailPlaceholder')"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ loading ? t('forgotPassword.requestingCode') : t('forgotPassword.requestCode') }}
        </button>
      </form>

      <!-- Шаг 2: Ввод кода + новый пароль -->
      <form v-else @submit.prevent="handleReset">
        <p class="text-gray-600 dark:text-gray-400 text-sm text-center mb-4">
          {{ t('forgotPassword.codeSentTo') }} <span class="font-medium text-gray-900 dark:text-white">{{ email }}</span>
        </p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('forgotPassword.codeLabel') }}</label>
          <input
            v-model="code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-3 text-center text-2xl tracking-widest bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('forgotPassword.codePlaceholder')"
            autocomplete="one-time-code"
          />
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('forgotPassword.newPassword') }}</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('forgotPassword.newPasswordPlaceholder')"
          />
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('forgotPassword.confirmPassword') }}</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('forgotPassword.confirmPasswordPlaceholder')"
          />
        </div>

        <button
          type="submit"
          :disabled="loading || code.length !== 6"
          class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ loading ? t('forgotPassword.submitting') : t('forgotPassword.submit') }}
        </button>

        <div class="text-center mt-4">
          <button
            @click="handleResend"
            :disabled="resendCooldown > 0"
            type="button"
            class="text-sm text-blue-600 dark:text-blue-400 hover:underline disabled:text-gray-400 dark:disabled:text-gray-600 disabled:no-underline"
          >
            {{ resendCooldown > 0 ? t('forgotPassword.resendCountdown', { seconds: resendCooldown }) : t('forgotPassword.resend') }}
          </button>
        </div>
      </form>

      <p class="text-sm text-center mt-4 text-gray-600 dark:text-gray-400">
        <router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline">{{ t('forgotPassword.backToLogin') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

const step = ref(1)
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const successMessage = ref('')
const loading = ref(false)
const resendCooldown = ref(0)
let cooldownInterval = null

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

async function handleRequestCode() {
  error.value = ''
  successMessage.value = ''
  loading.value = true
  try {
    const data = await auth.forgotPassword(email.value)
    successMessage.value = data.message
    step.value = 2
    startCooldown()
  } catch (e) {
    error.value = e.response?.data?.detail || t('forgotPassword.sendError')
  } finally {
    loading.value = false
  }
}

async function handleReset() {
  error.value = ''
  successMessage.value = ''

  if (newPassword.value !== confirmPassword.value) {
    error.value = t('forgotPassword.errorPasswordMismatch')
    return
  }

  loading.value = true
  try {
    await auth.resetPassword(email.value, code.value, newPassword.value)
    successMessage.value = t('forgotPassword.success')
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || t('forgotPassword.defaultError')
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  error.value = ''
  successMessage.value = ''
  try {
    const data = await auth.forgotPassword(email.value)
    successMessage.value = data.message
    startCooldown()
  } catch (e) {
    error.value = e.response?.data?.detail || t('forgotPassword.sendError')
  }
}
</script>
