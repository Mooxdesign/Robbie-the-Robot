import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/control',
      name: 'control',
      component: () => import('../views/Control.vue')
    },
    {
      path: '/config',
      name: 'config',
      component: () => import('../views/Config.vue')
    },
    {
      path: '/visualization',
      name: 'visualization',
      component: () => import('../views/Visualization.vue')
    },
    {
      path: '/debug',
      name: 'debug',
      component: () => import('../views/Debug.vue')
    }
  ]
})

export default router
