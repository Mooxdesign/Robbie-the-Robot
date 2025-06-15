import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
// import '../assets/css/main.css'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/visualization',
      name: 'visualization',
      component: () => import('../views/Camera-and-3D-Model.vue')
    }
  ]
})

export default router
