<template>
  <AuthLayout>
    <h2 class="text-xl font-semibold mb-6 text-center text-gray-900 dark:text-white">{{ t('login.title') }}</h2>

    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl mb-4 text-sm text-center">
      {{ error }}
      <router-link
        v-if="showVerifyLink"
        :to="{ path: '/verify-email', query: { email: email } }"
        class="block mt-2 text-blue-600 dark:text-blue-400 hover:underline"
      >
        {{ t('login.goToVerify') }}
      </router-link>
    </div>

    <form @submit.prevent="handleLogin">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('login.email') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
          </svg>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('login.emailPlaceholder')"
          />
        </div>
      </div>

      <div class="mb-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ t('login.password') }}</label>
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <input
            v-model="password"
            type="password"
            required
            class="w-full border border-gray-200 dark:border-gray-600 rounded-xl pl-10 pr-4 py-2.5 bg-white/50 dark:bg-gray-700/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
            :placeholder="t('login.passwordPlaceholder')"
          />
        </div>
      </div>

      <div class="flex justify-end mb-6">
        <router-link to="/forgot-password" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
          {{ t('login.forgotPassword') }}
        </router-link>
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 text-white py-2.5 rounded-xl hover:from-blue-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-500/40 font-medium"
      >
        {{ loading ? t('login.submitting') : t('login.submit') }}
      </button>
    </form>

    <p class="text-sm text-center mt-5 text-gray-600 dark:text-gray-400">
      {{ t('login.noAccount') }}
      <router-link to="/register" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">{{ t('login.registerLink') }}</router-link>
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
