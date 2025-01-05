<template>
  <div class="confirm-dialog-wrapper" v-if="show">
    <div class="modal-overlay" @click="$emit('cancel')"></div>
    <div class="modal confirm-dialog">
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
  </div>
</template>

<script>
/**
 * @description 确认对话框组件
 */
export default {
  name: 'ConfirmDialog',
  props: {
    show: {
      type: Boolean,
      default: false
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
  }
}
</script>

<style lang="scss" scoped>
.confirm-dialog-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
}

.confirm-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 8px;
  min-width: 300px;
  max-width: 90%;
  
  .modal-header {
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    
    h3 {
      margin: 0;
      font-size: 18px;
    }
  }
  
  .modal-body {
    padding: 20px;
    
    p {
      margin: 0;
    }
  }
  
  .modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      
      &.cancel-btn {
        background: #f5f5f5;
        
        &:hover {
          background: #e8e8e8;
        }
      }
      
      &.confirm-btn {
        background: var(--primary-color);
        color: white;
        
        &:hover {
          opacity: 0.9;
        }
        
        &.dangerous {
          background: var(--error-color);
        }
      }
    }
  }
}
</style> 