<template>
  <div class="max-w-4xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-4">
      Добро пожаловать{{ auth.user?.full_name ? `, ${auth.user.full_name}` : '' }}!
    </h1>
    <p class="text-gray-600 text-lg">
      Это панель управления AI-платформой АО «Узтрансгаз». Функционал будет расширяться.
    </p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

onMounted(() => {
  if (!auth.user) {
    auth.fetchUser()
  }
})
</script>
