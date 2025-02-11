<template>
  <div class="task-detail">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-section">
        <button class="mac-btn" @click="goBack">
          <ArrowLeftIcon class="btn-icon" />
          返回
        </button>
        <h2 class="task-title">{{ task?.name }}</h2>
        <div class="task-status-badge" :class="getStatusClass(task?.status)">
          {{ getStatusText(task?.status) }}
        </div>
      </div>
      
      <div class="right-section">
        <button 
          v-if="canSubmitMarking"
          class="mac-btn primary"
          :disabled="isLoading"
          @click="handleSubmitMarking"
        >
          <TagIcon class="btn-icon" />
          提交标记
        </button>
        <button 
          v-if="canStartTraining"
          class="mac-btn primary"
          :disabled="isLoading"
          @click="handleStartTraining"
        >
          <PlayIcon class="btn-icon" />
          开始训练
        </button>
        <button 
          v-if="canRestart"
          class="mac-btn warning"
          :disabled="isLoading"
          @click="handleRestart"
        >
          <ArrowPathIcon class="btn-icon" />
          重启任务
        </button>
        <button 
          v-if="canCancel"
          class="mac-btn secondary"
          :disabled="isLoading"
          @click="handleCancel"
        >
          <XMarkIcon class="btn-icon" />
          取消任务
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-area">
      <!-- 左侧图片区域 -->
      <div class="images-section mac-card">
        <div class="section-header">
          <h3>训练图片</h3>
          <div class="header-actions">
            <button 
              class="mac-btn"
              @click="showUploader"
              :title="uploadButtonTitle"
            >
              <PlusIcon class="btn-icon" />
              上传图片
            </button>
          </div>
        </div>

        <!-- 图片网格 -->
        <ImageGrid
          :images="task?.images"
          :loading="isLoading"
          @delete="handleDeleteImage"
          @preview="handlePreview"
        />
      </div>

      <!-- 右侧信息区域 -->
      <div class="info-section">
        <!-- 基本信息卡片 -->
        <div class="mac-card">
          <h3>基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">创建时间</span>
              <span>{{ formatDate(task?.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">图片数量</span>
              <span>{{ task?.images?.length || 0 }} 张</span>
            </div>
            <div class="info-item">
              <span class="label">描述</span>
              <p class="description">{{ task?.description || '暂无描述' }}</p>
            </div>
            <div v-if="task?.marking_asset" class="info-item">
              <span class="label">标记资产</span>
              <div class="asset-info">
                <span class="asset-name">{{ task.marking_asset.name }}</span>
                <span class="asset-ip">{{ task.marking_asset.ip }}</span>
              </div>
            </div>
            <div v-if="task?.training_asset" class="info-item">
              <span class="label">训练资产</span>
              <div class="asset-info">
                <span class="asset-name">{{ task.training_asset.name }}</span>
                <span class="asset-ip">{{ task.training_asset.ip }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 任务状态卡片 -->
        <div class="mac-card">
          <h3>任务状态</h3>
          <TaskStatus :task="task"/>
        </div>
      </div>
    </div>

    <!-- 图片上传模态框 -->
    <BaseModal
      v-model="showUploadModal"
      title="上传训练图片"
      :loading="isUploading"
      @confirm="handleUploadConfirm"
    >
      <template #body>
        <ImageUploader
          ref="uploaderRef"
          :task-id="taskId"
          :disabled="isUploading"
          @update:files="files = $event"
        />
      </template>
    </BaseModal>

    <!-- 图片预览模态框 -->
    <ImageViewer
      v-model="showPreview"
      v-model:image="selectedImage"
      :images="task?.images || []"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeftIcon,
  TagIcon,
  PlayIcon,
  PlusIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import { formatDate } from '@/utils/date'
import message from '@/utils/message'
import ImageGrid from '@/components/tasks/ImageGrid.vue'
import ImageUploader from '@/components/tasks/ImageUploader.vue'
import ImageViewer from '@/components/tasks/ImageViewer.vue'
import BaseModal from '@/components/common/Modal.vue'
import TaskStatus from '@/components/tasks/TaskStatus.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id

// 状态
const task = ref(null)
const isLoading = ref(false)
const isUploading = ref(false)
const showUploadModal = ref(false)
const showPreview = ref(false)
const selectedImage = ref(null)
const files = ref([])
const uploaderRef = ref(null)
const refreshTimer = ref(null)
const REFRESH_INTERVAL = 5000 // 5秒刷新一次

// 获取任务详情
const fetchTask = async () => {
  try {
    isLoading.value = true
    const data = await tasksApi.getTaskById(taskId)
    if (data) {
      task.value = data
      // 根据任务状态决定是否需要继续自动刷新
      if (needsAutoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    } else {
      message.error('任务不存在')
      router.push('/tasks')
    }
  } catch (error) {
    message.error('获取任务详情失败')
    router.push('/tasks')
  } finally {
    isLoading.value = false
  }
}

// 监听任务状态变化
watch(() => task.value?.status, (newStatus, oldStatus) => {
  if (newStatus !== oldStatus) {
    if (needsAutoRefresh.value) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }
})

// 状态相关的计算属性
const canUploadImages = computed(() => {
  return task.value?.status === 'NEW'
})

const canSubmitMarking = computed(() => {
  return task.value?.status === 'NEW' && task.value?.images?.length > 0
})

const canStartTraining = computed(() => {
  return task.value?.status === 'MARKED'
})

// 计算是否可以重启
const canRestart = computed(() => {
  return task.value?.status === 'ERROR'
})

// 计算是否可以取消
const canCancel = computed(() => {
  return ['SUBMITTED', 'MARKED'].includes(task.value?.status)
})

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'NEW': '新建',
    'SUBMITTED': '已提交',
    'MARKING': '标记中',
    'MARKED': '已标记',
    'TRAINING': '训练中',
    'COMPLETED': '已完成',
    'ERROR': '错误'
  }
  return statusMap[status] || status
}

// 获取状态样式类
const getStatusClass = (status) => {
  const classMap = {
    'NEW': 'new',
    'SUBMITTED': 'submitted',
    'MARKING': 'marking',
    'MARKED': 'marked',
    'TRAINING': 'training',
    'COMPLETED': 'completed',
    'ERROR': 'error'
  }
  return classMap[status] || ''
}

// 上传按钮提示文本
const uploadButtonTitle = computed(() => {
  if (canUploadImages.value) {
    return '上传训练图片'
  }
  return `${getStatusText(task.value?.status)}状态不能上传图片`
})

// 显示上传器
const showUploader = () => {
  if (!canUploadImages.value) {
    message.warning(`${getStatusText(task.value?.status)}状态不能上传图片`)
    return
  }
  showUploadModal.value = true
}

// 处理上传确认
const handleUploadConfirm = async () => {
  if (!files.value.length) {
    message.warning('请选择要上传的图片')
    return
  }

  try {
    isUploading.value = true
    const formData = new FormData()
    files.value.forEach(file => {
      formData.append('images', file)
    })

    await tasksApi.uploadImages(taskId, formData)
    message.success('图片上传成功')
    showUploadModal.value = false
    files.value = []
    await fetchTask() // 刷新任务数据
  } catch (error) {
    message.error('图片上传失败')
  } finally {
    isUploading.value = false
  }
}

// 处理图片删除
const handleDeleteImage = async (imageId) => {
  try {
    await tasksApi.deleteImage(taskId, imageId)
    message.success('删除成功')
    fetchTask()
  } catch (error) {
    message.error('删除失败')
  }
}

// 处理图片预览
const handlePreview = (image) => {
  selectedImage.value = image
  showPreview.value = true
}

// 开始标记
const handleSubmitMarking = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.startMarking(taskId)
    
    if (response.error) {
      if (response.error_type === 'VALIDATION_ERROR') {
        message.warning(response.error)
      } else {
        message.error(response.error)
      }
      return
    }
    
    message.success('标记任务已提交')
    task.value = response
  } catch (error) {
    message.error('提交标记任务失败')
  } finally {
    isLoading.value = false
  }
}

// 开始训练
const handleStartTraining = async () => {
  try {
    isLoading.value = true
    await tasksApi.startTraining(taskId)
    message.success('开始训练')
    fetchTask()
  } catch (error) {
    message.error('开始训练失败')
  } finally {
    isLoading.value = false
  }
}

// 处理重启
const handleRestart = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.restartTask(taskId)
    
    if (!response.success) {
      console.log('Restart task failed:', response.error)
      // 处理业务错误
      if (response.error_type === 'VALIDATION_ERROR') {
        message.warning(response.error)
      } else {
        message.error(response.error)
      }
      return
    }
    
    message.success('任务已重启')
    task.value = response.task
  } catch (error) {
    console.error('Restart task error:', error)
    message.error('重启任务失败')
  } finally {
    isLoading.value = false
  }
}

