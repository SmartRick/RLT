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
            :class="{ active: route.path === currentPath }"
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
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { routes } from '@/router'
import { 
  UserCircleIcon,
  ServerIcon,
  Cog6ToothIcon,
  ChartBarIcon 
} from '@heroicons/vue/24/outline'
import message from '@/utils/message'

const route = useRoute()

/**
 * @type {Object.<string, import('@heroicons/vue/24/outline').IconComponent>}
 */
const iconMap = {
  Assets: ServerIcon,
  Tasks: ChartBarIcon,
  Settings: Cog6ToothIcon
}

/**
 * 主导航路由配置
 */
const mainRoutes = computed(() => {
  return routes
    .filter(route => route.meta?.title)
    .map(route => ({
      path: route.path,
      name: route.meta.title,
      icon: iconMap[route.name]
    }))
})

/**
 * 当前激活的路由路径
 */
const currentPath = computed(() => route.path)
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
  cursor: pointer;
  user-select: none;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.nav-item.active {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.nav-item.active .nav-icon {
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