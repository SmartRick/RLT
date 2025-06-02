<template>
  <div class="task-list-sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">任务列表</h2>
      <button 
        class="new-task-btn"
        @click="$emit('create')"
        title="新建任务"
      >
        <PlusIcon class="icon" />
      </button>
    </div>
    
    <!-- 搜索和过滤区域 -->
    <div class="search-filter-area">
      <div class="search-box">
        <MagnifyingGlassIcon class="search-icon" />
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="搜索任务..." 
          class="search-input"
          @input="handleSearch"
        >
      </div>
      
      <div class="filter-row">
        <select 
          v-model="statusFilter" 
          class="filter-select"
          @change="handleFilterChange"
        >
          <option value="">全部状态</option>
          <option value="NEW">新建</option>
          <option value="SUBMITTED">已提交</option>
          <option value="MARKING">标记中</option>
          <option value="MARKED">已标记</option>
          <option value="TRAINING">训练中</option>
          <option value="COMPLETED">已完成</option>
          <option value="ERROR">错误</option>
        </select>

        <select 
          v-model="dateFilter" 
          class="filter-select"
          @change="handleFilterChange"
        >
          <option value="">全部时间</option>
          <option value="today">今天</option>
          <option value="week">本周</option>
          <option value="month">本月</option>
        </select>
      </div>
    </div>
    
    <div class="task-count">共 {{ tasks.length }} 个任务</div>
    
    <!-- 任务列表 -->
    <div class="task-list">
      <div 
        v-for="task in tasks" 
        :key="task.id"
        class="task-list-item"
        :class="{ 'selected': selectedTaskId == task.id }"
        @click="selectTask(task)"
      >
        <div class="task-icon">
          <component :is="getStatusIcon(task.status)" class="status-icon" />
        </div>
        <div class="task-item-content">
          <div class="task-name text-ellipsis">{{ task.name }}</div>
          <div class="task-meta">
            <span class="task-status" :class="getStatusClass(task.status)">
              {{ getStatusText(task.status) }}
            </span>
            <span class="task-date">{{ formatDate(task.created_at) }}</span>
          </div>
        </div>
        <button 
          v-if="canDeleteTask(task)"
          class="delete-btn"
          @click.stop="confirmDelete(task)"
          title="删除任务"
        >
          <TrashIcon class="delete-icon" />
        </button>
      </div>
      
      <!-- 无任务时显示提示 -->
      <div v-if="tasks.length === 0" class="empty-list">
        <p>暂无任务</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  MagnifyingGlassIcon, 
  PlusIcon,
  DocumentIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  TagIcon,
  XCircleIcon,
  TrashIcon,
  ArrowUpCircleIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import { formatDate } from '@/utils/datetime'
import message from '@/utils/message'
import { 
  getStatusText as getStatusTextUtil, 
  getStatusClass as getStatusClassUtil, 
  canDeleteTask as canDelete,
  statusDetailColorMap
} from '@/utils/taskStatus'

const route = useRoute()

