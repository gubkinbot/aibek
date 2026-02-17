<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <form @submit.prevent="handleRegister" class="bg-white dark:bg-gray-800 shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('register.title') }}</h2>

      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">
        {{ error }}
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('register.name') }}</label>
        <input
          v-model="fullName"
          type="text"
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('register.namePlaceholder')"
        />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('register.corporateEmail') }}</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('register.emailPlaceholder')"
        />
        <p class="text-xs text-gray-500 mt-1">{{ t('register.emailHint') }}</p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('register.password') }}</label>
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('register.passwordPlaceholder')"
        />
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('register.confirmPassword') }}</label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="t('register.confirmPasswordPlaceholder')"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {{ loading ? t('register.submitting') : t('register.submit') }}
      </button>

      <p class="text-sm text-center mt-4 text-gray-600 dark:text-gray-400">
        {{ t('register.hasAccount') }}
        <router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline">{{ t('register.loginLink') }}</router-link>
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

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (!email.value.endsWith('@utg.uz')) {
    error.value = t('register.errorOnlyUtg')
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = t('register.errorPasswordMismatch')
    return
  }

  loading.value = true
  try {
    await auth.register(email.value, password.value, fullName.value || null)
    router.push({ path: '/verify-email', query: { email: email.value } })
  } catch (e) {
    error.value = e.response?.data?.detail || t('register.defaultError')
  } finally {
    loading.value = false
  }
}
</script>
