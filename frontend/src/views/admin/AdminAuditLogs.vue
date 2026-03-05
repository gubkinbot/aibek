<template>
  <div class="py-8">
    <h1 class="text-2xl font-bold mb-6">{{ t('admin.audit.title') }}</h1>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-4 flex flex-wrap gap-3 items-end">
      <select v-model="filterAction" @change="loadLogs" class="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
        <option value="">{{ t('admin.audit.allActions') }}</option>
        <option value="user.create">user.create</option>
        <option value="user.edit">user.edit</option>
        <option value="user.block">user.block</option>
        <option value="user.unblock">user.unblock</option>
        <option value="user.delete">user.delete</option>
        <option value="user.reset_password">user.reset_password</option>
        <option value="user.roles.assign">user.roles.assign</option>
        <option value="user.groups.assign">user.groups.assign</option>
        <option value="role.create">role.create</option>
        <option value="role.edit">role.edit</option>
        <option value="role.delete">role.delete</option>
        <option value="role.permissions.set">role.permissions.set</option>
        <option value="group.create">group.create</option>
        <option value="group.edit">group.edit</option>
        <option value="group.delete">group.delete</option>
        <option value="department.create">department.create</option>
        <option value="department.edit">department.edit</option>
        <option value="department.delete">department.delete</option>
      </select>
      <select v-model="filterTargetType" @change="loadLogs" class="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
        <option value="">{{ t('admin.audit.allTypes') }}</option>
        <option value="user">user</option>
        <option value="role">role</option>
        <option value="group">group</option>
        <option value="department">department</option>
      </select>
    </div>

    <!-- Logs table -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.date') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.actor') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.action') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.target') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.details') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.audit.ip') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="log in admin.auditLogs.items" :key="log.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td class="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{{ formatDateTime(log.created_at) }}</td>
              <td class="px-4 py-3">{{ log.actor_name || '-' }}</td>
              <td class="px-4 py-3">
                <code class="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">{{ log.action }}</code>
              </td>
              <td class="px-4 py-3 text-xs">
                <span class="text-gray-500">{{ log.target_type }}:</span>
                <span class="font-mono">{{ log.target_id?.substring(0, 8) }}...</span>
              </td>
              <td class="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">
                {{ log.details ? JSON.stringify(log.details) : '-' }}
              </td>
              <td class="px-4 py-3 text-xs text-gray-400">{{ log.ip_address || '-' }}</td>
            </tr>
            <tr v-if="!admin.auditLogs.items.length">
              <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ t('admin.audit.empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="admin.auditLogs.pages > 1" class="flex items-center justify-between px-4 py-3 border-t dark:border-gray-700">
        <span class="text-sm text-gray-500">{{ t('admin.users.total') }}: {{ admin.auditLogs.total }}</span>
        <div class="flex gap-1">
          <button v-for="p in Math.min(admin.auditLogs.pages, 10)" :key="p" @click="page = p; loadLogs()"
            :class="['px-3 py-1 rounded text-sm', p === page ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600']">
            {{ p }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useI18n } from 'vue-i18n'
import { useDateFormat } from '../../utils/date'

const { t } = useI18n()
const { formatDateTime } = useDateFormat()
const admin = useAdminStore()

const page = ref(1)
const filterAction = ref('')
const filterTargetType = ref('')

async function loadLogs() {
  const params = { page: page.value, per_page: 20 }
  if (filterAction.value) params.action = filterAction.value
  if (filterTargetType.value) params.target_type = filterTargetType.value
  await admin.fetchAuditLogs(params)
}

onMounted(() => loadLogs())
</script>