const props = defineProps({
  selectedTaskId: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select', 'create', 'update:tasks'])

// 状态
const tasks = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const dateFilter = ref('')
// 判断当前是否在任务相关页面
const isTasksRoute = computed(() => {
  return route.path === '/tasks' || route.path.startsWith('/tasks/')
})
// 获取任务列表
const fetchTasks = async () => {
  // 只有在任务相关路由下才获取任务列表
  if (!isTasksRoute.value) return
  try {
    const data = await tasksApi.getTasks({
      status: statusFilter.value,
      search: searchQuery.value,
      date: dateFilter.value
    })
    
    tasks.value = data
    emit('update:tasks', data)
    
    // 如果有任务但没有选中的任务，默认选择第一个
    if (tasks.value.length > 0 && !props.selectedTaskId && isTasksRoute.value) {
      selectTask(tasks.value[0])
    }
  } catch (error) {
    message.error('获取任务列表失败')
  }
}

// 处理搜索和过滤
const handleSearch = () => {
  fetchTasks()
}

const handleFilterChange = () => {
  fetchTasks()
}

// 选择任务
const selectTask = (task) => {
  // 只有在任务相关页面才触发选择事件
  if (isTasksRoute.value) {
    emit('select', task)
  }
}

// 删除任务
const handleDeleteTask = async (taskId) => {
  try {
    await tasksApi.deleteTask(taskId)
    message.success('任务已删除')
    fetchTasks() // 刷新列表
    
    // 如果当前正在查看被删除的任务，发送null通知父组件
    if (props.selectedTaskId === taskId) {
      emit('select', null)
    }
  } catch (error) {
    message.error('删除任务失败')
  }
}

// 获取状态图标
const getStatusIcon = (status) => {
  const iconMap = {
    'NEW': DocumentIcon,
    'SUBMITTED': ArrowUpCircleIcon,
    'MARKING': TagIcon,
    'MARKED': CheckCircleIcon,
    'TRAINING': ArrowPathIcon,
    'COMPLETED': CheckCircleIcon,
    'ERROR': XCircleIcon
  }
  return iconMap[status] || ExclamationCircleIcon
}

// 使用统一的状态文本方法
const getStatusText = (status) => {
  return getStatusTextUtil(status)
}

// 使用统一的状态样式类方法
const getStatusClass = (status) => {
  return getStatusClassUtil(status)
}

// 判断任务是否可以删除
const canDeleteTask = (task) => {
  return canDelete(task)
}

// 确认删除任务
const confirmDelete = (task) => {
  if (confirm(`确定要删除任务 "${task.name}" 吗？`)) {
    handleDeleteTask(task.id)
  }
}

// 监听selectedTaskId变化
watch(() => props.selectedTaskId, (newId) => {
  // 如果selectedTaskId被清空且有任务，则选择第一个
  if (!newId && tasks.value.length > 0 && isTasksRoute.value) {
    selectTask(tasks.value[0])
  }
})

// 监听路由变化
watch(() => route.path, (newPath) => {
  // 如果进入任务页面，则获取任务列表
  if (newPath === '/tasks' || newPath.startsWith('/tasks/')) {
    fetchTasks()
  }
}, { immediate: true })

// 暴露方法给父组件
defineExpose({
  fetchTasks
})
</script>

<style scoped>
/* 左侧任务列表侧边栏 */
.task-list-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.new-task-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--primary-color);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.new-task-btn:hover {
  background: color-mix(in srgb, var(--primary-color) 80%, white);
}

.new-task-btn .icon {
  width: 18px;
  height: 18px;
}

.search-filter-area {
  padding: 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.search-box {
  position: relative;
  margin-bottom: 8px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  height: 32px;
  padding: 0 10px 0 30px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--background-secondary);
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  background: var(--background-primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.1);
}

.filter-row {
  display: flex;
  gap: 8px;
}

.filter-select {
  flex: 1;
  height: 30px;
  padding: 0 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  background: var(--background-secondary);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
  background-size: 12px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.task-count {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color-light);
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.task-list-item:hover {
  background: var(--background-secondary);
}

.task-list-item.selected {
  background: color-mix(in srgb, var(--primary-color) 15%, transparent);
  border-left: 3px solid var(--primary-color);
  padding-left: 9px; /* 补偿边框宽度 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.task-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--background-secondary);
}

.status-icon {
  width: 16px;
  height: 16px;
}

.task-item-content {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 3px;
}

.task-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}

.task-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.task-status.new {
  background-color: v-bind('statusDetailColorMap.NEW.background');
  color: v-bind('statusDetailColorMap.NEW.color');
}

.task-status.submitted {
  background-color: v-bind('statusDetailColorMap.SUBMITTED.background');
  color: v-bind('statusDetailColorMap.SUBMITTED.color');
}

.task-status.marking {
  background-color: v-bind('statusDetailColorMap.MARKING.background');
  color: v-bind('statusDetailColorMap.MARKING.color');
}

.task-status.marked {
  background-color: v-bind('statusDetailColorMap.MARKED.background');
  color: v-bind('statusDetailColorMap.MARKED.color');
}

.task-status.training {
  background-color: v-bind('statusDetailColorMap.TRAINING.background');
  color: v-bind('statusDetailColorMap.TRAINING.color');
}

.task-status.completed {
  background-color: v-bind('statusDetailColorMap.COMPLETED.background');
  color: v-bind('statusDetailColorMap.COMPLETED.color');
}

.task-status.error {
  background-color: v-bind('statusDetailColorMap.ERROR.background');
  color: v-bind('statusDetailColorMap.ERROR.color');
}

.task-date {
  color: var(--text-tertiary);
}

.empty-list {
  display: flex;
  justify-content: center;
  padding: 30px 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #EF4444;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: #FEE2E2;
  color: #DC2626;
  opacity: 1;
}

.delete-icon {
  width: 16px;
  height: 16px;
}

/* 滚动条样式 */
.task-list::-webkit-scrollbar {
  width: 6px;
}

.task-list::-webkit-scrollbar-track {
  background: transparent;
}

.task-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 