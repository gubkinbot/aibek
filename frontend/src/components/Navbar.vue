<template>
  <nav :class="[
    'z-30 transition-all duration-500',
    isAuthPage || isLandingPage
      ? 'absolute top-0 left-0 right-0 bg-transparent border-transparent'
      : 'relative border-b bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-gray-200/50 dark:border-white/[0.06]',
    isFullscreen && isLandingPage
      ? 'opacity-0 pointer-events-none'
      : 'opacity-100'
  ]">
    <div class="px-6 py-3 flex items-center justify-between">
      <!-- Logo + Brand -->
      <router-link to="/" class="flex items-center">
        <img src="/UTG-dark.svg" alt="UTG" class="h-8 dark:hidden" />
        <img src="/UTG.svg" alt="UTG" class="h-8 hidden dark:block" />
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
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
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
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
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

        <!-- Fullscreen toggle (only on Landing page) -->
        <button
          v-if="isLandingPage"
          @click="toggleFullscreen()"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
        >
          <svg v-if="!isFullscreen" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
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
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
        @click="sidebarOpen = false"
      />
    </Transition>

    <Transition name="sidebar-panel">
      <div
        v-if="sidebarOpen"
        class="fixed top-0 right-0 h-full w-80 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-l border-gray-200/50 dark:border-white/[0.06] shadow-2xl z-50 flex flex-col"
      >
        <!-- Header: user info -->
        <div class="px-4 pt-4 pb-2">
          <template v-if="auth.isAuthenticated && auth.user">
            <button
              @click="profileMenuOpen = !profileMenuOpen"
              class="flex items-center gap-3 w-full min-w-0 rounded-xl px-3 py-2.5 hover:bg-white/50 dark:hover:bg-white/10 transition-all"
            >
              <div class="w-11 h-11 shrink-0 rounded-full bg-gray-100 dark:bg-gray-700 p-1.5 text-gray-500 dark:text-gray-300">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="w-full h-full">
                  <circle cx="12" cy="8" r="4.5" />
                  <path d="M3.5 21.5c0-4.7 3.8-8.5 8.5-8.5s8.5 3.8 8.5 8.5" />
                </svg>
              </div>
              <div class="min-w-0 text-left flex-1">
                <div class="font-semibold text-gray-900 dark:text-white truncate">
                  {{ auth.user?.full_name || auth.user?.email }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {{ auth.user?.email }}
                </div>
              </div>
              <svg
                :class="['w-4 h-4 shrink-0 text-gray-400 dark:text-gray-500 transition-transform duration-200', profileMenuOpen ? 'rotate-180' : '']"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </template>
        </div>

        <!-- Profile dropdown menu -->
        <Transition name="profile-menu">
          <div v-if="auth.isAuthenticated && auth.user && profileMenuOpen" class="px-4 pb-2 space-y-0.5">
            <router-link
              to="/settings"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all text-sm"
              active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {{ t('navbar.settings') }}
            </router-link>
            <button
              @click="handleLogout"
              class="flex items-center gap-3 w-full px-3 py-2 rounded-xl text-red-500 dark:text-red-400 hover:bg-red-500/10 dark:hover:bg-red-400/10 transition-all text-sm"
            >
              <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ t('navbar.logout') }}
            </button>
          </div>
        </Transition>

        <!-- Authenticated user content -->
        <template v-if="auth.isAuthenticated && auth.user">

          <div class="border-t border-gray-200/50 dark:border-white/[0.06] mx-5" />

          <!-- Navigation -->
          <nav class="flex-1 px-4 py-4 space-y-1">
            <router-link
              to="/dashboard"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
              active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" />
              </svg>
              {{ t('navbar.dashboard') }}
            </router-link>

            <!-- Admin section -->
            <template v-if="auth.isAdmin">
              <div class="border-t border-gray-200/50 dark:border-white/[0.06] my-2" />
              <p class="px-3 py-1 text-[11px] font-semibold text-gray-400/80 dark:text-gray-500 uppercase tracking-widest">{{ t('navbar.administration') }}</p>

              <router-link to="/admin/users"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                {{ t('navbar.adminUsers') }}
              </router-link>

              <router-link to="/admin/roles"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                {{ t('navbar.adminRoles') }}
              </router-link>

              <router-link to="/admin/groups"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                {{ t('navbar.adminGroups') }}
              </router-link>

              <router-link to="/admin/departments"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                {{ t('navbar.adminDepartments') }}
              </router-link>

              <router-link to="/admin/audit-logs"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                {{ t('navbar.adminAuditLogs') }}
              </router-link>

              <router-link to="/admin/system"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
                active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                </svg>
                {{ t('navbar.adminSystem') }}
              </router-link>
            </template>
          </nav>

        </template>

        <!-- Not authenticated content -->
        <template v-if="!auth.isAuthenticated">
          <nav class="flex-1 px-4 py-4 space-y-1">
            <router-link
              to="/login"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
              active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ t('navbar.login') }}
            </router-link>

            <router-link
              to="/register"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-white/60 dark:hover:bg-white/10 transition-all"
              active-class="bg-blue-500/10 dark:bg-blue-400/10 !text-blue-600 dark:!text-blue-400 font-medium"
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
import { useFullscreen } from '../composables/useFullscreen'
import { useI18n } from 'vue-i18n'

const auth = useAuthStore()
const themeStore = useThemeStore()
const { isFullscreen, toggle: toggleFullscreen } = useFullscreen()
const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const sidebarOpen = ref(false)
const profileMenuOpen = ref(false)

const authRoutes = ['/login', '/register', '/forgot-password', '/verify-email']
const isAuthPage = computed(() => authRoutes.includes(route.path))
const isLandingPage = computed(() => route.path === '/')

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
  profileMenuOpen.value = false
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

/* Profile menu transition */
.profile-menu-enter-active,
.profile-menu-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.profile-menu-enter-from,
.profile-menu-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.profile-menu-enter-to,
.profile-menu-leave-from {
  opacity: 1;
  max-height: 120px;
}
</style>
