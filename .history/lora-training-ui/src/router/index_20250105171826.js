import Vue from 'vue'
import VueRouter from 'vue-router'
import TrainingView from '@/views/Training.vue'
import MaterialsView from '@/views/Materials.vue'
import TasksView from '@/views/Tasks.vue'

Vue.use(VueRouter)

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

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router 