import { createRouter, createWebHistory } from 'vue-router'
import AssetManager from '@/views/Assets.vue'

const routes = [
  {
    path: '/',
    redirect: '/assets'
  },
  {
    path: '/assets',
    name: 'AssetManager',
    component: AssetManager,
    meta: { title: '资产管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 