<template>
  <nav class="bg-white shadow">
    <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
      <router-link to="/" class="text-xl font-bold text-blue-700">
        AI-платформа Узтрансгаз
      </router-link>
      <div class="flex items-center gap-4">
        <template v-if="auth.isAuthenticated">
          <span class="text-sm text-gray-600">{{ auth.user?.email }}</span>
          <button
            @click="handleLogout"
            class="text-sm text-red-600 hover:underline"
          >
            Выйти
          </button>
        </template>
        <template v-else>
          <router-link to="/login" class="text-sm text-blue-600 hover:underline">
            Войти
          </router-link>
          <router-link
            to="/register"
            class="text-sm bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Регистрация
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>
