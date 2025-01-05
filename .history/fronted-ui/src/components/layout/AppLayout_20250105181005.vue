<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <div class="sidebar mac-card">
      <div class="logo">
        <img src="@/assets/logo.png" alt="Logo">
        <span class="logo-text">资产管理系统</span>
      </div>
      
      <nav class="nav-menu">
        <router-link 
          v-for="route in routes" 
          :key="route.path"
          :to="route.path"
          class="nav-item"
          :class="{ active: currentRoute.path.includes(route.path) }"
        >
          <component :is="route.meta?.icon" class="nav-icon" />
          <span class="nav-text">{{ route.meta?.title }}</span>
        </router-link>
      </nav>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ServerIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'AppLayout',
  
  components: {
    ServerIcon
  },

  setup() {
    const router = useRouter()
    const currentRoute = useRoute()

    const routes = computed(() => {
      return router.options.routes[0].children.filter(route => route.meta?.title)
    })

    return {
      routes,
      currentRoute
    }
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 240px;
  height: 100%;
  background: white;
  border-radius: 0;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 0 20px;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo img {
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s;
}

.nav-item:hover {
  background: var(--hover-color);
  color: var(--primary-color);
}

.nav-item.active {
  background: var(--primary-color);
  color: white;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.main-content {
  flex: 1;
  overflow: hidden;
  background: var(--background-secondary);
}
</style> 