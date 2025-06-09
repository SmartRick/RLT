<template>
  <div class="training-details">
    <div class="details-header">
      <h3 class="details-title">任务 - {{ taskName }}</h3>
      <div class="header-info" v-if="trainingProgress">
        <div class="progress-info">
          <span class="progress-label">训练进度:</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${trainingProgress.progress_percent}%` }"></div>
          </div>
          <span class="progress-text">{{ trainingProgress.progress_percent }}%</span>
        </div>
        <div class="step-info">
          <span>步数: {{ trainingProgress.current_step }}/{{ trainingProgress.total_steps }}</span>
          <span>轮数: {{ trainingProgress.max_epochs }}</span>
        </div>
      </div>
    </div>

    <div class="details-content">
      <!-- 左侧Loss曲线区域 -->
      <div class="loss-section">
        <h4 class="section-title">
          训练Loss曲线
          <span v-if="lastStepLoss" class="loss-value">(当前Loss: {{ lastStepLoss }})</span>
        </h4>
        <div class="chart-container" ref="chartContainer" id="training-loss-chart">
          <div v-if="isLoadingLoss" class="loading-placeholder">加载中...</div>
          <div v-else-if="!hasLossData" class="empty-placeholder">
            <div class="empty-icon">📊</div>
            <div class="empty-text">暂无训练数据</div>
            <div class="empty-desc" v-if="isTraining">训练进行中，数据将在训练过程中更新</div>
          </div>
        </div>
      </div>

      <!-- 右侧模型预览和列表 -->
      <div class="models-section">
        <!-- 大图预览区域 -->
        <div class="model-preview-area">
          <h4 class="section-title">模型预览</h4>
          <div class="model-large-preview">
            <img 
              v-if="selectedModel && selectedModel.preview_image" 
              :src="selectedModel.preview_image" 
              alt="模型预览" 
              class="large-preview-image"
              @click="openImagePreview(selectedModel.preview_image)"
            />
            <div v-else class="no-preview-large">
              <div class="empty-icon">🖼️</div>
              <div class="empty-text">{{ selectedModel ? '无预览图' : '请选择模型查看预览' }}</div>
            </div>
            
            <div v-if="selectedModel" class="selected-model-info">
              <div class="model-info-left">
                <div class="model-name" :title="selectedModel.name">{{ selectedModel.name }}</div>
                <div class="model-meta">
                  <span class="model-size">{{ formatFileSize(selectedModel.size) }}</span>
                  <span class="model-date">{{ formatDate(selectedModel.modified_time) }}</span>
                </div>
              </div>
              <button class="download-btn" @click="downloadModel(selectedModel)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="download-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
                下载
              </button>
            </div>
          </div>
        </div>

        <!-- 模型列表 -->
        <div class="models-list-container">
          <h4 class="section-title">训练模型 ({{ models.length }})</h4>
          <div v-if="isLoadingModels" class="loading-placeholder">加载中...</div>
          <div v-else-if="models.length === 0" class="empty-placeholder">
            <div class="empty-icon">📦</div>
            <div class="empty-text">暂无训练模型</div>
            <div class="empty-desc" v-if="isTraining">训练进行中，模型将在训练过程中保存</div>
          </div>
          <div v-else class="models-thumbnails" ref="thumbnailsContainer">
            <div 
              v-for="(model, index) in models" 
              :key="index" 
              class="model-thumbnail" 
              :class="{ active: selectedModel && selectedModel.path === model.path }"
              @click="selectModel(model)"
            >
              <div class="thumbnail-preview">
                <img 
                  v-if="model.preview_image" 
                  :src="model.preview_image" 
                  alt="模型缩略图"
                />
                <div v-else class="no-preview-thumbnail">无预览</div>
              </div>
              <div class="thumbnail-name" :title="model.name">{{ model.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { tasksApi } from '@/api/tasks'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  TitleComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  CanvasRenderer
])

const props = defineProps({
  taskId: {
    type: [Number, String],
    required: true
  },
  taskName: {
    type: String,
    default: ''
  },
  isTraining: {
    type: Boolean,
    default: false
  },
  refreshInterval: {
    type: Number,
    default: 10000 // 默认10秒刷新一次
  },
  task: {
    type: Object,
    default: () => ({})
  }
})

// 添加自定义事件
const emit = defineEmits(['preview-image', 'model-images-change'])

// 状态变量
const chartContainer = ref(null)
const chart = ref(null)
const models = ref([])
const lossData = ref([])
const trainingProgress = ref(null)
const isLoadingModels = ref(false)
const isLoadingLoss = ref(false)
const refreshTimer = ref(null)
const selectedModel = ref(null)

// 处理缩略图列表的横向滚动
const thumbnailsContainer = ref(null)

// 计算属性
const hasLossData = computed(() => lossData.value && lossData.value.length > 0)
const lastStepLoss = computed(() => {
  if (lossData.value && lossData.value.length > 0) {
    const lastLoss = lossData.value[lossData.value.length - 1]
    return lastLoss.value.toFixed(4)
  }
  return null
})

// 计算模型的所有预览图片数组
const modelPreviewImages = computed(() => {
  return models.value
    .filter(model => model.preview_image)
    .map(model => model.preview_image)
})

// 获取训练结果
const fetchTrainingResults = async () => {
  if (!props.taskId) return
  
  try {
    isLoadingModels.value = true
    const data = await tasksApi.getTrainingResults(props.taskId)
    if (data && data.models) {
      models.value = data.models
      
      // 如果没有选中模型，默认选择第一个有预览图的模型
      if (!selectedModel.value && models.value.length > 0) {
        const modelWithPreview = models.value.find(model => model.preview_image) || models.value[0]
        selectedModel.value = modelWithPreview
      }
    }
  } catch (error) {
    console.error('获取训练结果失败:', error)
  } finally {
    isLoadingModels.value = false
  }
}

// 获取训练Loss数据
const fetchTrainingLoss = async () => {
  if (!props.taskId) return
  
  try {
    isLoadingLoss.value = true
    const data = await tasksApi.getTrainingLoss(props.taskId)
    if (data && data.series) {
      lossData.value = data.series
      trainingProgress.value = data.training_progress
      
      // 确保DOM已渲染后再初始化或更新图表
      nextTick(() => {
          updateChart()
      })
    }
  } catch (error) {
    console.error('获取训练Loss数据失败:', error)
  } finally {
    isLoadingLoss.value = false
  }
}

// 选择模型
const selectModel = (model) => {
  selectedModel.value = model
}

// 初始化图表
const initChart = () => {
  try {
    // 销毁可能存在的旧图表实例
    if (chart.value) {
      chart.value.dispose()
    }
    // 创建新图表实例
    chart.value = echarts.init(chartContainer.value, null, {
      renderer: 'canvas',
      useDirtyRect: true,
      // 添加passive选项解决事件监听器警告
      useCoarsePointer: true,
      pointerOptions: { passive: true }
    })
    
    // 设置图表选项
    const option = {
      title: {
        text: 'Training Loss',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal'
        }
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const dataPoint = params[0]
          return `步数: ${dataPoint.value[0]}<br/>Loss: ${dataPoint.value[1].toFixed(4)}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '步数',
        nameLocation: 'middle',
        nameGap: 30
      },
      yAxis: {
        type: 'value',
        name: 'Loss',
        nameLocation: 'middle',
        nameGap: 40
      },
      series: [
        {
          name: 'Loss',
          type: 'line',
          smooth: true,
          symbol: 'none',
          sampling: 'average',
          itemStyle: {
            color: '#5470c6'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: 'rgba(84, 112, 198, 0.5)'
              },
              {
                offset: 1,
                color: 'rgba(84, 112, 198, 0.1)'
              }
            ])
          },
          data: []
        }
      ]
    }
    
    chart.value.setOption(option)
    
    // 添加窗口大小变化时的自适应
    window.addEventListener('resize', handleResize, { passive: true })
    
    return true
  } catch (error) {
    console.error('初始化图表失败:', error)
    return false
  }
}

