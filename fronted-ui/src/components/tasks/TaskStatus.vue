<template>
  <div class="task-status">
    <!-- 任务阶段进度条 -->
    <div class="task-phases" ref="phasesContainer" @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag">
      <div 
        v-for="(state, index) in taskStates" 
        :key="state.status"
        ref="phaseItems"
        class="phase-item"
        :class="{
          'active': isStateActive(state.status),
          'completed': isStateCompleted(state.status),
          'error': isStateError(state.status)
        }"
      >
        <div class="phase-icon">
          <component 
            :is="getPhaseIcon(state.status)" 
            class="icon"
          />
        </div>
        <div class="phase-info">
          <div class="phase-name">{{ state.label }}</div>
          <div class="phase-time" v-if="getStateTime(state.status)">
            {{ getStateTime(state.status) }}
          </div>
        </div>
        <div v-if="index < taskStates.length - 1" class="phase-connector" />
      </div>
    </div>

    <!-- 当前任务状态 -->
    <div v-if="isTaskActive" class="current-progress">
      <div class="progress-header">
        <div class="progress-title">
          <ClockIcon class="progress-icon" />
          <span>当前进度</span>
        </div>
        <div class="progress-time">{{ getRunningTime() }}</div>
      </div>
      <div class="progress-bar">
        <div 
          class="progress-value" 
          :style="{ width: `${task.progress}%` }"
        />
      </div>
      <div class="progress-text">{{ task.progress }}%</div>
    </div>

    <!-- 错误信息面板 -->
    <div v-if="task?.status === 'ERROR'" class="error-section">
      <div class="error-header">
        <ExclamationTriangleIcon class="error-icon"/>
        <span>错误信息</span>
      </div>
      <div class="error-content">
        <pre v-if="errorDetails">{{ errorDetails }}</pre>
        <div v-else class="error-message">{{ task.error_message }}</div>
      </div>
    </div>

    <!-- 任务状态日志 -->
    <div v-for="(status, statusKey) in task.status_history" :key="statusKey" class="status-record">
      <div class="status-header">
        <div class="status-badge" :class="getStatusClass(statusKey)">
          {{ getStatusText(statusKey) }}
        </div>
        <div class="status-time">
          <span>{{ formatDate(status.start_time) }}</span>
          <span v-if="status.end_time">- {{ formatDate(status.end_time) }}</span>
        </div>
      </div>
      <div class="status-logs">
        <div v-for="(log, index) in status.logs" :key="index" class="log-item">
          <div class="log-time">{{ formatTime(log.time) }}</div>
          <div class="log-message">{{ log.message }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { 
  CheckCircleIcon, 
  ClockIcon, 
  XCircleIcon,
  CircleIcon,
  ExclamationTriangleIcon,
  FlagIcon,
  DocumentIcon,
  ArrowPathIcon,
  TagIcon,
  CommandLineIcon
} from '@heroicons/vue/24/outline'
import { formatDateTime, formatDuration, formatDate, formatTime } from '@/utils/datetime'

// // 状态文本映射
// const statusTextMap = {
//   'NEW': '新建',
//   'SUBMITTED': '已提交',
//   'MARKING': '标记中',
//   'MARKED': '已标记',
//   'TRAINING': '训练中',
//   'COMPLETED': '已完成',
//   'ERROR': '错误'
// }

const props = defineProps({
  task: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 定义任务状态流程
const taskStates = [
  { status: 'NEW', label: '新建' },
  { status: 'SUBMITTED', label: '已提交' },
  { status: 'MARKING', label: '标记中' },
  { status: 'MARKED', label: '已标记' },
  { status: 'TRAINING', label: '训练中' },
  { status: 'COMPLETED', label: '已完成' }
]

// 状态判断方法
const isStateActive = (status) => props.task?.status === status
const isStateCompleted = (status) => {
  if (!props.task?.status) return false
  const stateIndex = taskStates.findIndex(s => s.status === status)
  const currentIndex = taskStates.findIndex(s => s.status === props.task.status)
  return currentIndex > stateIndex && props.task.status !== 'ERROR'
}
const isStateError = (status) => {
  if (!props.task?.status) return false
  return props.task.status === 'ERROR' && status === props.task.status
}

// 获取状态时间和消息
const getStateTime = (status) => {
  const stateHistory = props.task?.status_history?.find(h => h.status === status)
  return stateHistory ? formatDateTime(stateHistory.timestamp) : null
}



// 解析错误详情
const errorDetails = computed(() => {
  try {
    if (props.task?.error_message) {
      const error = JSON.parse(props.task.error_message)
      return JSON.stringify(error, null, 2)
    }
    return null
  } catch {
    return null
  }
})

// 计算任务是否处于活动状态
const isTaskActive = computed(() => {
  if (!props.task?.status) return false
  return ['MARKING', 'TRAINING'].includes(props.task.status)
})

// 计算运行时长
const runningTime = ref('')
let timer = null

const updateRunningTime = () => {
  if (props.task?.started_at && isTaskActive.value) {
    const start = new Date(props.task.started_at)
    const duration = Date.now() - start.getTime()
    runningTime.value = formatDuration(duration)
  }
}

const getRunningTime = () => runningTime.value

const phasesContainer = ref(null)
const phaseItems = ref([])
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)

// 开始拖动
const startDrag = (e) => {
  isDragging.value = true
  const container = phasesContainer.value
  startX.value = e.pageX - container.offsetLeft
  scrollLeft.value = container.scrollLeft
  container.style.cursor = 'grabbing'
  // 防止文本选择
  e.preventDefault()
}

// 拖动中
const onDrag = (e) => {
  if (!isDragging.value) return
  
  const container = phasesContainer.value
  const x = e.pageX - container.offsetLeft
  const walk = (x - startX.value) * 1.5 // 增加滚动速度
  container.scrollLeft = scrollLeft.value - walk
}

// 停止拖动
const stopDrag = () => {
  if (!isDragging.value) return
  
  isDragging.value = false
  const container = phasesContainer.value
  container.style.cursor = 'grab'
}

// 滚动到当前活动状态
const scrollToActivePhase = async () => {
  await nextTick()
  if (!phasesContainer.value) return
  
  const activeIndex = taskStates.findIndex(s => isStateActive(s.status))
  if (activeIndex === -1) return
  
  const activeElement = phaseItems.value[activeIndex]
  if (!activeElement) return
  
  const container = phasesContainer.value
  const scrollLeft = activeElement.offsetLeft - (container.clientWidth / 2) + (activeElement.clientWidth / 2)
  
  container.scrollTo({
    left: Math.max(0, scrollLeft),
    behavior: 'smooth'
  })
}

// 启动定时器
onMounted(() => {
  if (isTaskActive.value) {
    updateRunningTime()
    timer = setInterval(updateRunningTime, 1000)
  }
  scrollToActivePhase()
})

// 监听任务状态变化
watch(() => props.task?.status, () => {
  scrollToActivePhase()
})

// 清理定时器
onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})

