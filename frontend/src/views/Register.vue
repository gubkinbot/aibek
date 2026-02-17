<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <form @submit.prevent="handleRegister" class="bg-white shadow rounded-lg p-8 w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center">Регистрация</h2>

      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">
        {{ error }}
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Имя</label>
        <input
          v-model="fullName"
          type="text"
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Иван Иванов"
        />
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Корпоративный email</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="name@utg.uz"
        />
        <p class="text-xs text-gray-500 mt-1">Только адреса @utg.uz</p>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Минимум 6 символов"
        />
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">Подтвердите пароль</label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Повторите пароль"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>

      <p class="text-sm text-center mt-4 text-gray-600">
        Уже есть аккаунт?
        <router-link to="/login" class="text-blue-600 hover:underline">Войти</router-link>
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

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (!email.value.endsWith('@utg.uz')) {
    error.value = 'Разрешена регистрация только с корпоративной почтой @utg.uz'
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'Пароли не совпадают'
    return
  }

  loading.value = true
  try {
    await auth.register(email.value, password.value, fullName.value || null)
    router.push({ path: '/verify-email', query: { email: email.value } })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
