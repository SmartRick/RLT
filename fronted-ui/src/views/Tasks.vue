<template>
  <div class="tasks-page">
    <div class="tasks-container">
      <!-- 使用TaskList组件 -->
      <TaskList
        ref="taskListRef"
        :selectedTaskId="selectedTaskId"
        @select="handleTaskSelect"
        @create="showTaskModal = true"
        @update:tasks="allTasks = $event"
      />
      
      <!-- 任务详情区域 -->
      <div class="task-detail-container" v-if="selectedTaskId">
        <router-view />
      </div>
      
      <!-- 无选中任务时的空状态 -->
      <div class="empty-state" v-else>
        <div class="empty-content">
          <DocumentIcon class="empty-icon" />
          <h3>请选择任务</h3>
          <p>在左侧列表中选择一个任务查看详情，或创建新任务</p>
          <button class="mac-btn primary" @click="showTaskModal = true">
            <PlusIcon class="btn-icon" />
            新建任务
          </button>
        </div>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <BaseModal
      v-model="showTaskModal"
      title="新建训练任务"
      :loading="isCreating"
      @confirm="handleCreateTask"
    >
      <template #body>
        <div class="form-group">
          <label for="taskName">任务名称</label>
          <input
            id="taskName"
            v-model="newTask.name"
            type="text"
            placeholder="输入任务名称"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="taskDescription">任务描述 (可选)</label>
          <textarea
            id="taskDescription"
            v-model="newTask.description"
            placeholder="输入任务描述"
            class="form-textarea"
            rows="3"
          ></textarea>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  DocumentIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import BaseModal from '@/components/common/Modal.vue'
import TaskList from '@/components/tasks/TaskList.vue'
import message from '@/utils/message'

const route = useRoute()
const router = useRouter()

// 状态
const allTasks = ref([])
const taskListRef = ref(null)
const showTaskModal = ref(false)
const isCreating = ref(false)
const newTask = ref({
  name: '',
  description: ''
})

// 当前选中的任务ID（从路由参数获取）
const selectedTaskId = computed(() => route.params.id || '')

// 处理任务选择
const handleTaskSelect = (task) => {
  if (task) {
    // 导航到任务详情页
    router.push(`/tasks/${task.id}`)
  } else if (allTasks.value.length > 0) {
    // 如果没有选中任务但列表不为空，则默认选择第一个
    router.push(`/tasks/${allTasks.value[0].id}`)
  } else {
    // 列表为空时，导航到任务列表页
    router.push('/tasks')
  }
}

// 创建新任务
const handleCreateTask = async () => {
  if (!newTask.value.name) {
    message.warning('请输入任务名称')
    return
  }

  try {
    isCreating.value = true
    const task = await tasksApi.createTask(newTask.value)
    message.success('任务创建成功')
    
    // 重置表单
    newTask.value = { name: '', description: '' }
    showTaskModal.value = false
    
    // 刷新任务列表
    if (taskListRef.value) {
      await taskListRef.value.fetchTasks()
    }
    
    // 导航到新创建的任务详情页
    router.push(`/tasks/${task.id}`)
  } catch (error) {
    message.error('创建任务失败')
  } finally {
    isCreating.value = false
  }
}

// 在组件挂载后，如果没有选择任务且列表不为空，则选择第一个任务
onMounted(async () => {
  // 如果当前没有选中任务，且路由是/tasks
  if (!selectedTaskId.value && route.path === '/tasks') {
    // 等待任务列表加载完成
    await nextTick()
    
    // 如果有任务，选择第一个
    if (allTasks.value.length > 0) {
      handleTaskSelect(allTasks.value[0])
    }
  }
})

// 监听任务列表变化，在必要时自动选择任务
watch(allTasks, (tasks) => {
  // 如果有任务但没有选中任何任务，则选择第一个
  if (tasks.length > 0 && !selectedTaskId.value && route.path === '/tasks') {
    handleTaskSelect(tasks[0])
  }
}, { deep: true })
</script>

<style scoped>
.tasks-page {
  height: 100%;
  padding: 20px;
}

.tasks-container {
  display: flex;
  height: 100%;
  gap: 20px;
}

.task-detail-container {
  flex: 1;
  overflow: auto;
  min-width: 0;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  min-width: 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  max-width: 400px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.empty-content h3 {
  font-size: 18px;
  margin: 0 0 8px 0;
}

.empty-content p {
  color: var(--text-secondary);
  margin: 0 0 24px 0;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--background-secondary);
  transition: all 0.3s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  background: var(--background-primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}
</style> 