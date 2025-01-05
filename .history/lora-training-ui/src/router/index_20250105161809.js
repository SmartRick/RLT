import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Materials from '@/views/Materials.vue'
import Tasks from '@/views/Tasks.vue'
import Assets from '@/views/Assets.vue'
import Settings from '@/views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '仪表盘' }
  },
  {
    path: '/materials',
    name: 'Materials',
    component: Materials,
    meta: { title: '训练素材' }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: { title: '训练任务' }
  },
  {
    path: '/assets',
    name: 'Assets',
    component: Assets,
    meta: { title: '资产管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: '系统设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - Lora 训练任务管理器`
  next()
})

export default router 