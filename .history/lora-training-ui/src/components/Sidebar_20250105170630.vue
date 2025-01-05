<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <router-link to="/" class="sidebar-header-logo">
        Lora Training
      </router-link>
    </div>

    <nav class="sidebar-menu">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path"
        :to="item.path"
        class="sidebar-menu-item"
        :class="{ active: currentPath === item.path }"
      >
        <i :class="item.icon"></i>
        <span>{{ item.title }}</span>
      </router-link>

      <div class="sidebar-menu-divider"></div>

      <router-link 
        to="/settings" 
        class="sidebar-menu-item"
        :class="{ active: currentPath === '/settings' }"
      >
        <i class="fas fa-cog"></i>
        <span>系统设置</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <span class="sidebar-footer-version" v-if="!isCollapsed">v1.0.0</span>
      <i 
        class="fas" 
        :class="isCollapsed ? 'fa-angle-right' : 'fa-angle-left'"
        @click="toggleCollapse"
      ></i>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  data() {
    return {
      isCollapsed: false,
      menuItems: [
        {
          title: '任务管理',
          path: '/tasks',
          icon: 'fas fa-tasks'
        },
        {
          title: '资产管理',
          path: '/assets',
          icon: 'fas fa-images'
        },
        {
          title: '训练监控',
          path: '/training',
          icon: 'fas fa-chart-line'
        }
      ]
    }
  },
  computed: {
    currentPath() {
      return this.$route.path
    }
  },
  methods: {
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
      this.$emit('collapse', this.isCollapsed)
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 240px;
  background-color: #1e1e2d;
  color: #ffffff;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 100;

  &.collapsed {
    width: 64px;

    .sidebar-header-logo {
      padding: 0 8px;
      justify-content: center;
    }

    .sidebar-menu-item {
      padding: 12px 8px;
      justify-content: center;

      span {
        display: none;
      }
    }

    .sidebar-footer-version {
      display: none;
    }
  }
}

.sidebar-header {
  height: 64px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &-logo {
    height: 100%;
    padding: 0 24px;
    display: flex;
    align-items: center;
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
    text-decoration: none;
  }
}

.sidebar-menu {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;

  &-item {
    display: flex;
    align-items: center;
    padding: 12px 24px;
    color: #a2a3b7;
    text-decoration: none;
    transition: all 0.3s ease;

    i {
      margin-right: 12px;
      width: 20px;
      text-align: center;
    }

    &:hover {
      color: #ffffff;
      background-color: rgba(255, 255, 255, 0.1);
    }

    &.active {
      color: #ffffff;
      background-color: rgba(255, 255, 255, 0.1);
    }
  }

  &-divider {
    height: 1px;
    margin: 16px 0;
    background-color: rgba(255, 255, 255, 0.1);
  }
}

.sidebar-footer {
  height: 48px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;

  &-version {
    color: #a2a3b7;
    font-size: 12px;
  }

  i {
    cursor: pointer;
    color: #a2a3b7;
    transition: all 0.3s ease;

    &:hover {
      color: #ffffff;
    }
  }
}
</style> 