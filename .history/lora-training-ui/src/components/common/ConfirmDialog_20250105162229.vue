<template>
  <div v-if="show" class="modal-overlay" @click="$emit('cancel')"></div>
  <div v-if="show" class="modal confirm-dialog">
    <div class="modal-header">
      <h3>{{ title }}</h3>
    </div>
    <div class="modal-body">
      <p>{{ message }}</p>
    </div>
    <div class="modal-footer">
      <button 
        class="cancel-btn"
        @click="$emit('cancel')"
      >
        {{ cancelText }}
      </button>
      <button 
        class="confirm-btn"
        @click="$emit('confirm')"
        :class="{ dangerous }"
      >
        {{ confirmText }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    title: {
      type: String,
      default: '确认'
    },
    message: {
      type: String,
      required: true
    },
    confirmText: {
      type: String,
      default: '确定'
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    dangerous: {
      type: Boolean,
      default: false
    }
  },
  emits: ['confirm', 'cancel']
}
</script>

<style lang="scss" scoped>
.confirm-dialog {
  width: 90%;
  max-width: 400px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;

  button {
    padding: 8px 16px;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }

    &.cancel-btn {
      background: var(--border-color);
      color: var(--text-color);
    }

    &.confirm-btn {
      background: var(--primary-color);
      color: white;

      &.dangerous {
        background: var(--error-color);
      }
    }
  }
}
</style> 