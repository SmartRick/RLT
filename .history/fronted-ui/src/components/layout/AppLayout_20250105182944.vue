<template>
  <div class="app-layout">
    <header class="top-bar mac-card">
      <div class="left-section">
        <div class="window-controls">
          <span class="control close"></span>
          <span class="control minimize"></span>
          <span class="control maximize"></span>
        </div>
        <nav class="main-nav">
          <router-link 
            v-for="route in mainRoutes" 
            :key="route.path"
            :to="route.path"
            class="nav-item"
            :class="{ active: isRouteActive(route.path) }"
            @click="handleNavClick(route)"
          >
            <component :is="route.icon" class="nav-icon" />
            {{ route.name }}
          </router-link>
        </nav>
      </div>
      
      <div class="right-section">
        <button class="user-menu mac-btn">
          <UserCircleIcon class="user-icon" />
          管理员
        </button>
      </div>
    </header>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  UserCircleIcon,
  ServerIcon,
  Cog6ToothIcon,
  ChartBarIcon 
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const currentRoute = computed(() => route.path)

// 路由配置
const mainRoutes = [
  { path: '/assets', name: '资产管理', icon: ServerIcon },
  { path: '/tasks', name: '任务管理', icon: ChartBarIcon },
  { path: '/settings', name: '系统设置', icon: Cog6ToothIcon }
]

// 判断路由是否激活
const isRouteActive = (path) => {
  if (path === '/assets' && currentRoute.value === '/') {
    return true
  }
  return currentRoute.value === path
}

// 处理导航点击
const handleNavClick = (route) => {
  console.log('点击菜单:', route.name, '路径:', route.path)
}

// 监听路由变化
watch(
  () => route.path,
  (newPath, oldPath) => {
    console.log('路由变化:', {
      from: oldPath,
      to: newPath,
      currentComponent: route.name
    })
  }
)

// 组件挂载时
onMounted(() => {
  console.log('当前路由:', {
    path: route.path,
    name: route.name,
    params: route.params,
    query: route.query
  })
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f7;
}

.top-bar {
  height: 48px;
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.window-controls {
  display: flex;
  gap: 8px;
  padding-right: 8px;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control.close {
  background: #ff5f57;
}

.control.minimize {
  background: #febc2e;
}

.control.maximize {
  background: #28c840;
}

.control:hover {
  filter: brightness(0.9);
}

.main-nav {
  display: flex;
  gap: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #1c1c1e;
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.nav-item.active {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.nav-icon {
  width: 16px;
  height: 16px;
}

.right-section {
  display: flex;
  align-items: center;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  color: #1c1c1e;
  font-size: 14px;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-menu:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-icon {
  width: 20px;
  height: 20px;
  color: #1c1c1e;
}

.main-content {
  flex: 1;
  overflow: auto;
  position: relative;
  height: calc(100vh - 48px);
  width: 100%;
  padding: 20px;
  background: transparent;
}

.main-content > * {
  height: 100%;
  width: 100%;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .window-controls {
    display: none;
  }
  
  .main-nav {
    gap: 12px;
  }
  
  .nav-item {
    padding: 6px 8px;
  }
  
  .nav-item span {
    display: none;
  }
}

/* 添加过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
  position: absolute;
  width: 100%;
  height: 100%;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 