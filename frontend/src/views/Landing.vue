<template>
  <div class="relative w-full h-dvh flex flex-col items-center justify-center bg-gray-50 dark:bg-[#0a0a0a] transition-colors duration-500 overflow-hidden">
    <!-- Subtle gradient accent -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-blue-500/[0.04] dark:bg-blue-400/[0.06] blur-[120px]" />
    </div>

    <!-- Content -->
    <div class="relative z-10 text-center px-6 max-w-2xl">
      <!-- Logo -->
      <div class="mb-8 flex justify-center">
        <img src="/UTG-dark.svg" alt="UTG" class="h-12 dark:hidden" />
        <img src="/UTG.svg" alt="UTG" class="h-12 hidden dark:block" />
      </div>

      <!-- Title -->
      <h1 class="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white mb-4 leading-tight">
        {{ t('landing.title') }}
      </h1>

      <!-- Description -->
      <p class="text-lg sm:text-xl text-gray-500 dark:text-gray-400 mb-10 leading-relaxed max-w-lg mx-auto">
        {{ t('landing.description') }}
      </p>

      <!-- CTA buttons -->
      <div class="flex items-center justify-center gap-4">
        <router-link
          :to="auth.isAuthenticated ? '/dashboard' : '/register'"
          class="px-6 py-3 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
        >
          {{ t('landing.getStarted') }}
        </router-link>
        <router-link
          v-if="!auth.isAuthenticated"
          to="/login"
          class="px-6 py-3 rounded-xl border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
        >
          {{ t('landing.login') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
</script>
