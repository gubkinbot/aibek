<template>
  <div class="w-[80%] mx-auto py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">{{ t('admin.users.title') }}</h1>
      <button @click="showCreateModal = true" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm">
        {{ t('admin.users.create') }}
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-4 flex flex-wrap gap-3 items-end">
      <div class="flex-1 min-w-[200px]">
        <input v-model="search" :placeholder="t('admin.users.searchPlaceholder')" @input="debouncedFetch"
          class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <select v-model="filterStatus" @change="loadUsers" class="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm">
        <option value="">{{ t('admin.users.allStatuses') }}</option>
        <option value="true">{{ t('admin.users.active') }}</option>
        <option value="false">{{ t('admin.users.blocked') }}</option>
      </select>
    </div>

    <!-- Error -->
    <div v-if="loadError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 p-4 rounded-lg mb-4 flex items-center justify-between">
      <span>{{ loadError }}</span>
      <button @click="loadUsers" class="text-red-600 dark:text-red-400 hover:underline text-sm ml-4">{{ t('admin.users.retry') || 'Повторить' }}</button>
    </div>

    <!-- Loading -->
    <div v-if="loadingUsers && !admin.users.items.length" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Users table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.users.name') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.users.email') }} / {{ t('admin.users.phone') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.users.status') }}</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.users.date') }}</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600 dark:text-gray-300">{{ t('admin.users.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="u in admin.users.items" :key="u.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td class="px-4 py-3">
                <router-link :to="`/admin/users/${u.id}`" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">
                  {{ u.full_name || '-' }}
                </router-link>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ u.email || u.phone || '-' }}</td>
              <td class="px-4 py-3">
                <span :class="['inline-block px-2 py-0.5 rounded text-xs', u.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400']">
                  {{ u.is_active ? t('admin.users.active') : t('admin.users.blocked') }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button v-if="u.is_active && !u.is_superadmin" @click="handleBlock(u)" class="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-2 py-1 rounded text-xs">
                    {{ t('admin.users.block') }}
                  </button>
                  <button v-if="!u.is_active" @click="handleUnblock(u)" class="text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 px-2 py-1 rounded text-xs">
                    {{ t('admin.users.unblock') }}
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!admin.users.items.length">
              <td colspan="5" class="px-4 py-8 text-center text-gray-500">{{ t('admin.users.empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="admin.users.pages > 1" class="flex items-center justify-between px-4 py-3 border-t dark:border-gray-700">
        <span class="text-sm text-gray-500">{{ t('admin.users.total') }}: {{ admin.users.total }}</span>
        <div class="flex gap-1">
          <button v-for="p in admin.users.pages" :key="p" @click="page = p; loadUsers()"
            :class="['px-3 py-1 rounded text-sm', p === page ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600']">
            {{ p }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showCreateModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-lg font-bold mb-4">{{ t('admin.users.createTitle') }}</h2>
          <div v-if="createError" class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{{ createError }}</div>

          <form @submit.prevent="handleCreate">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.name') }}</label>
                <input v-model="createForm.full_name" type="text" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.email') }}</label>
                <input v-model="createForm.email" type="email" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.password') }}</label>
                <input v-model="createForm.password" type="text" :placeholder="t('admin.users.passwordHint')"
                  class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('admin.users.phone') }}</label>
                <input v-model="createForm.phone" type="tel" :placeholder="t('admin.users.phonePlaceholder')" class="w-full border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 dark:text-white text-sm" />
              </div>
            </div>

            <!-- Module Access Matrix -->
            <div v-if="Object.keys(createModuleLevels).length" class="mb-4">
              <h3 class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{{ t('admin.moduleAccess.title') }}</h3>
              <div class="overflow-x-auto border dark:border-gray-600 rounded">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b dark:border-gray-600 bg-gray-50 dark:bg-gray-700">
                      <th class="text-left py-2 px-3 font-medium text-gray-700 dark:text-gray-300">{{ t('admin.moduleAccess.module') }}</th>
                      <th class="px-2 py-2 text-center font-medium text-gray-400 min-w-[70px]">{{ t('admin.moduleAccess.noAccess') }}</th>
                      <th v-for="lvlName in createUniqueLevels" :key="lvlName" class="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 min-w-[70px]">
                        {{ t(`admin.moduleAccess.levels.${lvlName}`) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(levels, moduleName) in createModuleLevels" :key="moduleName" class="border-b dark:border-gray-700">
                      <td class="py-2 px-3 font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">
                        {{ t(`admin.moduleAccess.modules.${moduleName}`) }}
                      </td>
                      <td class="px-2 py-2 text-center">
                        <input type="radio" :name="`create-module-${moduleName}`" :value="''" v-model="createModuleAccess[moduleName]"
                          class="w-4 h-4 text-gray-400 focus:ring-gray-300" />
                      </td>
                      <td v-for="lvlName in createUniqueLevels" :key="lvlName" class="px-2 py-2 text-center">
                        <input v-if="levels.some(l => l.level === lvlName)" type="radio" :name="`create-module-${moduleName}`" :value="lvlName" v-model="createModuleAccess[moduleName]"
                          class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                        <span v-else class="text-gray-300 dark:text-gray-600">—</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="flex justify-end gap-2">
              <button type="button" @click="showCreateModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                {{ t('admin.cancel') }}
              </button>
              <button type="submit" :disabled="createLoading" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50">
                {{ createLoading ? t('admin.creating') : t('admin.users.create') }}
              </button>
            </div>
          </form>

          <div v-if="createdTempPassword" class="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
            <p class="font-medium text-yellow-800 dark:text-yellow-400">{{ t('admin.users.tempPassword') }}:</p>
            <code class="text-lg font-mono font-bold text-gray-900 dark:text-white">{{ createdTempPassword }}</code>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useI18n } from 'vue-i18n'
import { useDateFormat } from '../../utils/date'
import api from '../../api'

const { t } = useI18n()
const { formatDate } = useDateFormat()
const admin = useAdminStore()

const page = ref(1)
const search = ref('')
const filterStatus = ref('')

const loadingUsers = ref(false)
const loadError = ref('')

const showCreateModal = ref(false)
const createForm = ref({ full_name: '', email: '', password: '', phone: '' })
const createError = ref('')
const createLoading = ref(false)
const createdTempPassword = ref('')
const createModuleLevels = ref({})
const createModuleAccess = ref({})

const createUniqueLevels = computed(() => {
  const set = new Set()
  for (const levels of Object.values(createModuleLevels.value)) {
    for (const lvl of levels) set.add(lvl.level)
  }
  return [...set]
})

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; loadUsers() }, 300)
}

async function loadUsers() {
  loadError.value = ''
  loadingUsers.value = true
  try {
    const params = { page: page.value, per_page: 20 }
    if (search.value) params.search = search.value
    if (filterStatus.value !== '') params.is_active = filterStatus.value
    await admin.fetchUsers(params)
  } catch (e) {
    const detail = e.response?.data?.detail
    const status = e.response?.status
    loadError.value = detail
      ? `${detail} (${status})`
      : status
        ? `${t('admin.error')} (HTTP ${status})`
        : t('admin.error')
  } finally {
    loadingUsers.value = false
  }
}

async function handleBlock(user) {
  const reason = prompt(t('admin.users.blockReason'))
  if (reason === null) return
  try {
    await admin.blockUser(user.id, reason || null)
    await loadUsers()
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function handleUnblock(user) {
  try {
    await admin.unblockUser(user.id)
    await loadUsers()
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function handleCreate() {
  createError.value = ''
  createdTempPassword.value = ''
  createLoading.value = true
  try {
    const payload = {}
    if (createForm.value.full_name) payload.full_name = createForm.value.full_name
    if (createForm.value.email) payload.email = createForm.value.email
    if (createForm.value.password) payload.password = createForm.value.password
    if (createForm.value.phone) payload.phone = createForm.value.phone

    // Collect non-empty module access levels
    const moduleAccess = {}
    for (const [mod, level] of Object.entries(createModuleAccess.value)) {
      if (level) moduleAccess[mod] = level
    }
    if (Object.keys(moduleAccess).length) payload.module_access = moduleAccess

    const result = await admin.createUser(payload)
    if (result.temp_password) {
      createdTempPassword.value = result.temp_password
    } else {
      showCreateModal.value = false
    }
    createForm.value = { full_name: '', email: '', password: '', phone: '' }
    resetCreateModuleAccess()
    await loadUsers()
  } catch (e) {
    createError.value = e.response?.data?.detail || t('admin.error')
  } finally {
    createLoading.value = false
  }
}

function resetCreateModuleAccess() {
  for (const mod of Object.keys(createModuleLevels.value)) {
    createModuleAccess.value[mod] = ''
  }
}

onMounted(async () => {
  await loadUsers()
  try {
    const { data: levels } = await api.get('/admin/module-access/levels')
    createModuleLevels.value = levels
    for (const mod of Object.keys(levels)) {
      createModuleAccess.value[mod] = ''
    }
  } catch {}
})
</script>
