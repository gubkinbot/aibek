import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../views/Landing.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import VerifyEmail from '../views/VerifyEmail.vue'
import ForgotPassword from '../views/ForgotPassword.vue'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'

const routes = [
  { path: '/', component: Landing, meta: { guestOnly: true } },
  { path: '/login', component: Login, meta: { guestOnly: true } },
  { path: '/register', component: Register, meta: { guestOnly: true } },
  { path: '/verify-email', component: VerifyEmail },
  { path: '/forgot-password', component: ForgotPassword },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    component: Settings,
    meta: { requiresAuth: true },
  },
  // Module routes
  {
    path: '/compressor',
    component: () => import('../views/modules/CompressorHome.vue'),
    meta: { requiresAuth: true, requiresPermission: 'compressor.access', noContainer: true },
  },
  {
    path: '/balance',
    component: () => import('../views/modules/BalanceHome.vue'),
    meta: { requiresAuth: true, requiresPermission: 'balance.access' },
  },
  {
    path: '/weather',
    component: () => import('../views/modules/WeatherHome.vue'),
    meta: { requiresAuth: true, requiresPermission: 'weather.access' },
  },
  {
    path: '/digital',
    component: () => import('../views/modules/DigitalHome.vue'),
    meta: { requiresAuth: true, requiresPermission: 'digital.access' },
  },
  {
    path: '/ai-chat',
    component: () => import('../views/modules/AiChatHome.vue'),
    meta: { requiresAuth: true, requiresPermission: 'ai_chat.access' },
  },
  // Admin routes
  {
    path: '/admin/users',
    component: () => import('../views/admin/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresPermission: 'users.view' },
  },
  {
    path: '/admin/users/:id',
    component: () => import('../views/admin/AdminUserDetail.vue'),
    meta: { requiresAuth: true, requiresPermission: 'users.view' },
  },
  {
    path: '/admin/audit-logs',
    component: () => import('../views/admin/AdminAuditLogs.vue'),
    meta: { requiresAuth: true, requiresPermission: 'audit.view' },
  },
  {
    path: '/admin/system',
    component: () => import('../views/admin/AdminSystem.vue'),
    meta: { requiresAuth: true, requiresPermission: 'system.view' },
  },
  {
    path: '/admin/compressor',
    component: () => import('../views/admin/AdminCompressor.vue'),
    meta: { requiresAuth: true, requiresPermission: 'compressor.manage' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const { useAuthStore } = await import('../stores/auth')
  const auth = useAuthStore()

  // Ensure user data is loaded on first navigation
  await auth.init()

  if (to.meta.requiresAuth) {
    if (!auth.isAuthenticated) return '/login'

    if (to.meta.requiresPermission) {
      if (!auth.hasPermission(to.meta.requiresPermission)) return '/dashboard'
    }
  }

  // Redirect authenticated users away from guest-only pages
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return '/dashboard'
  }
})

export default router
