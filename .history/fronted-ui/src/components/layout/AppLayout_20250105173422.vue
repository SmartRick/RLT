<template>
  <div class="app-wrapper">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <img src="@/assets/logo.png" alt="Logo" class="logo">
        <h1 v-show="!isCollapsed">AI Studio</h1>
      </div>

      <nav class="nav-menu">
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentRoute === item.path }"
        >
          <i :class="item.icon"></i>
          <span v-show="!isCollapsed">{{ item.title }}</span>
        </router-link>
      </nav>

      <button class="collapse-btn" @click="toggleSidebar">
        <i :class="isCollapsed ? 'icon-expand' : 'icon-collapse'"></i>
      </button>
    </aside>

    <main class="main-content">
      <header class="top-bar mac-card">
        <div class="breadcrumb">
          <h2>{{ currentPageTitle }}</h2>
        </div>
        <div class="actions">
          <div class="search-bar">
            <input 
              type="text" 
              class="mac-input" 
              placeholder="搜索..." 
              v-model="searchQuery"
            >
          </div>
          <div class="user-profile">
            <img src="@/assets/avatar.png" alt="User" class="avatar">
            <span>管理员</span>
          </div>
        </div>
      </header>

      <div class="content-wrapper">
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
      isCollapsed: false,
      searchQuery: '',
      menuItems: [
        { path: '/assets', title: '资产管理', icon: 'icon-assets' },
        { path: '/tasks', title: '任务管理', icon: 'icon-tasks' },
        { path: '/training', title: '训练数据', icon: 'icon-training' },
        { path: '/settings', title: '系统设置', icon: 'icon-settings' }
      ]
    }
  },
  computed: {
    currentRoute() {
      return this.$route.path
    },
    currentPageTitle() {
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
.app-wrapper {
  display: flex;
  height: 100vh;
  background-color: var(--background-primary);
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1F2937 0%, #111827 100%);
  color: white;
  transition: all var(--transition-speed);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 100;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 32px;
  height: 32px;
}

.nav-menu {
  padding: 12px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: #E5E7EB;
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all var(--transition-speed);
  gap: 12px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: 70px;
  margin: 16px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: var(--border-radius);
}

.actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-bar {
  position: relative;
}

.search-bar input {
  width: 240px;
  padding-left: 36px;
  background: url('@/assets/icons/search.svg') no-repeat 12px center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.content-wrapper {
  flex: 1;
  padding: 0 16px 16px;
  overflow-y: auto;
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-speed);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 