// 更新图表数据
const updateChart = () => {
  if (!chart.value) {
    // 如果图表实例不存在，尝试初始化
    nextTick(() => {
      if (chartContainer.value) {
        initChart()
      }
    })
    return
  }
  
  if (!lossData.value || lossData.value.length === 0) {
    console.warn('No loss data to update chart')
    return
  }
  
  try {
    // 转换数据格式
    const seriesData = lossData.value.map(item => [item.step, item.value])
    
    chart.value.setOption({
      series: [
        {
          data: seriesData
        }
      ]
    })
  } catch (error) {
    console.error('更新图表数据失败:', error)
  }
}

// 窗口大小变化时调整图表大小
const handleResize = () => {
  if (!chart.value) {
    return
  }
  
  try {
    chart.value.resize()
  } catch (error) {
    console.error('调整图表大小失败:', error)
  }
}

// 下载模型
const downloadModel = (model) => {
  if (!model || !model.path) return
  
  const downloadUrl = model.path
  window.open(downloadUrl, '_blank')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  
  return `${bytes.toFixed(2)} ${units[i]}`
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 启动自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先停止可能存在的定时器
  
  if (props.isTraining) {
    refreshTimer.value = setInterval(() => {
      fetchTrainingLoss()
      fetchTrainingResults()
    }, props.refreshInterval)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 监听训练状态变化
watch(() => props.isTraining, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

// 监听taskId变化
watch(() => props.taskId, () => {
  fetchTrainingResults()
  fetchTrainingLoss()
})

// 监听鼠标滚轮事件实现横向滚动
const handleThumbnailsScroll = (event) => {
  if (!thumbnailsContainer.value) return
  
  // 阻止默认的垂直滚动
  event.preventDefault()
  
  // 根据滚轮方向确定滚动方向和距离
  const scrollAmount = event.deltaY || event.deltaX
  thumbnailsContainer.value.scrollLeft += scrollAmount
}

// 修改图片预览方法，发送事件到父组件
const openImagePreview = (imageUrl) => {
  if (!imageUrl) return
  // 触发父组件的预览事件
  emit('preview-image', imageUrl)
}

// 添加对modelPreviewImages变化的监听，向父组件发送更新
watch(modelPreviewImages, (images) => {
  emit('model-images-change', images)
}, { immediate: true })

// 组件挂载时
onMounted(async () => {
  // 先获取数据
  await Promise.all([
    fetchTrainingResults(),
    fetchTrainingLoss()
  ])
  
  // 使用nextTick确保DOM已渲染
  nextTick(() => {
    // 如果已有数据，初始化图表并绘制
    if (initChart() && lossData.value && lossData.value.length > 0) {
      updateChart()
    }
  })
  
  // 如果是训练中状态，启动自动刷新
  if (props.isTraining) {
    startAutoRefresh()
  }
  
  // 添加滚轮事件监听
  if (thumbnailsContainer.value) {
    thumbnailsContainer.value.addEventListener('wheel', handleThumbnailsScroll, { passive: false })
  }
})

// 组件卸载时
onUnmounted(() => {
  stopAutoRefresh()
  
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)
  
  // 销毁图表实例
  if (chart.value) {
    try {
      chart.value.dispose()
    } catch (error) {
      console.error('销毁图表实例失败:', error)
    }
    chart.value = null
  }
  
  // 移除滚轮事件监听
  if (thumbnailsContainer.value) {
    thumbnailsContainer.value.removeEventListener('wheel', handleThumbnailsScroll)
  }
})
</script>

<style scoped>
.training-details {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 添加overflow: hidden防止内容溢出 */
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.details-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  width: 150px;
  height: 8px;
  background-color: var(--background-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
}

.step-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
  max-height: calc(100% - 60px); /* 减去标题区域的高度 */
}

.details-content {
  flex: 1;
  display: flex;
  gap: 24px;
  overflow: hidden;
  min-height: 0; /* 修改min-height为0，允许内容区域收缩 */
}

/* 左侧Loss曲线区域 */
.loss-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 0; 
  background-color: var(--background-secondary);
  border-radius: 8px;
}

/* 右侧模型区域 */
.models-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
  overflow: hidden;
}