// 获取阶段图标
const getPhaseIcon = (status) => {
  if (isStateCompleted(status)) return CheckCircleIcon
  if (isStateActive(status)) return ClockIcon
  if (isStateError(status)) return XCircleIcon
  
  // 为每个状态设置特定图标
  const iconMap = {
    'NEW': DocumentIcon,
    'SUBMITTED': ArrowPathIcon,
    'MARKING': TagIcon,
    'MARKED': CheckCircleIcon,
    'TRAINING': CommandLineIcon,
    'COMPLETED': FlagIcon
  }
  
  return iconMap[status] || CircleIcon
}

// 获取状态文本和类
const getStatusText = (status) => {
  // 状态文本映射
  const statusTextMap = {
    'NEW': '新建',
    'SUBMITTED': '已提交',
    'MARKING': '标记中',
    'MARKED': '已标记',
    'TRAINING': '训练中',
    'COMPLETED': '已完成',
    'ERROR': '错误'
  }
  return statusTextMap[status] || status
}

const getStatusClass = (status) => {
  // 状态类映射
  const statusClassMap = {
    'NEW': 'status-new',
    'SUBMITTED': 'status-submitted',
    'MARKING': 'status-marking',
    'MARKED': 'status-marked',
    'TRAINING': 'status-training',
    'COMPLETED': 'status-completed',
    'ERROR': 'status-error'
  }
  return statusClassMap[status] || 'status-unknown'
}
</script>

