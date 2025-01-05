<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <h1 class="logo">Lora Training</h1>
      <button class="collapse-btn" @click="toggleCollapse">
        {{ collapsed ? '›' : '‹' }}
      </button>
    </div>
    <nav class="nav-menu">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :title="collapsed ? item.title : ''"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="title" v-show="!collapsed">{{ item.title }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script>
/**
 * @description 侧边栏导航组件
 */
export default {
  name: 'Sidebar',
  data() {
    return {
      collapsed: false,
      menuItems: [
        { path: '/training', title: '训练管理', icon: '🎯' },
        { path: '/materials', title: '素材管理', icon: '📁' },
        { path: '/tasks', title: '任务列表', icon: '📋' }
      ]
    }
  },
  methods: {
    toggleCollapse() {
      this.collapsed = !this.collapsed
      this.$emit('collapse', this.collapsed)
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  background: var(--sidebar-bg, #fff);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  width: 240px;
  transition: width 0.3s;
  z-index: 100;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);

  .logo {
    font-size: 1.2em;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .collapse-btn {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;

    &:hover {
      background: var(--hover-bg);
    }
  }
}

.nav-menu {
  padding: 20px 0;

  .nav-item {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    text-decoration: none;
    color: var(--text-color);
    gap: 12px;

    &:hover {
      background: var(--hover-bg);
    }

    &.router-link-active {
      background: var(--active-bg);
      color: var(--primary-color);
    }

    .icon {
      font-size: 1.2em;
      width: 24px;
      text-align: center;
    }

    .title {
      white-space: nowrap;
    }
  }
}
</style> 