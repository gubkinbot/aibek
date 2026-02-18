<template>
  <AuthLayout>
    <h2 class="text-xl font-semibold mb-6 text-center text-gray-900 dark:text-white">{{ t('register.title') }}</h2>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ error }}
    </div>

    <form @submit.prevent="handleRegister">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('register.name') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0" />
          </svg>
          <input
            v-model="fullName"
            type="text"
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('register.namePlaceholder')"
          />
        </div>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('register.corporateEmail') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
          </svg>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('register.emailPlaceholder')"
          />
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1.5 ml-1">{{ t('register.emailHint') }}</p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('register.password') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('register.passwordPlaceholder')"
          />
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('register.confirmPassword') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('register.confirmPasswordPlaceholder')"
          />
        </div>
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 text-white py-2.5 rounded-xl hover:from-blue-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 font-medium"
      >
        {{ loading ? t('register.submitting') : t('register.submit') }}
      </button>
    </form>

    <p class="text-sm text-center mt-5 text-gray-600 dark:text-gray-400">
      {{ t('register.hasAccount') }}
      <router-link to="/login" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">{{ t('register.loginLink') }}</router-link>
    </p>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'
import AuthLayout from '../components/AuthLayout.vue'

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
