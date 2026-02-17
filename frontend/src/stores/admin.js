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

  async function assignUserRoles(userId, roleIds) {
    const { data } = await api.put(`/admin/users/${userId}/roles`, { role_ids: roleIds })
    return data
  }

  async function assignUserGroups(userId, groupIds) {
    const { data } = await api.put(`/admin/users/${userId}/groups`, { group_ids: groupIds })
    return data
  }

  async function assignUserDepartments(userId, departmentIds) {
    const { data } = await api.put(`/admin/users/${userId}/departments`, { department_ids: departmentIds })
    return data
  }

  // ── Roles ──────────────────────────────────────
  const roles = ref([])

  async function fetchRoles() {
    const { data } = await api.get('/admin/roles')
    roles.value = data
    return data
  }

  async function fetchRole(id) {
    const { data } = await api.get(`/admin/roles/${id}`)
    return data
  }

  async function createRole(roleData) {
    const { data } = await api.post('/admin/roles', roleData)
    return data
  }

  async function updateRole(id, roleData) {
    const { data } = await api.patch(`/admin/roles/${id}`, roleData)
    return data
  }

  async function deleteRole(id) {
    const { data } = await api.delete(`/admin/roles/${id}`)
    return data
  }

  async function setRolePermissions(roleId, permissionIds) {
    const { data } = await api.put(`/admin/roles/${roleId}/permissions`, { permission_ids: permissionIds })
    return data
  }

  // ── Groups ─────────────────────────────────────
  const groups = ref([])

  async function fetchGroups() {
    const { data } = await api.get('/admin/groups')
    groups.value = data
    return data
  }

  async function fetchGroup(id) {
    const { data } = await api.get(`/admin/groups/${id}`)
    return data
  }

  async function createGroup(groupData) {
    const { data } = await api.post('/admin/groups', groupData)
    return data
  }

  async function updateGroup(id, groupData) {
    const { data } = await api.patch(`/admin/groups/${id}`, groupData)
    return data
  }

  async function deleteGroup(id) {
    const { data } = await api.delete(`/admin/groups/${id}`)
    return data
  }

  async function setGroupPermissions(groupId, permissionIds) {
    const { data } = await api.put(`/admin/groups/${groupId}/permissions`, { permission_ids: permissionIds })
    return data
  }

  async function setGroupMembers(groupId, userIds) {
    const { data } = await api.put(`/admin/groups/${groupId}/members`, { user_ids: userIds })
    return data
  }

  // ── Departments ────────────────────────────────
  const departments = ref([])

  async function fetchDepartments() {
    const { data } = await api.get('/admin/departments')
    departments.value = data
    return data
  }

  async function createDepartment(deptData) {
    const { data } = await api.post('/admin/departments', deptData)
    return data
  }

  async function updateDepartment(id, deptData) {
    const { data } = await api.patch(`/admin/departments/${id}`, deptData)
    return data
  }

  async function deleteDepartment(id) {
    const { data } = await api.delete(`/admin/departments/${id}`)
    return data
  }

  async function setDepartmentMembers(deptId, userIds) {
    const { data } = await api.put(`/admin/departments/${deptId}/members`, { user_ids: userIds })
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
    assignUserRoles, assignUserGroups, assignUserDepartments,
    // Roles
    roles, fetchRoles, fetchRole, createRole, updateRole, deleteRole, setRolePermissions,
    // Groups
    groups, fetchGroups, fetchGroup, createGroup, updateGroup, deleteGroup, setGroupPermissions, setGroupMembers,
    // Departments
    departments, fetchDepartments, createDepartment, updateDepartment, deleteDepartment, setDepartmentMembers,
    // Permissions
    permissions, fetchPermissions,
    // Audit
    auditLogs, fetchAuditLogs,
  }
})
