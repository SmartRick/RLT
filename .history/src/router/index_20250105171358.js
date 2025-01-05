import { createRouter, createWebHistory } from 'vue-router'
import TrainingView from '@/views/Training.vue'
import MaterialsView from '@/views/Materials.vue'

const routes = [
  {
    path: '/',
    redirect: '/training'
  },
  {
    path: '/training',
    name: 'training',
    component: TrainingView
  },
  {
    path: '/materials',
    name: 'materials',
    component: MaterialsView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router 