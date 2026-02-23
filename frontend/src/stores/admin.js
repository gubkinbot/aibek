import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAdminStore = defineStore('admin', () => {
  // ── Users ──────────────────────────────────────
  const users = ref({ items: [], total: 0, page: 1, per_page: 20, pages: 1 })
  const currentUser = ref(null)

  async function fetchUsers(params = {}) {
    const { data } = await api.get('/admin/users', { params })
    users.value = data
    return data
  }

  async function fetchUser(id) {
    const { data } = await api.get(`/admin/users/${id}`)
    currentUser.value = data
    return data
  }

  async function createUser(userData) {
    const { data } = await api.post('/admin/users', userData)
    return data
  }

  async function updateUser(id, userData) {
    const { data } = await api.patch(`/admin/users/${id}`, userData)
    return data
  }

  async function blockUser(id, reason = null) {
    const { data } = await api.post(`/admin/users/${id}/block`, { reason })
    return data
  }

  async function unblockUser(id) {
    const { data } = await api.post(`/admin/users/${id}/unblock`)
    return data
  }

  async function resetPassword(id) {
    const { data } = await api.post(`/admin/users/${id}/reset-password`)
    return data
  }

  async function deleteUser(id) {
    const { data } = await api.delete(`/admin/users/${id}`)
    return data
  }

  async function toggleSuperadmin(userId) {
    const { data } = await api.put(`/admin/users/${userId}/superadmin`)
    return data
  }

  // ── Permissions ────────────────────────────────
  const permissions = ref([])

  async function fetchPermissions() {
    const { data } = await api.get('/admin/permissions')
    permissions.value = data
    return data
  }

  // ── Audit Logs ─────────────────────────────────
  const auditLogs = ref({ items: [], total: 0, page: 1, per_page: 20, pages: 1 })

  async function fetchAuditLogs(params = {}) {
    const { data } = await api.get('/admin/audit-logs', { params })
    auditLogs.value = data
    return data
  }

  return {
    // Users
    users, currentUser,
    fetchUsers, fetchUser, createUser, updateUser,
    blockUser, unblockUser, resetPassword, deleteUser,
    toggleSuperadmin,
    // Permissions
    permissions, fetchPermissions,
    // Audit
    auditLogs, fetchAuditLogs,
  }
})
