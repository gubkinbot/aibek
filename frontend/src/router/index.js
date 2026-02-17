import { createRouter, createWebHistory } from 'vue-router'
import Landing from '../views/Landing.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  { path: '/', component: Landing },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) return '/login'
  }
})

export default router
