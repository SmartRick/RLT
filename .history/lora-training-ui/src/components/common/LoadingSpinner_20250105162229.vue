<template>
  <div :class="['loading-spinner', { overlay: overlay }]">
    <div class="spinner"></div>
    <div v-if="text" class="loading-text">{{ text }}</div>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    text: {
      type: String,
      default: ''
    },
    overlay: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style lang="scss" scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;

  &.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    z-index: 1000;
    justify-content: center;
  }
}

.loading-text {
  color: var(--text-secondary);
  font-size: 0.9em;
}

@media (prefers-color-scheme: dark) {
  .loading-spinner.overlay {
    background: rgba(0, 0, 0, 0.9);
  }
}
</style> 