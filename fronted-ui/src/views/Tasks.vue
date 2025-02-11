<template>
  <div class="tasks-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-section">
        <!-- 搜索框 -->
        <div class="search-box">
          <MagnifyingGlassIcon class="search-icon" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索任务..." 
            class="mac-search-input"
            @input="handleSearch"
          >
        </div>
        
        <!-- 过滤器组 -->
        <div class="filter-group">
          <select 
            v-model="statusFilter" 
            class="mac-select"
            @change="handleFilterChange"
          >
            <option value="">全部状态</option>
            <option value="NEW">新建</option>
            <option value="MARKING">标记中</option>
            <option value="MARKED">已标记</option>
            <option value="TRAINING">训练中</option>
            <option value="COMPLETED">已完成</option>
            <option value="ERROR">错误</option>
          </select>

          <select 
            v-model="dateFilter" 
            class="mac-select"
            @change="handleFilterChange"
          >
            <option value="">全部时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
          </select>
        </div>
      </div>

      <!-- 右侧操作 -->
      <div class="right-section">
        <button 
          class="mac-btn primary"
          @click="showCreateTask"
        >
          <PlusIcon class="btn-icon" />
          新建任务
        </button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="tasks-grid">
      <TaskCard
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        @click="openTaskDetail(task)"
        @delete="handleDeleteTask"
      />
    </div>

    <!-- 新建任务模态框 -->
    <BaseModal
      v-model="showTaskModal"
      title="新建训练任务"
      :loading="isSubmitting"
      @close="closeTaskModal"
      @confirm="handleConfirm"
    >
      <template #body>
        <TaskForm
          ref="taskFormRef"
          :loading="isSubmitting"
        />
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { MagnifyingGlassIcon, PlusIcon } from '@heroicons/vue/24/outline'
import TaskCard from '@/components/tasks/TaskCard.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import BaseModal from '@/components/common/Modal.vue'
import { tasksApi } from '@/api/tasks'
import message from '@/utils/message'

// 状态
const tasks = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const dateFilter = ref('')
const showTaskModal = ref(false)
const isSubmitting = ref(false)

const router = useRouter()

const taskFormRef = ref(null)

// 获取任务列表
const fetchTasks = async () => {
  try {
    const data = await tasksApi.getTasks({
      status: statusFilter.value,
      search: searchQuery.value,
      date: dateFilter.value
    })
    tasks.value = data
  } catch (error) {
    message.error('获取任务列表失败')
  }
}

// 过滤后的任务列表
const filteredTasks = computed(() => {
  return tasks.value
})

// 显示新建任务模态框
const showCreateTask = () => {
  showTaskModal.value = true
}

// 关闭模态框
const closeTaskModal = () => {
  showTaskModal.value = false
}

// 处理模态框确认
const handleConfirm = async () => {
  if (!taskFormRef.value) return
  
  // 调用表单的提交方法，并传递处理函数
  const formData = await taskFormRef.value.submit()
  if (formData) {
    handleCreateTask(formData)
  }
}

// 创建任务
const handleCreateTask = async (formData) => {
  try {
    isSubmitting.value = true
    const task = await tasksApi.createTask(formData)
    message.success('任务创建成功')
    closeTaskModal()
    router.push(`/tasks/${task.id}`)
  } catch (error) {
    message.error('创建任务失败')
  } finally {
    isSubmitting.value = false
  }
}

// 打开任务详情
const openTaskDetail = (task) => {
  router.push(`/tasks/${task.id}`)
}

// 删除任务
const handleDeleteTask = async (taskId) => {
  try {
    await tasksApi.deleteTask(taskId)
    message.success('任务已删除')
    fetchTasks() // 刷新列表
  } catch (error) {
    message.error('删除任务失败')
  }
}

// 初始化
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.tasks-container {
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
  padding: 16px;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.search-box {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.mac-search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 36px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--background-secondary);
  transition: all 0.3s ease;
}

.mac-search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  background: var(--background-primary);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.1);
}

.filter-group {
  display: flex;
  gap: 12px;
}

.mac-select {
  height: 36px;
  padding: 0 32px 0 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--background-secondary);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
}

.mac-select:focus {
  outline: none;
  border-color: var(--primary-color);
  background-color: var(--background-primary);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.1);
}

.right-section {
  display: flex;
  gap: 12px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.tasks-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 4px;
  overflow-y: auto;
}

/* 滚动条样式 */
.tasks-grid::-webkit-scrollbar {
  width: 8px;
}

.tasks-grid::-webkit-scrollbar-track {
  background: transparent;
}

.tasks-grid::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.tasks-grid::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}
</style> 