<style scoped>
.task-status {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-height: 100%;
  overflow: hidden;
}

/* 任务阶段样式 */
.task-phases {
  display: flex;
  align-items: flex-start;
  padding: var(--spacing-4);
  background: var(--background-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color-light);
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  /* 隐藏滚动条但保持功能 */
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
  cursor: grab;
  user-select: none; /* 防止文本选择 */
}

/* 隐藏 Webkit 滚动条 */
.task-phases::-webkit-scrollbar {
  display: none;
}

.phase-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 auto;
  min-width: 120px;
  gap: var(--spacing-2);
  padding: 0 var(--spacing-2);
}

.phase-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-color);
  transition: all var(--transition-speed);
  position: relative;
  z-index: 1;
}

.phase-icon svg {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
}

.phase-item.completed .phase-icon {
  background: var(--success-color);
  border-color: var(--success-color);
}

.phase-item.completed .phase-icon svg {
  color: white;
}

.phase-item.active .phase-icon {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.phase-item.active .phase-icon svg {
  color: white;
}

.phase-item.error .phase-icon {
  background: var(--danger-color);
  border-color: var(--danger-color);
}

.phase-item.error .phase-icon svg {
  color: white;
}

.phase-info {
  text-align: center;
  min-width: 80px;
}

.phase-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.phase-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.phase-connector {
  position: absolute;
  top: 18px;
  right: -50%;
  width: 100%;
  height: 2px;
  background: var(--border-color-light);
}

.phase-item.completed .phase-connector {
  background: var(--success-color);
}

/* 添加悬停效果 */
.phase-item:hover .phase-icon {
  transform: scale(1.1);
  box-shadow: var(--shadow-sm);
}

/* 添加活动状态的动画 */
.phase-item.active .phase-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--primary-color) 40%, transparent);
  }
  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--primary-color) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--primary-color) 0%, transparent);
  }
}

/* 当前进度样式 */
.current-progress {
  padding: var(--spacing-4);
  background: var(--background-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color-light);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.progress-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-weight: 500;
}

.progress-icon {
  width: 18px;
  height: 18px;
  color: var(--primary-color);
}

.progress-time {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  height: 6px;
  background: var(--background-tertiary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: var(--spacing-2);
}

.progress-value {
  height: 100%;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width var(--transition-speed);
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: right;
}

/* 错误信息样式 */
.error-section {
  flex-shrink: 0;
  max-height: 300px;
  display: flex;
  flex-direction: column;
}

.error-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
  padding: 0 var(--spacing-2);
}

.error-icon {
  width: 18px;
  height: 18px;
  color: var(--danger-color);
}

.error-content {
  flex: 1;
  overflow: auto;
  background: color-mix(in srgb, var(--danger-color) 5%, white);
  border: 1px solid color-mix(in srgb, var(--danger-color) 20%, white);
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
}

.error-content pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-message {
  color: var(--danger-color);
  font-size: 14px;
  line-height: 1.5;
}

/* 拖动时的光标样式 */
.task-phases:active {
  cursor: grabbing;
}

.status-record {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-logs {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 2px solid var(--border-color-light);
}

.log-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.log-time {
  color: var(--text-tertiary);
  white-space: nowrap;
}

.log-message {
  color: var(--text-secondary);
}
</style> 