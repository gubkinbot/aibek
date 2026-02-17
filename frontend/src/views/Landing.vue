<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
    <h1 class="text-4xl font-bold mb-4">
      {{ t('landing.title') }}
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mb-8">
      {{ t('landing.description') }}
    </p>
    <div class="flex gap-4">
      <router-link
        to="/register"
        class="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg hover:bg-blue-700 transition"
      >
        {{ t('landing.getStarted') }}
      </router-link>
      <router-link
        to="/login"
        class="border border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400 px-6 py-3 rounded-lg text-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 transition"
      >
        {{ t('landing.login') }}
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
