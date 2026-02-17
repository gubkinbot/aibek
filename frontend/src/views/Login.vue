<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <form @submit.prevent="handleLogin" class="bg-white dark:bg-gray-800 shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('login.title') }}</h2>

      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">
        {{ error }}
        <router-link
          v-if="showVerifyLink"
          :to="{ path: '/verify-email', query: { email: email } }"
          class="block mt-2 text-blue-600 dark:text-blue-400 hover:underline"
        >
          {{ t('login.goToVerify') }}
        </router-link>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('login.email') }}</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('login.emailPlaceholder')"
        />
      </div>

      <div class="mb-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('login.password') }}</label>
        <input
          v-model="password"
          type="password"
          required
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('login.passwordPlaceholder')"
        />
      </div>

      <div class="flex justify-end mb-6">
        <router-link to="/forgot-password" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
          {{ t('login.forgotPassword') }}
        </router-link>
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {{ loading ? t('login.submitting') : t('login.submit') }}
      </button>

      <p class="text-sm text-center mt-4 text-gray-600 dark:text-gray-400">
        {{ t('login.noAccount') }}
        <router-link to="/register" class="text-blue-600 dark:text-blue-400 hover:underline">{{ t('login.registerLink') }}</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showVerifyLink = ref(false)

async function handleLogin() {
  error.value = ''
  showVerifyLink.value = false
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    const data = e.response?.data?.detail
    const detail = typeof data === 'object' ? data.message : (data || t('login.defaultError'))
    error.value = detail
    if (typeof data === 'object' && data.code === 'email_not_verified') {
      showVerifyLink.value = true
    }
  } finally {
    loading.value = false
  }
}
</script>
