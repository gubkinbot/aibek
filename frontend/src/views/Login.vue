<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <form @submit.prevent="handleLogin" class="bg-white shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center">Вход</h2>

      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">
        {{ error }}
        <router-link
          v-if="showVerifyLink"
          :to="{ path: '/verify-email', query: { email: email } }"
          class="block mt-2 text-blue-600 hover:underline"
        >
          Перейти к подтверждению email
        </router-link>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="name@utg.uz"
        />
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
        <input
          v-model="password"
          type="password"
          required
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Введите пароль"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>

      <p class="text-sm text-center mt-4 text-gray-600">
        Нет аккаунта?
        <router-link to="/register" class="text-blue-600 hover:underline">Зарегистрироваться</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

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
    const status = e.response?.status
    const detail = e.response?.data?.detail || 'Ошибка входа'
    error.value = detail
    if (status === 403 && detail.includes('не подтверждён')) {
      showVerifyLink.value = true
    }
  } finally {
    loading.value = false
  }
}
</script>
