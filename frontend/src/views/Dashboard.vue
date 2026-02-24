<template>
  <div class="w-[80%] mx-auto py-12">
    <h1 class="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
      {{ auth.user?.full_name ? t('dashboard.welcomeUser', { name: auth.user.full_name }) : t('dashboard.welcome') }}
    </h1>

    <!-- Module cards -->
    <div v-if="availableModules.length">
      <h2 class="text-sm font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4">{{ t('dashboard.yourModules') }}</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <router-link
          v-for="mod in availableModules"
          :key="mod.key"
          :to="mod.route"
          class="group relative rounded-2xl border border-gray-200/60 dark:border-white/[0.06] bg-white/60 dark:bg-white/[0.03] backdrop-blur-sm p-6 transition-all hover:shadow-lg hover:shadow-gray-200/40 dark:hover:shadow-black/20 hover:border-gray-300 dark:hover:border-white/[0.12] hover:-translate-y-0.5"
        >
          <div :class="['w-11 h-11 rounded-xl flex items-center justify-center mb-4', mod.bgClass]">
            <svg :class="['w-5 h-5', mod.iconClass]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" :d="mod.icon" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">{{ t(`modules.${mod.key}.name`) }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ t(`modules.${mod.key}.description`) }}</p>
        </router-link>
      </div>
    </div>

    <div v-else class="text-center py-16">
      <svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <p class="text-gray-500 dark:text-gray-400">{{ t('dashboard.noModules') }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const { t } = useI18n()

const modules = [
  {
    key: 'compressor',
    route: '/compressor',
    permission: 'compressor.access',
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    bgClass: 'bg-orange-100 dark:bg-orange-900/30',
    iconClass: 'text-orange-600 dark:text-orange-400',
  },
  {
    key: 'balance',
    route: '/balance',
    permission: 'balance.access',
    icon: 'M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3',
    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
    iconClass: 'text-blue-600 dark:text-blue-400',
  },
  {
    key: 'weather',
    route: '/weather',
    permission: 'weather.access',
    icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z',
    bgClass: 'bg-cyan-100 dark:bg-cyan-900/30',
    iconClass: 'text-cyan-600 dark:text-cyan-400',
  },
  {
    key: 'digital',
    route: '/digital',
    permission: 'digital.access',
    icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    iconClass: 'text-purple-600 dark:text-purple-400',
  },
  {
    key: 'ai_chat',
    route: '/ai-chat',
    permission: 'ai_chat.access',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    bgClass: 'bg-green-100 dark:bg-green-900/30',
    iconClass: 'text-green-600 dark:text-green-400',
  },
  {
    key: 'scada',
    route: '/scada',
    permission: 'scada.access',
    icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4',
    bgClass: 'bg-red-100 dark:bg-red-900/30',
    iconClass: 'text-red-600 dark:text-red-400',
  },
]

const availableModules = computed(() =>
  modules.filter(m => auth.hasPermission(m.permission))
)
</script>
