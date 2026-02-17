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
  // Admin routes
  {
    path: '/admin/users',
    component: () => import('../views/admin/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/users/:id',
    component: () => import('../views/admin/AdminUserDetail.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/roles',
    component: () => import('../views/admin/AdminRoles.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/groups',
    component: () => import('../views/admin/AdminGroups.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/departments',
    component: () => import('../views/admin/AdminDepartments.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/audit-logs',
    component: () => import('../views/admin/AdminAuditLogs.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
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

    if (to.meta.requiresAdmin) {
      if (!auth.isAdmin) return '/dashboard'
    }
  }

  // Redirect authenticated users away from guest-only pages
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return '/dashboard'
  }
})

export default router
