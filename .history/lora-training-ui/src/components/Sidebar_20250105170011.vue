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

<style lang="scss">
@use '@/styles/variables' as *;
@use '@/styles/sidebar';
</style> 