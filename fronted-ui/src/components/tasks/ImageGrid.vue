<template>
  <div class="image-grid-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!images?.length" class="empty-state">
      <PhotoIcon class="empty-icon" />
      <span>暂无图片</span>
    </div>

    <!-- 图片网格 -->
    <div v-else class="image-grid">
      <div 
        v-for="image in images" 
        :key="image.id"
        class="image-item"
      >
        <!-- 图片 -->
        <img 
          :src="getImageUrl(image.preview_url)" 
          :alt="image.filename"
          @click="handlePreview(image)"
        >
        
        <!-- 图片信息 -->
        <div class="image-info">
          <span class="image-name text-ellipsis" :title="image.filename">
            {{ image.filename }}
          </span>
          
          <!-- 操作按钮 -->
          <div class="image-actions">
            <button 
              class="action-btn preview"
              @click="handlePreview(image)"
              title="预览"
            >
              <EyeIcon class="btn-icon" />
            </button>
            <button 
              v-if="canDelete"
              class="action-btn delete"
              @click="handleDelete(image)"
              title="删除"
            >
              <TrashIcon class="btn-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { PhotoIcon, EyeIcon, TrashIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  status: {
    type: String,
    default: 'NEW'
  }
})

const emit = defineEmits(['delete', 'preview'])

// 是否可以删除图片
const canDelete = computed(() => {
  return props.status === 'NEW'
})

// 处理预览
const handlePreview = (image) => {
  emit('preview', image)
}

// 处理删除
const handleDelete = (image) => {
  if (confirm(`确定要删除图片 "${image.filename}" 吗？`)) {
    emit('delete', image.id)
  }
}

// 处理图片URL
const getImageUrl = (url) => {
  if (!url) return ''
  // 直接使用相对路径，让代理处理
  return url
}
</script>

<style scoped>
.image-grid-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1px;  /* 防止阴影被裁剪 */
}

.loading-state,
.empty-state {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.empty-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 4px;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: var(--background-secondary);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.image-item img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  cursor: pointer;
}

.image-info {
  padding: 8px;
  background: var(--background-secondary);
}

.image-name {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
  display: block;
}

.image-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--background-tertiary);
}

.action-btn.preview {
  color: var(--primary-color);
}

.action-btn.delete {
  color: var(--danger-color);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 滚动条样式 */
.image-grid-container::-webkit-scrollbar {
  width: 8px;
}

.image-grid-container::-webkit-scrollbar-track {
  background: transparent;
}

.image-grid-container::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.image-grid-container::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}
</style> 