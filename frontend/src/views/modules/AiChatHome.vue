<template>
  <div class="w-[80%] mx-auto py-8">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
        <svg class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">{{ t('modules.ai_chat.name') }}</h1>
    </div>

    <!-- Access Level Info -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
      <div class="flex items-center gap-3 mb-4">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ t('modules.accessLevel') }}</span>
        <span :class="['inline-block px-3 py-1 rounded-full text-xs font-medium', levelBadgeClass]">{{ levelName }}</span>
      </div>
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{{ t('modules.capabilities') }}</h3>
        <ul class="space-y-1.5">
          <li v-for="cap in capabilities" :key="cap" class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <svg class="w-4 h-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {{ cap }}
          </li>
        </ul>
      </div>
    </div>

    <p class="text-gray-500 dark:text-gray-400 text-lg">{{ t('modules.comingSoon') }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const moduleName = 'ai_chat'

const accessLevel = computed(() => {
  if (auth.isSuperAdmin) return 'superadmin'
  return auth.user?.module_access?.[moduleName] || 'viewer'
})

const levelName = computed(() => t(`modules.levelNames.${accessLevel.value}`))

const levelBadgeClass = computed(() => {
  const classes = {
    viewer: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    operator: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    manager: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    admin: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    superadmin: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  }
  return classes[accessLevel.value] || classes.viewer
})

const capabilities = computed(() => {
  const level = accessLevel.value
  const caps = []
  if (level === 'superadmin') {
    caps.push(t('modules.capabilityList.full'))
    return caps
  }
  caps.push(t('modules.capabilityList.view'))
  if (['operator', 'manager', 'admin'].includes(level)) caps.push(t('modules.capabilityList.edit'))
  if (['manager', 'admin'].includes(level)) caps.push(t('modules.capabilityList.manage'))
  if (level === 'admin') caps.push(t('modules.capabilityList.admin'))
  return caps
})
</script>
