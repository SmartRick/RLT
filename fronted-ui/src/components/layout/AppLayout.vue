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
          <router-link v-for="route in mainRoutes" :key="route.path" :to="route.path" class="nav-item"
            :class="{ active: isRouteActive(route.path) }">
            <component :is="route.icon" class="nav-icon" />
            {{ route.name }}
          </router-link>
        </nav>
      </div>

      <div class="right-section">
        <div class="logo-container">
          <img src="@/assets/logo.png" alt="RLT Logo" class="logo-img" />
          <div class="logo-text-container">
            <span class="logo-text">RICK LORA TRAINER(RLT)</span>
            <span class="logo-subtitle">RICK 风格模型训练器</span>
          </div>
        </div>
      </div>
    </header>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { routes } from '@/router'
import {
  ServerIcon,
  Cog6ToothIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'

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

/**
 * 判断路由是否激活
 * @param {string} path - 路由路径
 * @returns {boolean} - 是否激活
 */
const isRouteActive = (path) => {
  // 根路由特殊处理
  if (path === '/') {
    return currentPath.value === '/'
  }

  // 检查当前路径是否以指定路径开头
  // 确保它是一个完整的路径段（例如：/tasks 匹配 /tasks 和 /tasks/123，但不匹配 /tasks-other）
  return currentPath.value === path ||
    (currentPath.value.startsWith(path) &&
      (currentPath.value[path.length] === '/' || currentPath.value.length === path.length))
}
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

.logo-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-img {
  width: 30px;
  height: 30px;
}

.logo-text-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.logo-text {
  font-size: 14px;
  font-weight: 600;
  width: 100%;
}

.logo-subtitle {
  font-size: 12px;
  font-weight: 400;
  color: #666;
  width: 100%;
  text-align: center;
  letter-spacing: 3px;
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

.main-content>* {
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
</style>