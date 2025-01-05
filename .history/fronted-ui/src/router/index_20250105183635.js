import { createRouter, createWebHistory } from 'vue-router'
import Assets from '../views/Assets.vue'
import Tasks from '../views/Tasks.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
      component: Tasks
    },
    {
      path: '/settings',
      name: 'Settings',
      component: Settings
    }
  ]
})

export default router 