.model-preview-area {
  flex: 0 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden; 
  position: relative;
}

.model-large-preview {
  height: 400px;
  background-color: var(--background-tertiary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.large-preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: pointer;
}

.selected-model-info {
  position: absolute; 
  bottom: 0; 
  left: 0;
  right: 0;
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.6); 
  backdrop-filter: blur(8px); 
  border-radius: 0 0 8px 8px; 
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 1;
}

.model-info-left {
  flex: 1;
  overflow: hidden;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: white;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.download-btn {
  width: auto; /* 改为自适应宽度 */
  padding: 6px 12px;
  border: none;
  background-color: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background-color 0.2s;
  flex-shrink: 0; /* 防止按钮被压缩 */
}

.download-btn:hover {
  background-color: var(--primary-color-dark);
}

.download-icon {
  width: 16px;
  height: 16px;
}

.models-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 添加overflow: hidden */
}

.models-thumbnails {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px;
  padding-bottom: 12px;
  flex-wrap: nowrap;
}

.model-thumbnail {
  flex: 0 0 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: var(--background-secondary);
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  max-height: 150px; /* 添加最大高度限制 */
}

.model-thumbnail.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.model-thumbnail:hover {
  transform: translateY(-2px);
}

.thumbnail-preview {
  height: 150px;
  background-color: var(--background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex: 1;
}

.thumbnail-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-name {
  padding: 8px;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-secondary);
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 16px 0;
}

.section-title .loss-value {
  font-size: 14px;
  font-weight: normal;
  color: var(--text-secondary);
  margin-left: 8px;
}

.no-preview-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  color: var(--text-secondary);
}

.no-preview-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 12px;
  color: var(--text-secondary);
}

.loading-placeholder,
.empty-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--background-secondary);
  border-radius: 8px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .details-content {
    flex-direction: column;
  }
  
  .loss-section,
  .models-section {
    width: 100%;
  }
  
  .chart-container {
    min-height: 300px;
  }
}
</style> 