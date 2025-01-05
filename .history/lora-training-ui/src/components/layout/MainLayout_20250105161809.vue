<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="logo">
        <h1>Lora Training</h1>
      </div>
      <ul class="nav-menu">
        <li 
          v-for="item in menuItems" 
          :key="item.path"
          :class="{ active: currentRoute === item.path }"
        >
          <router-link :to="item.path">
            <span class="icon">{{ item.icon }}</span>
            <span class="text">{{ item.title }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="main-content">
      <header class="top-bar">
        <div class="breadcrumb">
          {{ currentPageTitle }}
        </div>
        <div class="user-actions">
          <button class="action-btn" @click="showLogs">
            <span class="icon">📝</span>
            日志
          </button>
        </div>
      </header>

      <main class="page-content">
        <router-view></router-view>
      </main>
    </div>

    <!-- 日志查看器 -->
    <LogViewer 
      v-if="showLogViewer"
      @close="closeLogs"
    />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import LogViewer from '@/components/LogViewer.vue'

export default {
  name: 'MainLayout',
  components: {
    LogViewer
  },
  setup() {
    const route = useRoute()
    const showLogViewer = ref(false)

    const menuItems = [
      { path: '/', title: '仪表盘', icon: '📊' },
      { path: '/materials', title: '训练素材', icon: '📁' },
      { path: '/tasks', title: '训练任务', icon: '🔄' },
      { path: '/assets', title: '资产管理', icon: '💻' },
      { path: '/settings', title: '系统设置', icon: '⚙️' }
    ]

    const currentRoute = computed(() => route.path)
    const currentPageTitle = computed(() => route.meta.title)

    const showLogs = () => {
      showLogViewer.value = true
    }

    const closeLogs = () => {
      showLogViewer.value = false
    }

    return {
      menuItems,
      currentRoute,
      currentPageTitle,
      showLogViewer,
      showLogs,
      closeLogs
    }
  }
}
</script>

<style lang="scss" scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 250px;
  background: var(--sidebar-background);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;

  .logo {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    
    h1 {
      margin: 0;
      font-size: 1.5em;
      color: var(--primary-color);
    }
  }
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    a {
      display: flex;
      align-items: center;
      padding: 15px 20px;
      color: var(--text-color);
      text-decoration: none;
      transition: background-color var(--transition-speed);

      .icon {
        margin-right: 10px;
        font-size: 1.2em;
      }

      &:hover {
        background: var(--hover-background);
      }
    }

    &.active a {
      background: var(--primary-color);
      color: white;
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: 60px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--background-color);

  .breadcrumb {
    font-size: 1.2em;
    font-weight: 500;
  }
}

.page-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}
</style> 