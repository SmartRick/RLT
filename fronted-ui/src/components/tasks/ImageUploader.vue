<template>
  <div class="uploader-container">
    <!-- 拖拽上传区域 -->
    <div 
      class="upload-zone"
      :class="{ 
        'is-dragover': isDragover,
        'is-disabled': disabled 
      }"
      @dragenter.prevent="handleDragEnter"
      @dragleave.prevent="handleDragLeave"
      @dragover.prevent
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-content">
        <CloudArrowUpIcon class="upload-icon" />
        <p class="upload-text">
          拖拽文件到此处或
          <span class="upload-link">点击上传</span>
        </p>
        <p class="upload-hint">
          支持 jpg、png、webp 格式，单次最多可上传 50 张图片
        </p>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length" class="file-list">
      <div 
        v-for="(file, index) in fileList" 
        :key="index"
        class="file-item"
      >
        <!-- 文件预览 -->
        <div class="file-preview">
          <img :src="file.preview" :alt="file.name">
        </div>
        
        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-name text-ellipsis" :title="file.name">
            {{ file.name }}
          </span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
        </div>
        
        <!-- 删除按钮 -->
        <button 
          class="remove-btn"
          @click="removeFile(index)"
          :disabled="disabled"
        >
          <XMarkIcon class="btn-icon" />
        </button>
      </div>
    </div>

    <!-- 隐藏的文件输入框 -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept="image/*"
      class="hidden-input"
      @change="handleFileSelect"
    >
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:files'])

// 状态
const isDragover = ref(false)
const fileList = ref([])
const fileInput = ref(null)

// 触发文件选择
const triggerFileInput = () => {
  if (props.disabled) return
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  addFiles(files)
  e.target.value = '' // 重置input
}

// 处理拖拽
const handleDragEnter = () => {
  if (props.disabled) return
  isDragover.value = true
}

const handleDragLeave = () => {
  isDragover.value = false
}

const handleDrop = (e) => {
  if (props.disabled) return
  isDragover.value = false
  const files = Array.from(e.dataTransfer.files)
  addFiles(files)
}

// 添加文件
const addFiles = (files) => {
  // 检查文件数量限制
  if (files.length + fileList.value.length > 50) {
    alert('最多只能上传50张图片')
    return
  }

  // 过滤图片文件
  const imageFiles = files.filter(file => {
    const isImage = file.type.startsWith('image/')
    const isValidSize = file.size <= 50 * 1024 * 1024 // 50MB 限制
    
    if (!isImage) {
      console.warn(`跳过非图片文件: ${file.name}`)
    }
    if (!isValidSize) {
      console.warn(`文件过大: ${file.name}`)
      alert(`文件 ${file.name} 超过50MB限制`)
    }
    
    return isImage && isValidSize
  })
  
  // 创建预览
  const newFiles = imageFiles.map(file => {
    try {
      const preview = URL.createObjectURL(file)
      return {
        file,
        name: file.name,
        size: file.size,
        preview
      }
    } catch (error) {
      console.error(`创建预览失败: ${file.name}`, error)
      return null
    }
  }).filter(Boolean) // 过滤掉创建预览失败的文件
  
  fileList.value.push(...newFiles)
  emit('update:files', fileList.value)
}

// 移除文件
const removeFile = (index) => {
  try {
    const file = fileList.value[index]
    if (file?.preview) {
      URL.revokeObjectURL(file.preview)
    }
  } catch (error) {
    console.error('清理预览失败:', error)
  }
  fileList.value.splice(index, 1)
  emit('update:files', fileList.value)
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return ''
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

// 组件卸载时清理预览URL
onBeforeUnmount(() => {
  fileList.value.forEach(file => {
    try {
      if (file?.preview) {
        URL.revokeObjectURL(file.preview)
      }
    } catch (error) {
      console.error('清理预览失败:', error)
    }
  })
})
</script>

<style scoped>
.uploader-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-zone:hover {
  border-color: var(--primary-color);
}

.upload-zone.is-dragover {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb), 0.05);
}

.upload-zone.is-disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--text-secondary);
}

.upload-text {
  margin: 0;
  color: var(--text-primary);
}

.upload-link {
  color: var(--primary-color);
  text-decoration: underline;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.uploading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--background-tertiary);
  border-radius: 6px;
}

.file-preview {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.file-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 14px;
  color: var(--text-primary);
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
}

.remove-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: var(--background-secondary);
  color: var(--danger-color);
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.hidden-input {
  display: none;
}

/* 滚动条样式 */
.file-list::-webkit-scrollbar {
  width: 6px;
}

.file-list::-webkit-scrollbar-track {
  background: transparent;
}

.file-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.file-list::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}
</style> 