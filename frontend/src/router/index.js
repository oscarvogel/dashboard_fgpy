import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Produccion from '../views/Produccion.vue'
import Profile from '../views/Profile.vue'
import Combustible from '../views/Combustible.vue'
import { fetchCurrentUser, isAuthenticated } from '../auth'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', name: 'Produccion', component: Produccion, meta: { requiresAuth: true } },
  { path: '/resumen', name: 'Resumen', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/profile', name: 'Profile', component: Profile, meta: { requiresAuth: true } },
  { path: '/combustible', name: 'Combustible', component: Combustible, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (to.meta && to.meta.requiresAuth) {
    if (!isAuthenticated()) {
      try {
        await fetchCurrentUser()
      } catch (err) {
        next({ name: 'Login', query: { next: to.fullPath } })
        return
      }
    }
  }
  next()
})

export default router
