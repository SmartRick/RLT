<template>
  <div class="app-layout">
    <nav class="sidebar">
      <!-- 侧边栏导航 -->
      <router-link to="/assets" class="nav-item">
        <ServerIcon class="nav-icon" />
        资产管理
      </router-link>
      <!-- 其他导航项... -->
    </nav>
    
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import { ServerIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'AppLayout',
  components: {
    ServerIcon
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 220px;
  background: #f8f9fa;
  padding: 20px;
  border-right: 1px solid #e9ecef;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  color: #495057;
  text-decoration: none;
  border-radius: 6px;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: #e9ecef;
}

.nav-item.router-link-active {
  background: #e7f5ff;
  color: #339af0;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}
</style> 