<template>
  <AuthLayout>
    <h2 class="text-xl font-semibold mb-2 text-center text-gray-900 dark:text-white">{{ t('verifyEmail.title') }}</h2>
    <p class="text-gray-600 dark:text-gray-400 text-sm text-center mb-6">
      {{ t('verifyEmail.codeSentTo') }}<br />
      <span class="font-medium text-gray-900 dark:text-white">{{ email }}</span>
    </p>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ error }}
    </div>

    <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ successMessage }}
    </div>

    <form @submit.prevent="handleVerify">
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('verifyEmail.codeLabel') }}</label>
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
            class="w-full border border-gray-200/80 dark:border-white/10 rounded-xl pl-10 pr-4 py-3 text-center text-2xl tracking-widest bg-white/50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 shadow-[0_0_0_0px_transparent] focus:shadow-[0_0_0_3px_rgba(59,130,246,0.12)] dark:focus:shadow-[0_0_0_3px_rgba(96,165,250,0.1)] focus:outline-none focus:border-blue-500/50 dark:focus:border-blue-400/40 transition-[border-color,box-shadow] duration-200"
            :placeholder="t('verifyEmail.codePlaceholder')"
            autocomplete="one-time-code"
          />
        </div>
      </div>

      <button
        type="submit"
        :disabled="loading || code.length !== 6"
        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 text-white py-2.5 rounded-xl hover:from-blue-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 font-medium"
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
      <router-link to="/register" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">
        {{ t('verifyEmail.backToRegister') }}
      </router-link>
    </p>
  </AuthLayout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'
import AuthLayout from '../components/AuthLayout.vue'

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
