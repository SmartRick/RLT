import { createRouter, createWebHistory } from 'vue-router'
import Assets from '@/views/Assets.vue'

const routes = [
  {
    path: '/',
    redirect: '/assets'
  },
  {
    path: '/assets',
    name: 'Assets',
    component: Assets
  },
  // ... 其他路由
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 