<template>
  <div class="max-w-5xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">{{ t('admin.departments.title') }}</h1>
      <button @click="openCreate()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm">
        {{ t('admin.departments.create') }}
      </button>
    </div>

    <div v-if="message" class="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 p-3 rounded mb-4 text-sm">{{ message }}</div>
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ error }}</div>

    <!-- Tree -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div v-if="!admin.departments.length" class="text-center py-8 text-gray-500">{{ t('admin.departments.empty') }}</div>
      <DeptNode v-for="dept in admin.departments" :key="dept.id" :dept="dept" :level="0"
        @edit="openEdit" @delete="handleDelete" @add-child="openCreate" />
    </div>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
          <h2 class="text-lg font-bold mb-4">{{ editing ? t('admin.departments.editTitle') : t('admin.departments.createTitle') }}</h2>
          <form @submit.prevent="handleSave">
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.departments.nameField') }}</label>
                <input v-model="form.name" type="text" required class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.departments.description') }}</label>
                <textarea v-model="form.description" rows="2" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm"></textarea>
              </div>
              <div v-if="form.parent_id">
                <span class="text-sm text-gray-500">{{ t('admin.departments.parent') }}: {{ parentName }}</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted, defineComponent, h } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const admin = useAdminStore()

const message = ref('')
const error = ref('')
const showModal = ref(false)
const editing = ref(null)
const form = ref({ name: '', description: '', parent_id: null })
const parentName = ref('')

function openCreate(parentDept = null) {
  editing.value = null
  form.value = { name: '', description: '', parent_id: parentDept?.id || null }
  parentName.value = parentDept?.name || ''
  showModal.value = true
}

function openEdit(dept) {
  editing.value = dept
  form.value = { name: dept.name, description: dept.description || '' }
  showModal.value = true
}

async function handleSave() {
  error.value = ''
  message.value = ''
  try {
    if (editing.value) {
      await admin.updateDepartment(editing.value.id, { name: form.value.name, description: form.value.description })
    } else {
      await admin.createDepartment(form.value)
    }
    showModal.value = false
    await admin.fetchDepartments()
    message.value = t('admin.saved')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

async function handleDelete(dept) {
  if (!confirm(t('admin.departments.confirmDelete', { name: dept.name }))) return
  error.value = ''
  try {
    await admin.deleteDepartment(dept.id)
    await admin.fetchDepartments()
    message.value = t('admin.deleted')
  } catch (e) {
    error.value = e.response?.data?.detail || t('admin.error')
  }
}

onMounted(() => admin.fetchDepartments())

// Recursive tree node component
const DeptNode = defineComponent({
  name: 'DeptNode',
  props: { dept: Object, level: Number },
  emits: ['edit', 'delete', 'add-child'],
  setup(props, { emit }) {
    return () => h('div', { class: 'border-l-2 border-gray-200 dark:border-gray-600 ml-4', style: props.level === 0 ? 'margin-left: 0; border: none;' : '' }, [
      h('div', { class: 'flex items-center justify-between py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded' }, [
        h('div', {}, [
          h('span', { class: 'font-medium text-sm' }, props.dept.name),
          props.dept.description ? h('p', { class: 'text-xs text-gray-500' }, props.dept.description) : null,
          h('span', { class: 'text-xs text-gray-400' }, ` (${t('admin.groups.members')}: ${props.dept.user_count})`),
        ]),
        h('div', { class: 'flex gap-1' }, [
          h('button', { class: 'text-blue-600 dark:text-blue-400 text-xs px-2 py-1 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded', onClick: () => emit('add-child', props.dept) }, '+'),
          h('button', { class: 'text-gray-600 dark:text-gray-400 text-xs px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded', onClick: () => emit('edit', props.dept) }, t('admin.edit')),
          h('button', { class: 'text-red-600 dark:text-red-400 text-xs px-2 py-1 hover:bg-red-50 dark:hover:bg-red-900/20 rounded', onClick: () => emit('delete', props.dept) }, t('admin.delete')),
        ]),
      ]),
      ...(props.dept.children || []).map(child =>
        h(DeptNode, { dept: child, level: props.level + 1, onEdit: (d) => emit('edit', d), onDelete: (d) => emit('delete', d), onAddChild: (d) => emit('add-child', d) })
      ),
    ])
  },
})
</script>
