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
        <!-- 图片容器 -->
        <div class="image-container">
          <!-- 删除按钮 -->
          <button 
            v-if="canDelete"
            class="delete-btn"
            @click.stop="handleDelete(image)"
            title="删除"
          >
            <TrashIcon class="btn-icon" />
          </button>
          
          <!-- 图片 -->
          <img 
            :src="image.preview_url" 
            :alt="image.filename"
            @click="handlePreview(image)"
          >
        </div>
        
        <!-- 图片信息 -->
        <div class="image-info">
          <span class="image-name text-ellipsis" :title="image.filename">
            {{ image.filename }}
          </span>
          
          <!-- 打标文本（只在MARKED及之后的状态显示） -->
          <div v-if="showMarkedText && markedTexts[image.filename]" class="marked-text-container">
            <div 
              class="marked-text" 
              :class="{ 'expanded': expandedTexts.includes(image.filename) }"
              @click="toggleExpandText(image.filename)"
            >
              {{ markedTexts[image.filename] }}
            </div>
            <div class="text-actions">
              <button 
                class="text-toggle" 
                @click="toggleExpandText(image.filename)"
              >
                {{ expandedTexts.includes(image.filename) ? '收起' : '展开' }}
              </button>
              <button
                v-if="canEdit"
                class="text-edit"
                @click="startEditText(image.filename)"
              >
                编辑
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 文本编辑模态框 -->
    <BaseModal
      v-model="showEditModal"
      title="编辑打标文本"
      :loading="isEditing"
      @confirm="handleEditConfirm"
    >
      <template #body>
        <div class="edit-text-container">
          <div class="edit-filename">{{ currentEditingFilename }}</div>
          <textarea
            v-model="editingTextContent"
            class="edit-textarea"
            placeholder="请输入打标文本"
            rows="6"
          ></textarea>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { PhotoIcon, TrashIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import BaseModal from '@/components/common/Modal.vue'

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
  },
  markedTexts: {
    type: Object,
    default: () => ({})
  },
  taskId: {
    type: [Number, String],
    default: ''
  }
})

const emit = defineEmits(['delete', 'preview', 'update:markedText'])

// 是否可以删除图片
const canDelete = computed(() => {
  return props.status === 'NEW'
})

// 是否可以编辑打标文本
const canEdit = computed(() => {
  return ['MARKED', 'TRAINING', 'COMPLETED'].includes(props.status)
})

// 是否显示打标文本
const showMarkedText = computed(() => {
  return ['MARKED', 'TRAINING', 'COMPLETED'].includes(props.status)
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

// 打标文本展开状态管理
const expandedTexts = ref([])

// 切换文本展开状态
const toggleExpandText = (filename) => {
  const index = expandedTexts.value.indexOf(filename)
  if (index === -1) {
    expandedTexts.value.push(filename)
  } else {
    expandedTexts.value.splice(index, 1)
  }
}

// 文本编辑相关
const showEditModal = ref(false)
const currentEditingFilename = ref('')
const editingTextContent = ref('')
const isEditing = ref(false)

// 开始编辑文本
const startEditText = (filename) => {
  currentEditingFilename.value = filename
  editingTextContent.value = props.markedTexts[filename] || ''
  showEditModal.value = true
}

// 确认编辑
const handleEditConfirm = () => {
  if (!currentEditingFilename.value) return
  
  emit('update:markedText', {
    filename: currentEditingFilename.value,
    content: editingTextContent.value
  })
  
  showEditModal.value = false
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

.image-container {
  position: relative;
  width: 100%;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-container:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--danger-color);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.image-container img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  cursor: pointer;
  display: block;
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

/* 打标文本样式 */
.marked-text-container {
  margin-top: 8px;
  border-top: 1px solid var(--border-color-light);
  padding-top: 8px;
}

.marked-text {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  background: var(--background-tertiary);
  padding: 6px;
  border-radius: 4px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  text-overflow: ellipsis;
  cursor: pointer;
}

.marked-text.expanded {
  display: block;
  -webkit-line-clamp: unset;
  white-space: pre-wrap;
}

.text-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.text-toggle, .text-edit {
  font-size: 11px;
  color: var(--primary-color);
  background: transparent;
  border: none;
  padding: 2px 4px;
  cursor: pointer;
  border-radius: 2px;
}

.text-toggle:hover, .text-edit:hover {
  background: color-mix(in srgb, var(--primary-color) 10%, transparent);
}

/* 编辑模态框样式 */
.edit-text-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-filename {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.edit-textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

.edit-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
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