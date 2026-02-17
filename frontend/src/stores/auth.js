import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const loading = ref(false)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isSuperAdmin = computed(() => user.value?.roles?.includes('superadmin') ?? false)
  const isAdmin = computed(() => isSuperAdmin.value || (user.value?.roles?.includes('admin') ?? false))

  async function register(email, password, fullName) {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    })
    return data
  }

  async function verifyEmail(email, code) {
    const { data } = await api.post('/auth/verify-email', { email, code })
    return data
  }

  async function resendCode(email) {
    const { data } = await api.post('/auth/resend-code', { email })
    return data
  }

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      loading.value = true
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      logout()
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  async function init() {
    if (token.value && !user.value && !initialized.value) {
      await fetchUser()
    } else {
      initialized.value = true
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function forgotPassword(email) {
    const { data } = await api.post('/auth/forgot-password', { email })
    return data
  }

  async function resetPassword(email, code, newPassword) {
    const { data } = await api.post('/auth/reset-password', {
      email,
      code,
      new_password: newPassword,
    })
    return data
  }

  async function changePassword(currentPassword, newPassword) {
    const { data } = await api.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return data
  }

  async function updateProfile(fullName) {
    const { data } = await api.patch('/users/me', { full_name: fullName })
    user.value = data
    return data
  }

  return {
    user, token, loading, initialized, isAuthenticated, isAdmin, isSuperAdmin,
    init, register, verifyEmail, resendCode, login, fetchUser, logout,
    forgotPassword, resetPassword, changePassword, updateProfile,
  }
})
