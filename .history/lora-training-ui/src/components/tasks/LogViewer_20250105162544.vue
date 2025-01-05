<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')"></div>
  <div v-if="show" class="modal log-viewer-modal">
    <div class="modal-header">
      <h3>任务日志</h3>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    <div class="modal-body">
      <div class="log-content">
        <pre>{{ content }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogViewerModal',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    content: {
      type: String,
      default: ''
    }
  },
  emits: ['close']
}
</script>

<style lang="scss" scoped>
.log-viewer-modal {
  width: 90%;
  max-width: 800px;
  height: 80vh;
}

.log-content {
  height: calc(100% - 60px);
  overflow: auto;
  background: var(--input-background);
  padding: 10px;
  border-radius: var(--border-radius);

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: monospace;
    font-size: 0.9em;
    line-height: 1.5;
  }
}
</style> 