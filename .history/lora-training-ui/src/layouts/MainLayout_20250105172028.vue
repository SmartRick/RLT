<template>
  <div class="app-container">
    <Sidebar @collapse="handleCollapse" />
    <div class="main-content" :class="{ expanded: isExpanded }">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import Sidebar from '@/components/Sidebar.vue'

export default {
  name: 'MainLayout',
  components: {
    Sidebar
  },
  data() {
    return {
      isExpanded: false
    }
  },
  methods: {
    handleCollapse(collapsed) {
      this.isExpanded = collapsed
    }
  }
}
</script>

<style lang="scss" scoped>
.app-container {
  min-height: 100vh;
  background: var(--bg-color);
  display: flex;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 20px;
  transition: margin-left 0.3s;
  min-height: 100vh;
  
  &.expanded {
    margin-left: 64px;
  }
}
</style> 