// 处理取消
const handleCancel = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.cancelTask(taskId)
    
    if (!response.success) {
      console.log('Cancel task failed:', response.error)
      if (response.error_type === 'VALIDATION_ERROR') {
        message.warning(response.error)
      } else {
        message.error(response.error)
      }
      return
    }
    
    message.success('任务已取消')
    task.value = response.task
  } catch (error) {
    console.error('Cancel task error:', error)
    message.error('取消任务失败')
  } finally {
    isLoading.value = false
  }
}

// 返回列表
const goBack = () => {
  router.push('/tasks')
}

// 是否需要自动刷新
const needsAutoRefresh = computed(() => {
  const activeStates = ['SUBMITTED', 'MARKING', 'TRAINING']
  return activeStates.includes(task.value?.status)
})

// 开始自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先清除可能存在的定时器
  if (needsAutoRefresh.value) {
    refreshTimer.value = setInterval(async () => {
      if (!isLoading.value) { // 避免重复请求
        await fetchTask()
      }
    }, REFRESH_INTERVAL)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 初始化
onMounted(() => {
  fetchTask()
  startAutoRefresh()
})

// 清理
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.task-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.task-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.right-section {
  display: flex;
  gap: 12px;
}

.content-area {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.images-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 400px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 13px;
  color: var(--text-secondary);
}

.description {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  color: var(--text-primary);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.btn-icon.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 状态徽章样式 */
.task-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.task-status-badge.new {
  background: #F0F9FF;
  color: #0369A1;
}

.task-status-badge.marking {
  background: #FFF7ED;
  color: #C2410C;
}

.task-status-badge.marked {
  background: #F0FDF4;
  color: #166534;
}

.task-status-badge.training {
  background: #EEF2FF;
  color: #4338CA;
}

.task-status-badge.completed {
  background: #ECFDF5;
  color: #047857;
}

.task-status-badge.error {
  background: #FEF2F2;
  color: #B91C1C;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.asset-name {
  font-weight: 500;
}

.asset-ip {
  font-size: 13px;
  color: var(--text-secondary);
}

.mac-btn.warning {
  background-color: #FEF3C7;
  color: #92400E;
}

.mac-btn.warning:hover {
  background-color: #FDE68A;
}

.mac-btn.warning:disabled {
  background-color: #FEF3C7;
  opacity: 0.5;
  cursor: not-allowed;
}

.task-status-badge.submitted {
  background: #F0F7FF;
  color: #1D4ED8;
}

.mac-btn.secondary {
  background-color: #F3F4F6;
  color: #374151;
}

.mac-btn.secondary:hover {
  background-color: #E5E7EB;
}

.mac-btn.secondary:disabled {
  background-color: #F3F4F6;
  opacity: 0.5;
  cursor: not-allowed;
}

.mac-btn:not(:disabled):hover {
  background: var(--background-tertiary);
}
</style> 