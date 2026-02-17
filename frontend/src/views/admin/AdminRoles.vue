<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">{{ t('admin.roles.title') }}</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm">
        {{ t('admin.roles.create') }}
      </button>
    </div>

    <div v-if="message" class="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ message }}</div>
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ error }}</div>

    <!-- Roles list -->
    <div class="space-y-3">
      <div v-for="role in admin.roles" :key="role.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex items-center justify-between">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="font-bold">{{ role.display_name }}</span>
            <code class="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">{{ role.name }}</code>
            <span v-if="role.is_system" class="text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 px-2 py-0.5 rounded">{{ t('admin.system') }}</span>
          </div>
          <p v-if="role.description" class="text-sm text-gray-500 mt-1">{{ role.description }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ t('admin.roles.userCount') }}: {{ role.user_count }}</p>
        </div>
        <div class="flex gap-2">
          <button v-if="role.name !== 'superadmin'" @click="openPermissions(role)" class="text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 px-3 py-1 rounded text-sm">
            {{ t('admin.roles.permissions') }}
          </button>
          <button v-if="!role.is_system" @click="openEdit(role)" class="text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 px-3 py-1 rounded text-sm">
            {{ t('admin.edit') }}
          </button>
          <button v-if="!role.is_system" @click="handleDelete(role)" class="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-3 py-1 rounded text-sm">
            {{ t('admin.delete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
          <h2 class="text-lg font-bold mb-4">{{ editingRole ? t('admin.roles.editTitle') : t('admin.roles.createTitle') }}</h2>
          <form @submit.prevent="handleSave">
            <div class="space-y-3">
              <div v-if="!editingRole">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.roles.nameField') }}</label>
                <input v-model="roleForm.name" type="text" required :placeholder="t('admin.roles.nameFieldPlaceholder')" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.roles.displayName') }}</label>
                <input v-model="roleForm.display_name" type="text" required class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.roles.description') }}</label>
                <textarea v-model="roleForm.description" rows="2" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm"></textarea>
              </div>
            </div>
            <div class="flex justify-end gap-2 mt-6">
              <button type="button" @click="showModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">{{ t('admin.cancel') }}</button>
              <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Permissions Modal -->
    <Teleport to="body">
      <div v-if="showPermModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showPermModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg p-6 max-h-[80vh] overflow-y-auto">
          <h2 class="text-lg font-bold mb-4">{{ t('admin.roles.permissionsFor') }} {{ permRole?.display_name }}</h2>
          <div v-for="cat in allPermissions" :key="cat.category" class="mb-4">
            <h3 class="text-sm font-bold text-gray-500 uppercase mb-2">{{ cat.category }}</h3>
            <div class="space-y-1">
              <label v-for="perm in cat.permissions" :key="perm.id" class="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 px-2 py-1 rounded">
                <input type="checkbox" :value="perm.id" v-model="selectedPermIds" class="rounded" />
                <span>{{ perm.display_name }}</span>
                <code class="text-xs text-gray-400">{{ perm.codename }}</code>
              </label>
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <button @click="showPermModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">{{ t('admin.cancel') }}</button>
            <button @click="handleSavePermissions" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">{{ t('admin.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const admin = useAdminStore()

const message = ref('')
const error = ref('')
const showModal = ref(false)
const editingRole = ref(null)
const roleForm = ref({ name: '', display_name: '', description: '' })

const showPermModal = ref(false)
const permRole = ref(null)
const selectedPermIds = ref([])
const allPermissions = ref([])

function openCreate() {
  editingRole.value = null
  roleForm.value = { name: '', display_name: '', description: '' }
  showModal.value = true
}

function openEdit(role) {
  editingRole.value = role
  roleForm.value = { display_name: role.display_name, description: role.description || '' }
  showModal.value = true
}

async function openPermissions(role) {
  permRole.value = role
  try {
    const detail = await admin.fetchRole(role.id)
    selectedPermIds.value = detail.permissions.map(p => p.id)
    if (!allPermissions.value.length) {
      allPermissions.value = await admin.fetchPermissions()
    }
    showPermModal.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleSave() {
  error.value = ''
  message.value = ''
  try {
    if (editingRole.value) {
      await admin.updateRole(editingRole.value.id, roleForm.value)
    } else {
      await admin.createRole(roleForm.value)
    }
    showModal.value = false
    await admin.fetchRoles()
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleDelete(role) {
  if (!confirm(t('admin.roles.confirmDelete', { name: role.display_name }))) return
  error.value = ''
  try {
    await admin.deleteRole(role.id)
    await admin.fetchRoles()
    message.value = t('admin.deleted')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleSavePermissions() {
  error.value = ''
  try {
    await admin.setRolePermissions(permRole.value.id, selectedPermIds.value)
    showPermModal.value = false
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

onMounted(() => admin.fetchRoles())
</script>
