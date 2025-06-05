<template>
  <div class="task-detail">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-section">
        <h2 class="task-title">{{ task?.name }}</h2>
        <div class="task-status-badge" :class="getStatusClass(task?.status)">
          {{ getStatusText(task?.status) }}
        </div>
      </div>

      <!-- 中间状态栏 -->
      <div class="center-section" v-if="task">
        <div class="status-timeline">
          <TaskStatus :task="task" :compact="true" />
        </div>
      </div>

      <div class="right-section">
        <button v-if="canSubmitMarking" class="mac-btn primary" :disabled="isLoading" @click="handleSubmitMarking">
          <TagIcon class="btn-icon" />
          提交标记
        </button>
        <button v-if="canStartTraining" class="mac-btn primary" :disabled="isLoading" @click="handleStartTraining">
          <PlayIcon class="btn-icon" />
          开始训练
        </button>
        <button v-if="canRestart" class="mac-btn warning" :disabled="isLoading" @click="handleRestart">
          <ArrowPathIcon class="btn-icon" />
          重启任务
        </button>
        <button v-if="canCancel" class="mac-btn secondary" :disabled="isLoading" @click="handleCancel">
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
            <button class="mac-btn" @click="showUploader" :title="uploadButtonTitle">
              <PlusIcon class="btn-icon" />
              上传图片
            </button>
          </div>
        </div>

        <!-- 图片网格 -->
        <ImageGrid :images="task?.images" :loading="isLoading" :status="task?.status" :marked-texts="markedTexts"
          :task-id="taskId" @delete="handleDeleteImage" @preview="handlePreview"
          @update:marked-text="handleUpdateMarkedText" />
      </div>

      <!-- 右侧信息区域 -->
      <div class="info-section">
        <!-- 基本信息卡片 -->
        <div class="mac-card">
          <h3>基本信息</h3>
          <div class="info-grid">
            <div class="info-row">
              <div class="info-item">
                <span class="label">创建时间</span>
                <span>{{ formatDate(task?.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="label">图片数量</span>
                <span>{{ task?.images?.length || 0 }} 张</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item">
                <span class="label">标记资产</span>
                <div class="asset-info" v-if="task?.marking_asset">
                  <span class="asset-name">{{ task.marking_asset.name }}</span>
                  <span class="asset-ip">({{ task.marking_asset.ip }})</span>
                </div>
                <span v-else class="no-asset">暂无</span>
              </div>
              <div class="info-item">
                <span class="label">训练资产</span>
                <div class="asset-info" v-if="task?.training_asset">
                  <span class="asset-name">{{ task.training_asset.name }}</span>
                  <span class="asset-ip">({{ task.training_asset.ip }})</span>
                </div>
                <span v-else class="no-asset">暂无</span>
              </div>
            </div>
            <div class="info-item full-width">
              <span class="label">描述</span>
              <p class="description">{{ task?.description || '暂无描述' }}</p>
            </div>
          </div>
        </div>

        <!-- 任务配置卡片 -->
        <TaskConfigCard v-if="task" v-model:task="task" :can-edit="canEditConfig" @update:task="handleTaskUpdate" />
      </div>
    </div>

    <!-- 图片上传模态框 -->
    <BaseModal v-model="showUploadModal" title="上传训练图片" :loading="isUploading" @confirm="handleUploadConfirm">
      <template #body>
        <ImageUploader ref="uploaderRef" :task-id="taskId" :disabled="isUploading" @update:files="files = $event" />
      </template>
    </BaseModal>

    <!-- 图片预览模态框 -->
    <ImageViewer v-model="showPreview" v-model:image="selectedImage" :images="task?.images || []" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  TagIcon,
  PlayIcon,
  PlusIcon,
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import { formatDate } from '@/utils/datetime'
import message from '@/utils/message'
import ImageGrid from '@/components/tasks/ImageGrid.vue'
import ImageUploader from '@/components/tasks/ImageUploader.vue'
import ImageViewer from '@/components/tasks/ImageViewer.vue'
import BaseModal from '@/components/common/Modal.vue'
import TaskStatus from '@/components/tasks/TaskStatus.vue'
import TaskConfigCard from '@/components/tasks/TaskConfigCard.vue'
import {
  getStatusText,
  getStatusClass,
  isTaskActive as checkTaskActive,
  statusDetailColorMap
} from '@/utils/taskStatus'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id)

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
const statusUpdating = ref(false) // 添加状态更新标志
const markedTexts = ref({}) // 打标文本数据

// 获取任务详情
const fetchTask = async () => {
  if (!taskId.value) return // 添加ID判断，防止无ID时请求

  try {
    isLoading.value = true
    const data = await tasksApi.getTaskById(taskId.value)
    if (data) {
      task.value = data
      // 如果任务状态是MARKED或之后，获取打标文本
      if (['MARKED', 'TRAINING', 'COMPLETED'].includes(data.status)) {
        await fetchMarkedTexts()

        // 处理图片URL，将uploads替换为marked
        if (data.images && data.images.length > 0) {
          data.images.forEach(image => {
            if (image.preview_url) {
              image.preview_url = image.preview_url.replace('/uploads/', '/marked/')
              // 将图片URL后缀统一替换为png
              if (image.preview_url && !image.preview_url.endsWith('.png')) {
                const urlWithoutExtension = image.preview_url.substring(0, image.preview_url.lastIndexOf('.'));
                image.preview_url = `${urlWithoutExtension}.png`;
              }
            }
          })
        }
      }

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

// 获取打标文本
const fetchMarkedTexts = async () => {
  if (!taskId.value) return

  try {
    const data = await tasksApi.getMarkedTexts(taskId.value)
    if (data) {
      markedTexts.value = data
    }
  } catch (error) {
    console.error('获取打标文本失败', error)
    message.error('获取打标文本失败')
  }
}

// 只更新任务状态
const updateTaskStatus = async () => {
  if (!taskId.value || !task.value) return

  try {
    statusUpdating.value = true
    const statusData = await tasksApi.getTaskStatus(taskId.value)

    if (statusData) {
      // 只更新状态相关字段，而不替换整个task对象
      if (task.value.status !== statusData.status) {
        task.value.status = statusData.status
        task.value.status_history = statusData.status_history

        // 如果状态变为完成或错误，获取完整任务信息
        if (['COMPLETED', 'ERROR'].includes(statusData.status)) {
          await fetchTask()
        }
      }

      // 根据任务状态决定是否需要继续自动刷新
      if (!needsAutoRefresh.value) {
        stopAutoRefresh()
      }
    }
  } catch (error) {
    console.error('更新任务状态失败', error)
  } finally {
    statusUpdating.value = false
  }
}

// 监听任务ID变化，立即获取对应任务详情
watch(taskId, (newId, oldId) => {
  // 仅当ID真实变化且有效时执行
  if (newId && newId !== oldId) {
    fetchTask()
  }
})

// 监听任务状态变化
watch(() => task.value?.status, (newStatus, oldStatus) => {
  if (newStatus !== oldStatus) {
    // 如果状态变为MARKED或之后，获取打标文本
    if (['MARKED', 'TRAINING', 'COMPLETED'].includes(newStatus) &&
      !['MARKED', 'TRAINING', 'COMPLETED'].includes(oldStatus)) {
      fetchMarkedTexts()
    }

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
      formData.append('files', file)
    })

    await tasksApi.uploadImages(taskId.value, formData)
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
    await tasksApi.deleteImage(taskId.value, imageId)
    message.success('删除成功')
    fetchTask()
  } catch (error) {
    message.error('删除失败')
  }
}

// 处理图片预览
const handlePreview = (image) => {
  console.log("image", image)
  selectedImage.value = image
  showPreview.value = true
}

// 开始标记
const handleSubmitMarking = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.startMarking(taskId.value)

    message.success('标记任务已提交')
    task.value = response
  } catch (error) {
    message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 开始训练
const handleStartTraining = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.startTraining(taskId.value)
    message.success('开始训练')
    task.value = response
  } catch (error) {
    message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 处理重启
const handleRestart = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.restartTask(taskId.value)
    message.success('任务已重启')
    task.value = response
  } catch (error) {
    message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 处理取消
const handleCancel = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.cancelTask(taskId.value)
    message.success('任务已取消')
    task.value = response
  } catch (error) {
    message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 是否需要自动刷新
const needsAutoRefresh = computed(() => {
  return checkTaskActive(task.value?.status)
})

// 开始自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先清除可能存在的定时器
  if (needsAutoRefresh.value) {
    refreshTimer.value = setInterval(async () => {
      if (!isLoading.value && !statusUpdating.value) { // 避免重复请求
        await updateTaskStatus() // 使用轻量级更新函数代替完整获取
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

// 处理更新打标文本
const handleUpdateMarkedText = async ({ filename, content }) => {
  if (!taskId.value || !filename) return

  try {
    isLoading.value = true
    await tasksApi.updateMarkedText(taskId.value, filename, content)

    // 更新本地缓存
    markedTexts.value[filename] = content

    message.success('打标文本更新成功')
  } catch (error) {
    console.error('更新打标文本失败', error)
    message.error('更新打标文本失败')
  } finally {
    isLoading.value = false
  }
}

// 添加可以编辑配置的计算属性
const canEditConfig = computed(() => {
  return ['NEW'].includes(task.value?.status);
});

// 处理任务更新
const handleTaskUpdate = async (updatedTask) => {
  try {
    isLoading.value = true;

    // 创建包含需要更新字段的对象
    const updateData = {
      use_global_mark_config: updatedTask.use_global_mark_config,
      use_global_training_config: updatedTask.use_global_training_config
    };

    // 根据全局配置状态决定是否包含配置
    if (!updatedTask.use_global_mark_config) {
      updateData.mark_config = updatedTask.mark_config;
    }

    if (!updatedTask.use_global_training_config) {
      updateData.training_config = updatedTask.training_config;
    }

    // 调用API更新任务配置
    const result = await tasksApi.updateTask(taskId.value, updateData);

    // 更新本地任务数据
    task.value = result;
    message.success('任务配置已更新');
  } catch (error) {
    console.error('更新任务配置失败', error);
    message.error('更新任务配置失败');
  } finally {
    isLoading.value = false;
  }
};

// 初始化
onMounted(() => {
  if (taskId.value) {
    fetchTask()
    startAutoRefresh()
  }
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
  overflow: hidden;
  /* 修改为hidden，防止整个页面滚动 */
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0px 16px;
  flex-shrink: 0;
  height: auto;
  /* 调整为自适应高度 */
  min-height: 70px;
  /* 确保有足够高度显示状态图标和名称 */
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

/* 添加中间部分样式 */
.center-section {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 2;
  position: relative;
  padding: 5px 0;
  /* 增加上下内边距 */
}

.status-timeline {
  position: relative;
  cursor: pointer;
}

.task-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.right-section {
  display: flex;
  gap: 12px;
  flex: 1;
  justify-content: flex-end;
}

.content-area {
  display: grid;
  grid-template-columns: 4fr 1fr;
  /* 修改比例，从2:1改为3:1 */
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

.images-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: auto;
  /* 修改为auto，允许左侧区域在需要时滚动 */
  height: 100%;
  /* 确保高度为100% */
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
  min-width: 280px;
  /* 减小最小宽度 */
  height: 100%;
  /* 确保高度为100% */
  overflow-y: auto;
  /* 允许右侧区域单独滚动 */
  padding-right: 6px;
  /* 为滚动条留出空间 */
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.info-row {
  display: flex;
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.info-item.full-width {
  flex-basis: 100%;
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
  to {
    transform: rotate(360deg);
  }
}

/* 状态徽章样式 */
.task-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.task-status-badge.new {
  background: v-bind('statusDetailColorMap.NEW.background');
  color: v-bind('statusDetailColorMap.NEW.color');
}

.task-status-badge.submitted {
  background: v-bind('statusDetailColorMap.SUBMITTED.background');
  color: v-bind('statusDetailColorMap.SUBMITTED.color');
}

.task-status-badge.marking {
  background: v-bind('statusDetailColorMap.MARKING.background');
  color: v-bind('statusDetailColorMap.MARKING.color');
}

.task-status-badge.marked {
  background: v-bind('statusDetailColorMap.MARKED.background');
  color: v-bind('statusDetailColorMap.MARKED.color');
}

.task-status-badge.training {
  background: v-bind('statusDetailColorMap.TRAINING.background');
  color: v-bind('statusDetailColorMap.TRAINING.color');
}

.task-status-badge.completed {
  background: v-bind('statusDetailColorMap.COMPLETED.background');
  color: v-bind('statusDetailColorMap.COMPLETED.color');
}

.task-status-badge.error {
  background: v-bind('statusDetailColorMap.ERROR.background');
  color: v-bind('statusDetailColorMap.ERROR.color');
}

.asset-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.asset-name {
  font-weight: 500;
}

.asset-ip {
  font-size: 13px;
  color: var(--text-secondary);
}

.no-asset {
  font-size: 14px;
  color: var(--text-secondary);
  font-style: italic;
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