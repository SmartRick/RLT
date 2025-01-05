<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo-container">
        <img src="@/assets/logo.png" alt="Logo" class="logo">
        <span v-show="!isCollapsed">AI Studio 🚀</span>
      </div>
      
      <nav class="menu">
        <router-link to="/assets" class="menu-item">
          <i class="icon-assets"></i>
          <span v-show="!isCollapsed">资产管理 📦</span>
        </router-link>
        
        <router-link to="/tasks" class="menu-item">
          <i class="icon-tasks"></i>
          <span v-show="!isCollapsed">任务管理 ⚡</span>
        </router-link>
        
        <router-link to="/training" class="menu-item">
          <i class="icon-training"></i>
          <span v-show="!isCollapsed">训练数据集 🎯</span>
        </router-link>
        
        <router-link to="/settings" class="menu-item">
          <i class="icon-settings"></i>
          <span v-show="!isCollapsed">系统设置 ⚙️</span>
        </router-link>
      </nav>
      
      <div class="collapse-btn" @click="toggleSidebar">
        <i :class="isCollapsed ? 'icon-expand' : 'icon-collapse'"></i>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="top-bar">
        <div class="breadcrumb">{{ currentPath }}</div>
        <div class="user-info">
          <span>👤 管理员</span>
        </div>
      </header>
      
      <div class="content-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'AppLayout',
  data() {
    return {
      isCollapsed: false
    }
  },
  computed: {
    currentPath() {
      return this.$route.meta.title || '首页'
    }
  },
  methods: {
    toggleSidebar() {
      this.isCollapsed = !this.isCollapsed
    }
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
  color: white;
  transition: all 0.3s ease;
}

.sidebar.collapsed {
  width: 64px;
}

.logo-container {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 32px;
  height: 32px;
}

.menu {
  padding: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: white;
  text-decoration: none;
  transition: all 0.3s ease;
  gap: 10px;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
}

.main-content {
  flex: 1;
  background: #f5f7fa;
  overflow-y: auto;
}

.top-bar {
  height: 60px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.content-container {
  padding: 20px;
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 