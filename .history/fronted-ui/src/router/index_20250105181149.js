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
  },
  {
    path: '/tasks',
    name: 'TaskManager',
    component: () => import('@/views/Tasks.vue'),  // 懒加载
    meta: { title: '任务管理' }
  },
  {
    path: '/training',
    name: 'TrainingManager',
    component: () => import('@/views/Training.vue'),  // 懒加载
    meta: { title: '训练数据' }
  },
  {
    path: '/settings',
    name: 'SystemSettings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  // 添加404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),  // 懒加载
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局导航守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - AI Studio` : 'AI Studio'
  next()
})

export default router 