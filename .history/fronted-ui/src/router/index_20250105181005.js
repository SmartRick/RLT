import { createRouter, createWebHistory } from 'vue-router'

/**
 * @type {import('vue-router').RouteRecordRaw[]}
 */
const routes = [
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/assets'
      },
      {
        path: 'assets',
        name: 'Assets',
        component: () => import('@/views/Assets.vue'),
        meta: {
          title: '资产管理',
          icon: 'ServerIcon'
        }
      },
      // 其他路由配置...
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 