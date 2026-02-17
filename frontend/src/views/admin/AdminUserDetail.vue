<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
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
          <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
        </form>
      </div>

      <!-- Roles -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.users.rolesCol') }}</h2>
        <div class="flex flex-wrap gap-2 mb-4">
          <label v-for="role in allRoles" :key="role.id" class="flex items-center gap-2 px-3 py-2 rounded border dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
            :class="{ 'border-blue-500 bg-blue-50 dark:bg-blue-900/20': selectedRoleIds.includes(role.id) }">
            <input type="checkbox" :value="role.id" v-model="selectedRoleIds"
              :disabled="role.name === 'superadmin' && !authStore.isSuperAdmin" class="rounded" />
            <span>{{ role.display_name }}</span>
            <span v-if="role.is_system" class="text-xs text-gray-400">({{ t('admin.system') }})</span>
          </label>
        </div>
        <button @click="handleAssignRoles" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
      </div>

      <!-- Groups -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.groups.title') }}</h2>
        <div class="flex flex-wrap gap-2 mb-4">
          <label v-for="group in allGroups" :key="group.id" class="flex items-center gap-2 px-3 py-2 rounded border dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
            :class="{ 'border-blue-500 bg-blue-50 dark:bg-blue-900/20': selectedGroupIds.includes(group.id) }">
            <input type="checkbox" :value="group.id" v-model="selectedGroupIds" class="rounded" />
            <span>{{ group.name }}</span>
          </label>
          <span v-if="!allGroups.length" class="text-gray-400 text-sm">{{ t('admin.groups.empty') }}</span>
        </div>
        <button v-if="allGroups.length" @click="handleAssignGroups" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
      </div>

      <!-- Departments -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-4">
        <h2 class="text-lg font-bold mb-4">{{ t('admin.departments.title') }}</h2>
        <div class="flex flex-wrap gap-2 mb-4">
          <label v-for="dept in flatDepartments" :key="dept.id" class="flex items-center gap-2 px-3 py-2 rounded border dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
            :class="{ 'border-blue-500 bg-blue-50 dark:bg-blue-900/20': selectedDeptIds.includes(dept.id) }">
            <input type="checkbox" :value="dept.id" v-model="selectedDeptIds" class="rounded" />
            <span>{{ dept.prefix }}{{ dept.name }}</span>
          </label>
          <span v-if="!flatDepartments.length" class="text-gray-400 text-sm">{{ t('admin.departments.empty') }}</span>
        </div>
        <button v-if="flatDepartments.length" @click="handleAssignDepts" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
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
const selectedRoleIds = ref([])
const selectedGroupIds = ref([])
const selectedDeptIds = ref([])

const allRoles = ref([])
const allGroups = ref([])
const flatDepartments = ref([])

const isSuperAdminUser = computed(() => user.value?.roles?.some(r => r.name === 'superadmin'))

function flattenDepartments(departments, prefix = '') {
  const result = []
  for (const dept of departments) {
    result.push({ ...dept, prefix })
    if (dept.children?.length) {
      result.push(...flattenDepartments(dept.children, prefix + '— '))
    }
  }
  return result
}

async function loadUser() {
  try {
    const data = await admin.fetchUser(route.params.id)
    user.value = data
    editForm.value = { full_name: data.full_name || '', email: data.email || '', phone: data.phone || '' }
    selectedRoleIds.value = data.roles.map(r => r.id)
    selectedGroupIds.value = data.groups.map(g => g.id)
    selectedDeptIds.value = data.departments.map(d => d.id)
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
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleAssignRoles() {
  error.value = ''
  message.value = ''
  try {
    const data = await admin.assignUserRoles(route.params.id, selectedRoleIds.value)
    user.value = data
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleAssignGroups() {
  error.value = ''
  message.value = ''
  try {
    const data = await admin.assignUserGroups(route.params.id, selectedGroupIds.value)
    user.value = data
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleAssignDepts() {
  error.value = ''
  message.value = ''
  try {
    const data = await admin.assignUserDepartments(route.params.id, selectedDeptIds.value)
    user.value = data
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
  try {
    await admin.fetchRoles()
    allRoles.value = admin.roles
  } catch {}
  try {
    await admin.fetchGroups()
    allGroups.value = admin.groups
  } catch {}
  try {
    await admin.fetchDepartments()
    flatDepartments.value = flattenDepartments(admin.departments)
  } catch {}
})
</script>
