<template>
  <div class="py-8">
    <router-link to="/admin/users" class="text-blue-600 dark:text-blue-400 hover:underline text-sm mb-4 inline-block">&larr; {{ t('admin.users.title') }}</router-link>

    <div v-if="!user" class="text-center py-12 text-gray-500">{{ t('admin.loading') }}</div>

    <template v-else>
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ user.full_name || user.email || user.phone }}</h1>
        <span :class="['px-3 py-1 rounded text-sm', user.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400']">
          {{ user.is_active ? t('admin.users.active') : t('admin.users.blocked') }}
        </span>
      </div>

      <div v-if="message" class="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ message }}</div>
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ error }}</div>

      <!-- Profile Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.users.profileInfo') }}</h2>
        <form @submit.prevent="handleUpdateProfile" class="space-y-3">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.name') }}</label>
              <input v-model="editForm.full_name" type="text" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.email') }}</label>
              <input v-model="editForm.email" type="email" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.phone') }}</label>
              <input v-model="editForm.phone" type="tel" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('admin.users.provider') }}</label>
              <p class="text-sm py-2 text-gray-900 dark:text-white">{{ user.auth_provider }}</p>
            </div>
          </div>
          <!-- Superadmin toggle — only visible to superadmins -->
          <div v-if="authStore.isSuperAdmin && !isSelf" class="flex items-center gap-3 pt-2 border-t dark:border-gray-600">
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="checkbox" v-model="superadminToggle" class="rounded" />
              <span class="font-medium text-red-600 dark:text-red-400">{{ t('admin.users.superadmin') }}</span>
            </label>
            <span class="text-xs text-gray-400">{{ t('admin.users.superadminHint') }}</span>
          </div>
          <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
        </form>
      </div>

      <!-- Module Access Levels — Matrix Table -->
      <div v-if="authStore.hasPermission('users.edit')" class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.moduleAccess.title') }}</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b dark:border-gray-600">
                <th class="text-left py-2 pr-4 font-medium text-gray-700 dark:text-gray-300">{{ t('admin.moduleAccess.module') }}</th>
                <th class="px-2 py-2 text-center font-medium text-gray-400 min-w-[80px]">{{ t('admin.moduleAccess.noAccess') }}</th>
                <th v-for="lvlName in uniqueLevelNames" :key="lvlName" class="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 min-w-[80px]">
                  {{ t(`admin.moduleAccess.levels.${lvlName}`) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(levels, moduleName) in moduleLevels" :key="moduleName" class="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td class="py-3 pr-4 font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">
                  {{ t(`admin.moduleAccess.modules.${moduleName}`) }}
                </td>
                <td class="px-2 py-3 text-center">
                  <label class="inline-flex items-center justify-center cursor-pointer w-full h-full">
                    <input type="radio" :name="`module-${moduleName}`" :value="''" v-model="selectedModuleLevel[moduleName]"
                      class="w-4 h-4 text-gray-400 focus:ring-gray-300" />
                  </label>
                </td>
                <td v-for="lvlName in uniqueLevelNames" :key="lvlName" class="px-2 py-3 text-center">
                  <label v-if="moduleLevelExists(moduleName, lvlName)" class="inline-flex items-center justify-center cursor-pointer w-full h-full">
                    <input type="radio" :name="`module-${moduleName}`" :value="lvlName" v-model="selectedModuleLevel[moduleName]"
                      class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                  </label>
                  <span v-else class="text-gray-300 dark:text-gray-600">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <button @click="handleSaveModuleAccess" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
      </div>

      <!-- Actions -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.users.actions') }}</h2>
        <div class="flex flex-wrap gap-3">
          <button v-if="user.auth_provider === 'email'" @click="handleResetPassword" class="bg-yellow-500 text-white px-4 py-2 rounded text-sm hover:bg-yellow-600">
            {{ t('admin.users.resetPassword') }}
          </button>
          <button v-if="user.is_active && !isSuperAdminUser" @click="handleBlock" class="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700">
            {{ t('admin.users.block') }}
          </button>
          <button v-if="!user.is_active" @click="handleUnblock" class="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700">
            {{ t('admin.users.unblock') }}
          </button>
          <button v-if="!isSuperAdminUser" @click="handleDelete" class="bg-red-800 text-white px-4 py-2 rounded text-sm hover:bg-red-900">
            {{ t('admin.users.delete') }}
          </button>
        </div>
        <div v-if="tempPassword" class="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
          <p class="font-medium text-yellow-800 dark:text-yellow-400">{{ t('admin.users.tempPassword') }}:</p>
          <code class="text-lg font-mono font-bold text-gray-900 dark:text-white">{{ tempPassword }}</code>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const admin = useAdminStore()
const authStore = useAuthStore()

const user = ref(null)
const message = ref('')
const error = ref('')
const tempPassword = ref('')

const editForm = ref({ full_name: '', email: '', phone: '' })
const superadminToggle = ref(false)

const moduleLevels = ref({})
const selectedModuleLevel = ref({})

const isSuperAdminUser = computed(() => user.value?.is_superadmin)
const isSelf = computed(() => user.value?.id === authStore.user?.id)

const uniqueLevelNames = computed(() => {
  const set = new Set()
  for (const levels of Object.values(moduleLevels.value)) {
    for (const lvl of levels) set.add(lvl.level)
  }
  return [...set]
})

function moduleLevelExists(moduleName, lvlName) {
  const levels = moduleLevels.value[moduleName]
  return levels?.some(l => l.level === lvlName)
}

async function loadUser() {
  try {
    const data = await admin.fetchUser(route.params.id)
    user.value = data
    editForm.value = { full_name: data.full_name || '', email: data.email || '', phone: data.phone || '' }
    superadminToggle.value = data.is_superadmin ?? false
  } catch {
    error.value = t('admin.users.notFound')
  }
}

async function handleUpdateProfile() {
  error.value = ''
  message.value = ''
  try {
    const data = await admin.updateUser(route.params.id, editForm.value)
    user.value = data

    // Handle superadmin toggle if current user is superadmin
    if (authStore.isSuperAdmin && !isSelf.value) {
      if (superadminToggle.value !== data.is_superadmin) {
        const updated = await admin.toggleSuperadmin(route.params.id)
        user.value = updated
      }
    }

    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function loadModuleLevels() {
  try {
    const { data: levels } = await api.get('/admin/module-access/levels')
    moduleLevels.value = levels
    for (const mod of Object.keys(levels)) {
      selectedModuleLevel.value[mod] = ''
    }
    const { data: assignments } = await api.get(`/admin/module-access/users/${route.params.id}`)
    for (const a of assignments) {
      selectedModuleLevel.value[a.module] = a.level
    }
  } catch {}
}

async function handleSaveModuleAccess() {
  error.value = ''
  message.value = ''
  try {
    for (const [mod, level] of Object.entries(selectedModuleLevel.value)) {
      if (level) {
        await api.put(`/admin/module-access/users/${route.params.id}`, { module: mod, level })
      } else {
        try {
          await api.delete(`/admin/module-access/users/${route.params.id}/${mod}`)
        } catch (e) {
          if (e.response?.status !== 404) throw e
        }
      }
    }
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleResetPassword() {
  error.value = ''
  message.value = ''
  tempPassword.value = ''
  try {
    const result = await admin.resetPassword(route.params.id)
    if (result.temp_password) tempPassword.value = result.temp_password
    message.value = result.message
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleBlock() {
  const reason = prompt(t('admin.users.blockReason'))
  if (reason === null) return
  try {
    await admin.blockUser(route.params.id, reason || null)
    await loadUser()
    message.value = t('admin.users.userBlocked')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleUnblock() {
  try {
    await admin.unblockUser(route.params.id)
    await loadUser()
    message.value = t('admin.users.userUnblocked')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleDelete() {
  if (!confirm(t('admin.users.confirmDelete'))) return
  try {
    await admin.deleteUser(route.params.id)
    router.push('/admin/users')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

onMounted(async () => {
  await loadUser()
  await loadModuleLevels()
})
</script>
