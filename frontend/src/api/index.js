import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers['Accept-Language'] = localStorage.getItem('locale') || 'ru'
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 || (error.response?.status === 403 && error.config?.url === '/auth/me')) {
      const { useAuthStore } = await import('../stores/auth')
      const auth = useAuthStore()
      auth.logout()

      const { default: router } = await import('../router')
      if (router.currentRoute.value.meta.requiresAuth) {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api
