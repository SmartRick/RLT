import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      {
        path: '/assets',
        name: 'Assets',
        component: () => import('@/views/Assets.vue'),
        meta: {
          title: '资产管理'
        }
      },
      // 其他路由...
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 