<template>
  <nav class="bg-white dark:bg-gray-800 shadow relative z-30">
    <div class="px-6 py-3 flex items-center justify-between">
      <!-- Logo + Brand -->
      <router-link to="/" class="flex items-center gap-2 text-xl font-bold text-blue-700 dark:text-blue-400">
        <svg class="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2" />
          <circle cx="16" cy="10" r="2.5" fill="currentColor" />
          <circle cx="10" cy="20" r="2.5" fill="currentColor" />
          <circle cx="22" cy="20" r="2.5" fill="currentColor" />
          <line x1="16" y1="12.5" x2="10" y2="17.5" stroke="currentColor" stroke-width="1.5" />
          <line x1="16" y1="12.5" x2="22" y2="17.5" stroke="currentColor" stroke-width="1.5" />
          <line x1="10" y1="20" x2="22" y2="20" stroke="currentColor" stroke-width="1.5" />
        </svg>
        <span class="hidden sm:inline">{{ t('navbar.brand') }}</span>
      </router-link>

      <!-- Right controls -->
      <div class="flex items-center gap-2">
        <!-- Language switcher -->
        <div class="flex rounded-lg overflow-hidden">
          <button
            @click="changeLocale('ru')"
            :class="[
              'px-2.5 py-1 text-xs font-medium transition-colors',
              locale === 'ru'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
            ]"
          >
            RU
          </button>
          <button
            @click="changeLocale('uz')"
            :class="[
              'px-2.5 py-1 text-xs font-medium transition-colors',
              locale === 'uz'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
            ]"
          >
            UZ
          </button>
        </div>

        <!-- Theme toggle -->
        <button
          @click="themeStore.toggleTheme()"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
        >
          <!-- Sun icon (shown in dark mode → click to go light) -->
          <svg v-if="themeStore.theme === 'dark'" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
          </svg>
          <!-- Moon icon (shown in light mode → click to go dark) -->
          <svg v-else class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
          </svg>
        </button>

        <!-- Hamburger menu button -->
        <button
          @click="sidebarOpen = true"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </div>
  </nav>

  <!-- Sidebar overlay -->
  <Teleport to="body">
    <Transition name="sidebar-backdrop">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 bg-black/50 z-40"
        @click="sidebarOpen = false"
      />
    </Transition>

    <Transition name="sidebar-panel">
      <div
        v-if="sidebarOpen"
        class="fixed top-0 right-0 h-full w-80 bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col"
      >
        <!-- Header: user info + close button -->
        <div class="flex items-center justify-between px-5 py-4">
          <template v-if="auth.isAuthenticated && auth.user">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5 text-gray-500 dark:text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="font-semibold text-gray-900 dark:text-white truncate">
                  {{ auth.user?.full_name || auth.user?.email }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {{ auth.user?.email }}
                </div>
              </div>
            </div>
          </template>
          <div v-else />
          <button
            @click="sidebarOpen = false"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors shrink-0 ml-2"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Authenticated user content -->
        <template v-if="auth.isAuthenticated && auth.user">

          <div class="border-t border-gray-200 dark:border-gray-700 mx-6" />

          <!-- Navigation -->
          <nav class="flex-1 px-4 py-4 space-y-1">
            <router-link
              to="/dashboard"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" />
              </svg>
              {{ t('navbar.dashboard') }}
            </router-link>

            <router-link
              to="/settings"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {{ t('navbar.settings') }}
            </router-link>

            <!-- Admin section -->
            <template v-if="auth.isAdmin">
              <div class="border-t border-gray-200 dark:border-gray-700 my-2" />
              <p class="px-3 py-1 text-xs font-bold text-gray-400 uppercase tracking-wider">{{ t('navbar.administration') }}</p>

              <router-link to="/admin/users"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                {{ t('navbar.adminUsers') }}
              </router-link>

              <router-link to="/admin/roles"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                {{ t('navbar.adminRoles') }}
              </router-link>

              <router-link to="/admin/groups"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                {{ t('navbar.adminGroups') }}
              </router-link>

              <router-link to="/admin/departments"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                {{ t('navbar.adminDepartments') }}
              </router-link>

              <router-link to="/admin/audit-logs"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                {{ t('navbar.adminAuditLogs') }}
              </router-link>
            </template>
          </nav>

          <div class="border-t border-gray-200 dark:border-gray-700 mx-6" />

          <!-- Logout -->
          <div class="px-4 py-4">
            <button
              @click="handleLogout"
              class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ t('navbar.logout') }}
            </button>
          </div>
        </template>

        <!-- Not authenticated content -->
        <template v-if="!auth.isAuthenticated">
          <nav class="flex-1 px-4 py-4 space-y-1">
            <router-link
              to="/login"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ t('navbar.login') }}
            </router-link>

            <router-link
              to="/register"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              active-class="bg-blue-50 dark:bg-blue-900/30 !text-blue-700 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
              {{ t('navbar.register') }}
            </router-link>
          </nav>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const themeStore = useThemeStore()
const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const sidebarOpen = ref(false)

const userInitials = computed(() => {
  const name = auth.user?.full_name
  if (name) {
    const parts = name.trim().split(/\s+/)
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return parts[0][0].toUpperCase()
  }
  const email = auth.user?.email
  if (email) return email[0].toUpperCase()
  return 'U'
})

// Close sidebar on route change
watch(() => route.path, () => {
  sidebarOpen.value = false
})

function handleLogout() {
  sidebarOpen.value = false
  auth.logout()
  router.push('/')
}

function changeLocale(lang) {
  locale.value = lang
  localStorage.setItem('locale', lang)
  document.documentElement.lang = lang
  document.title = t('pageTitle')
}
</script>

<style scoped>
/* Backdrop transition */
.sidebar-backdrop-enter-active,
.sidebar-backdrop-leave-active {
  transition: opacity 0.3s ease;
}
.sidebar-backdrop-enter-from,
.sidebar-backdrop-leave-to {
  opacity: 0;
}

/* Panel slide transition */
.sidebar-panel-enter-active,
.sidebar-panel-leave-active {
  transition: transform 0.3s ease;
}
.sidebar-panel-enter-from,
.sidebar-panel-leave-to {
  transform: translateX(100%);
}
</style>
