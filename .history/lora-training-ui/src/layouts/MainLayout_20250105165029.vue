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

<style lang="scss">
.app-container {
  min-height: 100vh;
  background: #f5f8fa;
}
</style> 