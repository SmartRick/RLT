import { createRouter, createWebHistory } from 'vue-router'
import TrainingView from '@/views/Training.vue'
import MaterialsView from '@/views/Materials.vue'
import TasksView from '@/views/Tasks.vue'

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
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: TasksView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router 