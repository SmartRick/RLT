<template>
  <div class="training-details">
    <div class="details-header">
      <h3 class="details-title">训练详情 - {{ taskName }}</h3>
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
        <h4 class="section-title">训练Loss曲线</h4>
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
            />
            <div v-else class="no-preview-large">
              <div class="empty-icon">🖼️</div>
              <div class="empty-text">{{ selectedModel ? '无预览图' : '请选择模型查看预览' }}</div>
            </div>
          </div>
          
          <div v-if="selectedModel" class="selected-model-info">
            <div class="model-name" :title="selectedModel.name">{{ selectedModel.name }}</div>
            <div class="model-meta">
              <span class="model-size">{{ formatFileSize(selectedModel.size) }}</span>
              <span class="model-date">{{ formatDate(selectedModel.modified_time) }}</span>
            </div>
            <button class="download-btn" @click="downloadModel(selectedModel)">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="download-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              下载模型
            </button>
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
          <div v-else class="models-thumbnails">
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
  }
})

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

// 计算属性
const hasLossData = computed(() => lossData.value && lossData.value.length > 0)

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
      
      // 更新图表
      if (lossData.value.length > 0) {
        updateChart()
      }
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
  if (!chartContainer.value) {
    console.warn('Chart container not found')
    return
  }
  
  try {
    // 销毁可能存在的旧图表实例
    if (chart.value) {
      chart.value.dispose()
    }
    
    // 创建新图表实例
    chart.value = echarts.init(chartContainer.value)
    
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
    window.addEventListener('resize', handleResize)
  } catch (error) {
    console.error('初始化图表失败:', error)
  }
}

// 更新图表数据
const updateChart = () => {
  if (!chart.value) {
    console.warn('Chart instance not available when updating data')
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
  
  const downloadUrl = tasksApi.getModelDownloadUrl(props.taskId, model.path)
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

// 组件挂载时
onMounted(async () => {
  // 先获取数据
  await Promise.all([
    fetchTrainingResults(),
    fetchTrainingLoss()
  ])
  
  // 使用nextTick确保DOM已渲染
  nextTick(() => {
    // 首先尝试通过ref获取DOM元素
    if (chartContainer.value) {
      initChart()
    } else {
      // 如果ref获取失败，尝试通过ID获取
      console.warn('Chart container ref not available, trying by ID')
      const container = document.getElementById('training-loss-chart')
      if (container) {
        // 手动设置ref值
        chartContainer.value = container
        initChart()
      } else {
        // 如果仍然失败，延迟尝试
        console.warn('Chart container not found by ID, trying with delay')
        setTimeout(() => {
          const delayedContainer = document.getElementById('training-loss-chart')
          if (delayedContainer) {
            chartContainer.value = delayedContainer
            initChart()
          } else {
            console.error('Failed to initialize chart: container not found')
          }
        }, 500)
      }
    }
  })
  
  // 如果是训练中状态，启动自动刷新
  if (props.isTraining) {
    startAutoRefresh()
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
})
</script>

<style scoped>
.training-details {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
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
}

.details-content {
  flex: 1;
  display: flex;
  gap: 24px;
  overflow: hidden;
  min-height: 600px;
}

/* 左侧Loss曲线区域 */
.loss-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 确保flex项可以收缩 */
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 500px;
  height: 500px; /* 添加明确的高度 */
  width: 100%; /* 确保宽度为100% */
  background-color: var(--background-secondary);
  border-radius: 8px;
}

/* 右侧模型区域 */
.models-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0; /* 确保flex项可以收缩 */
}

.model-preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.model-large-preview {
  height: 300px;
  background-color: var(--background-tertiary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.large-preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.selected-model-info {
  margin-top: 16px;
  padding: 16px;
  background-color: var(--background-secondary);
  border-radius: 8px;
}

.models-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.models-thumbnails {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px;
  padding-bottom: 12px;
}

.model-thumbnail {
  flex: 0 0 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: var(--background-secondary);
}

.model-thumbnail.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.model-thumbnail:hover {
  transform: translateY(-2px);
}

.thumbnail-preview {
  height: 100px;
  background-color: var(--background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
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

.model-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  word-break: break-all;
}

.model-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.download-btn {
  width: 100%;
  padding: 8px;
  border: none;
  background-color: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background-color 0.2s;
}

.download-btn:hover {
  background-color: var(--primary-color-dark);
}

.download-icon {
  width: 16px;
  height: 16px;
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