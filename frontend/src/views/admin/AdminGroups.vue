<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">{{ t('admin.groups.title') }}</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm">
        {{ t('admin.groups.create') }}
      </button>
    </div>

    <div v-if="message" class="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ message }}</div>
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ error }}</div>

    <div class="space-y-3">
      <div v-for="group in admin.groups" :key="group.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex items-center justify-between">
        <div class="flex-1">
          <span class="font-bold">{{ group.name }}</span>
          <p v-if="group.description" class="text-sm text-gray-500 mt-1">{{ group.description }}</p>
          <p class="text-xs text-gray-400 mt-1">
            {{ t('admin.groups.members') }}: {{ group.user_count }} | {{ t('admin.roles.permissions') }}: {{ group.permission_count }}
          </p>
        </div>
        <div class="flex gap-2">
          <button @click="openPermissions(group)" class="text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 px-3 py-1 rounded text-sm">
            {{ t('admin.roles.permissions') }}
          </button>
          <button @click="openEdit(group)" class="text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 px-3 py-1 rounded text-sm">
            {{ t('admin.edit') }}
          </button>
          <button @click="handleDelete(group)" class="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-3 py-1 rounded text-sm">
            {{ t('admin.delete') }}
          </button>
        </div>
      </div>
      <div v-if="!admin.groups.length" class="text-center py-8 text-gray-500">{{ t('admin.groups.empty') }}</div>
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
          <h2 class="text-lg font-bold mb-4">{{ editing ? t('admin.groups.editTitle') : t('admin.groups.createTitle') }}</h2>
          <form @submit.prevent="handleSave">
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.groups.nameField') }}</label>
                <input v-model="form.name" type="text" required class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.groups.description') }}</label>
                <textarea v-model="form.description" rows="2" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm"></textarea>
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
          <h2 class="text-lg font-bold mb-4">{{ t('admin.roles.permissionsFor') }} {{ permGroup?.name }}</h2>
          <div v-for="cat in allPermissions" :key="cat.category" class="mb-4">
            <h3 class="text-sm font-bold text-gray-500 uppercase mb-2">{{ cat.category }}</h3>
            <div class="space-y-1">
              <label v-for="perm in cat.permissions" :key="perm.id" class="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 px-2 py-1 rounded">
                <input type="checkbox" :value="perm.id" v-model="selectedPermIds" class="rounded" />
                <span>{{ perm.display_name }}</span>
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
const editing = ref(null)
const form = ref({ name: '', description: '' })

const showPermModal = ref(false)
const permGroup = ref(null)
const selectedPermIds = ref([])
const allPermissions = ref([])

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '' }
  showModal.value = true
}

function openEdit(group) {
  editing.value = group
  form.value = { name: group.name, description: group.description || '' }
  showModal.value = true
}

async function openPermissions(group) {
  permGroup.value = group
  try {
    const detail = await admin.fetchGroup(group.id)
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
    if (editing.value) {
      await admin.updateGroup(editing.value.id, form.value)
    } else {
      await admin.createGroup(form.value)
    }
    showModal.value = false
    await admin.fetchGroups()
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleDelete(group) {
  if (!confirm(t('admin.groups.confirmDelete', { name: group.name }))) return
  error.value = ''
  try {
    await admin.deleteGroup(group.id)
    await admin.fetchGroups()
    message.value = t('admin.deleted')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleSavePermissions() {
  error.value = ''
  try {
    await admin.setGroupPermissions(permGroup.value.id, selectedPermIds.value)
    showPermModal.value = false
    await admin.fetchGroups()
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

onMounted(() => admin.fetchGroups())
</script>
