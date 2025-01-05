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
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/Tasks.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 添加全局前置守卫
router.beforeEach((to, from, next) => {
  console.log('路由跳转:', {
    to: to.path,
    from: from.path,
    timestamp: new Date().toISOString()
  })
  next()
})

// 添加全局后置钩子
router.afterEach((to, from) => {
  console.log('路由完成:', {
    to: to.path,
    from: from.path,
    timestamp: new Date().toISOString()
  })
})

export default router 