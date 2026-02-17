<template>
  <div class="max-w-4xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-4">
      {{ auth.user?.full_name ? t('dashboard.welcomeUser', { name: auth.user.full_name }) : t('dashboard.welcome') }}
    </h1>
    <p class="text-gray-600 dark:text-gray-400 text-lg">
      {{ t('dashboard.description') }}
    </p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const { t } = useI18n()

onMounted(() => {
  if (!auth.user) {
    auth.fetchUser()
  }
})
</script>
