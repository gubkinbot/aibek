<template>
  <AuthLayout>
    <h2 class="text-xl font-semibold mb-6 text-center text-gray-900 dark:text-white">{{ t('forgotPassword.title') }}</h2>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ error }}
    </div>
    <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ successMessage }}
    </div>

    <!-- Step 1: Enter email -->
    <form v-if="step === 1" @submit.prevent="handleRequestCode">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('forgotPassword.corporateEmail') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
          </svg>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('forgotPassword.emailPlaceholder')"
          />
        </div>
      </div>
      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 text-white py-2.5 rounded-xl hover:from-blue-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 font-medium"
      >
        {{ loading ? t('forgotPassword.requestingCode') : t('forgotPassword.requestCode') }}
      </button>
    </form>

    <!-- Step 2: Enter code + new password -->
    <form v-else @submit.prevent="handleReset">
      <p class="text-gray-600 dark:text-gray-400 text-sm text-center mb-4">
        {{ t('forgotPassword.codeSentTo') }} <span class="font-medium text-gray-900 dark:text-white">{{ email }}</span>
      </p>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('forgotPassword.codeLabel') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
          </svg>
          <input
            v-model="code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-3 text-center text-2xl tracking-widest bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('forgotPassword.codePlaceholder')"
            autocomplete="one-time-code"
          />
        </div>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('forgotPassword.newPassword') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('forgotPassword.newPasswordPlaceholder')"
          />
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('forgotPassword.confirmPassword') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('forgotPassword.confirmPasswordPlaceholder')"
          />
        </div>
      </div>

      <button
        type="submit"
        :disabled="loading || code.length !== 6"
        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 text-white py-2.5 rounded-xl hover:from-blue-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 font-medium"
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

    <p class="text-sm text-center mt-5 text-gray-600 dark:text-gray-400">
      <router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">{{ t('forgotPassword.backToLogin') }}</router-link>
    </p>
  </AuthLayout>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'
import AuthLayout from '../components/AuthLayout.vue'

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
