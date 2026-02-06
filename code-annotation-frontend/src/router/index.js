import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'register', component: () => import('../views/Register.vue') },
  { path: '/', name: 'code', component: () => import('../views/Preview.vue') },
  { path: '/admin-projects', name: 'admin-projects', component: () => import('../views/AdminProjects.vue') }
]

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })

router.beforeEach((to, from, next) => {
  const userId = window.localStorage.getItem('userId')
  const guest = (to && to.query && (to.query.guest === '1' || to.query.guest === 1))
  if (userId === null) {
    if (guest) { window.localStorage.setItem('userId','demo'); next() }
    else if (to.path !== '/login') { next({ name: 'login' });}
    else { next() }
  } else { next() }
})

export default router
