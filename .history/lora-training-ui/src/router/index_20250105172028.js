import Vue from 'vue'
import VueRouter from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        redirect: '/training'
      },
      {
        path: '/training',
        name: 'training',
        component: () => import('@/views/Training.vue')
      },
      {
        path: '/materials',
        name: 'materials',
        component: () => import('@/views/Materials.vue')
      },
      {
        path: '/tasks',
        name: 'tasks',
        component: () => import('@/views/Tasks.vue')
      }
    ]
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router 