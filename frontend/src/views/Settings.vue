<template>
  <div class="max-w-4xl mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-8">{{ t('settings.title') }}</h1>

    <!-- Профиль -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-8 mb-6">
      <h2 class="text-xl font-bold mb-4">{{ t('settings.profile') }}</h2>

      <div class="mb-4">
        <span class="text-sm text-gray-500">{{ t('settings.emailLabel') }}</span>
        <span class="ml-2 text-gray-900 dark:text-white">{{ auth.user?.email }}</span>
      </div>
      <div class="mb-4">
        <span class="text-sm text-gray-500">{{ t('settings.rolesLabel') }}</span>
        <span v-if="auth.user?.roles?.length" class="ml-2">
          <span v-for="role in auth.user.roles" :key="role"
            class="inline-block px-2 py-0.5 rounded text-xs mr-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
            {{ role }}
          </span>
        </span>
        <span v-else class="ml-2 text-gray-400 text-sm">-</span>
      </div>
      <div class="mb-6">
        <span class="text-sm text-gray-500">{{ t('settings.registrationDate') }}</span>
        <span class="ml-2 text-gray-900 dark:text-white">{{ formatDate(auth.user?.created_at) }}</span>
      </div>

      <div v-if="profileError" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ profileError }}</div>
      <div v-if="profileSuccess" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ profileSuccess }}</div>

      <form @submit.prevent="handleUpdateProfile">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.name') }}</label>
          <input
            v-model="fullName"
            type="text"
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('settings.namePlaceholder')"
          />
        </div>
        <button
          type="submit"
          :disabled="profileLoading"
          class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ profileLoading ? t('settings.savingProfile') : t('settings.saveProfile') }}
        </button>
      </form>
    </div>

    <!-- Смена пароля -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-8">
      <h2 class="text-xl font-bold mb-4">{{ t('settings.changePassword') }}</h2>

      <div v-if="passwordError" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ passwordError }}</div>
      <div v-if="passwordSuccess" class="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ passwordSuccess }}</div>

      <form @submit.prevent="handleChangePassword">
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.currentPassword') }}</label>
          <input
            v-model="currentPassword"
            type="password"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.newPassword') }}</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            :placeholder="t('settings.newPasswordPlaceholder')"
          />
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.confirmNewPassword') }}</label>
          <input
            v-model="confirmNewPassword"
            type="password"
            required
            class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          :disabled="passwordLoading"
          class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {{ passwordLoading ? t('settings.changingPassword') : t('settings.changePasswordSubmit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useI18n } from 'vue-i18n'
import { useDateFormat } from '../utils/date'

const auth = useAuthStore()
const { t } = useI18n()
const { formatDate: formatDateShort, formatDateLong } = useDateFormat()

const fullName = ref('')
const profileError = ref('')
const profileSuccess = ref('')
const profileLoading = ref(false)

const currentPassword = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordLoading = ref(false)

onMounted(() => {
  fullName.value = auth.user?.full_name || ''
})

function formatDate(dateStr) {
  return formatDateLong(dateStr)
}

async function handleUpdateProfile() {
  profileError.value = ''
  profileSuccess.value = ''
  profileLoading.value = true
  try {
    await auth.updateProfile(fullName.value || null)
    profileSuccess.value = t('settings.profileUpdated')
  } catch (e) {
    profileError.value = e.response?.data?.detail || t('settings.profileError')
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (newPassword.value !== confirmNewPassword.value) {
    passwordError.value = t('settings.passwordMismatch')
    return
  }

  passwordLoading.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    passwordSuccess.value = t('settings.passwordChanged')
    currentPassword.value = ''
    newPassword.value = ''
    confirmNewPassword.value = ''
  } catch (e) {
    passwordError.value = e.response?.data?.detail || t('settings.passwordError')
  } finally {
    passwordLoading.value = false
  }
}
</script>
