<template>
  <div :class="['task-card', task.status.toLowerCase()]">
    <div class="task-header">
      <h3>{{ task.folder_name }}</h3>
      <span :class="['status-badge', task.status.toLowerCase()]">
        {{ task.status }}
      </span>
    </div>
    <div class="task-info">
      <p>
        <strong>创建时间:</strong>
        <span>{{ formatDate(task.created_at) }}</span>
      </p>
      <p v-if="task.updated_at">
        <strong>更新时间:</strong>
        <span>{{ formatDate(task.updated_at) }}</span>
      </p>
      <p v-if="task.task_id">
        <strong>任务ID:</strong>
        <span>{{ task.task_id }}</span>
      </p>
      <p v-if="task.lora_path">
        <strong>Lora路径:</strong>
        <span>{{ task.lora_path }}</span>
      </p>
      <p v-if="task.error" class="error-message">
        <strong>错误信息:</strong>
        <span>{{ task.error }}</span>
      </p>
    </div>
    <div class="task-actions">
      <button 
        v-if="canRetry"
        class="action-btn retry"
        @click="$emit('retry', task)"
      >
        重试
      </button>
      <button 
        v-if="canCancel"
        class="action-btn cancel"
        @click="$emit('cancel', task)"
      >
        取消
      </button>
      <button 
        class="action-btn view-log"
        @click="$emit('view-log', task)"
      >
        查看日志
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskCard',
  props: {
    task: {
      type: Object,
      required: true
    }
  },
  computed: {
    canRetry() {
      return this.task.status.includes('FAILED')
    },
    canCancel() {
      return ['PENDING', 'DOWNLOADING', 'TRAINING'].includes(this.task.status)
    }
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style lang="scss" scoped>
.task-card {
  background: var(--card-background);
  border-radius: var(--border-radius);
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &.failed {
    border-left: 4px solid var(--error-color);
  }

  &.completed {
    border-left: 4px solid var(--success-color);
  }

  &.training {
    border-left: 4px solid var(--primary-color);
  }
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 1.1em;
  }
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;

  &.downloading { background: var(--info-color); color: white; }
  &.pending { background: var(--warning-color); color: white; }
  &.training { background: var(--primary-color); color: white; }
  &.completed { background: var(--success-color); color: white; }
  &.failed { background: var(--error-color); color: white; }
}

.task-info {
  margin: 10px 0;
  font-size: 0.9em;

  p {
    margin: 5px 0;
    display: flex;
    gap: 10px;

    strong {
      min-width: 80px;
    }
  }

  .error-message {
    color: var(--error-color);
  }
}

.task-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;

  .action-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }

    &.retry {
      background: var(--warning-color);
      color: white;
    }

    &.cancel {
      background: var(--error-color);
      color: white;
    }

    &.view-log {
      background: var(--info-color);
      color: white;
    }
  }
}
</style> 