<template>
  <div class="tasks-view">
    <div class="filters">
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索任务..."
          @input="filterTasks"
        >
      </div>
      <div class="filter-group">
        <div class="date-range">
          <input 
            type="datetime-local" 
            v-model="dateRange.start"
            @change="filterTasks"
            placeholder="开始时间"
          >
          <span>至</span>
          <input 
            type="datetime-local" 
            v-model="dateRange.end"
            @change="filterTasks"
            placeholder="结束时间"
          >
        </div>
        <select 
          v-model="statusFilter"
          @change="filterTasks"
        >
          <option value="">全部状态</option>
          <option 
            v-for="status in statusOptions" 
            :key="status"
            :value="status"
          >
            {{ status }}
          </option>
        </select>
      </div>
    </div>

    <div class="tasks-list">
      <TaskCard 
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        @retry="retryTask"
        @cancel="cancelTask"
        @view-log="viewTaskLog"
      />
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>

    <div 
      v-if="!loading && filteredTasks.length === 0" 
      class="no-tasks"
    >
      没有找到匹配的任务
    </div>
  </div>
</template>

<script>
/* eslint-disable vue/multi-word-component-names */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import TaskCard from '@/components/tasks/TaskCard.vue'
import { trainingApi } from '@/api/training'

export default {
  name: 'TasksView',
  components: {
    TaskCard
  },
  setup() {
    const tasks = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const statusFilter = ref('')
    const dateRange = ref({
      start: '',
      end: ''
    })

    const statusOptions = [
      'DOWNLOADING',
      'PENDING',
      'TRAINING',
      'COMPLETED',
      'FAILED'
    ]

    const loadTasks = async () => {
      loading.value = true
      try {
        const response = await trainingApi.listTasks()
        tasks.value = response.data
      } catch (error) {
        console.error('加载任务失败:', error)
      } finally {
        loading.value = false
      }
    }

    const isInDateRange = (date) => {
      if (!dateRange.value.start && !dateRange.value.end) return true
      const taskDate = new Date(date)
      if (dateRange.value.start && taskDate < new Date(dateRange.value.start)) {
        return false
      }
      if (dateRange.value.end && taskDate > new Date(dateRange.value.end)) {
        return false
      }
      return true
    }

    const filterTasks = () => {
      filteredTasks.value = tasks.value.filter(item => {
        const matchesSearch = item.folder_name.toLowerCase()
          .includes(searchQuery.value.toLowerCase())
        const matchesStatus = !statusFilter.value || 
          item.status === statusFilter.value
        const matchesDate = isInDateRange(item.created_at)
        return matchesSearch && matchesStatus && matchesDate
      })
    }

    const filteredTasks = computed(() => {
      return tasks.value.filter(item => {
        const matchesSearch = item.folder_name.toLowerCase()
          .includes(searchQuery.value.toLowerCase())
        const matchesStatus = !statusFilter.value || 
          item.status === statusFilter.value
        const matchesDate = isInDateRange(item.created_at)
        return matchesSearch && matchesStatus && matchesDate
      })
    })

    let pollingInterval = null

    onMounted(() => {
      loadTasks()
      pollingInterval = setInterval(loadTasks, 5000)
    })

    onUnmounted(() => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    })

    const retryTask = async (task) => {
      try {
        await trainingApi.retryTask(task.id)
        await loadTasks()
      } catch (error) {
        console.error('重试任务失败:', error)
      }
    }

    const cancelTask = async (task) => {
      if (!confirm(`确定要取消任务 "${task.folder_name}" 吗？`)) {
        return
      }

      try {
        await trainingApi.cancelTask(task.id)
        await loadTasks()
      } catch (error) {
        console.error('取消任务失败:', error)
      }
    }

    const viewTaskLog = (task) => {
      // TODO: 实现查看任务日志的功能
    }

    return {
      tasks,
      loading,
      searchQuery,
      statusFilter,
      dateRange,
      statusOptions,
      filteredTasks,
      retryTask,
      cancelTask,
      viewTaskLog,
      filterTasks
    }
  }
}
</script>

<style lang="scss" scoped>
.tasks-view {
  position: relative;
  min-height: 200px;
}

.filters {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;

  .search-box {
    flex: 1;
    min-width: 200px;
  }

  .filter-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  input, select {
    padding: 8px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    background: var(--input-background);
    color: var(--text-color);
  }
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-tasks {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

@media (prefers-color-scheme: dark) {
  .loading-overlay {
    background: rgba(0, 0, 0, 0.8);
  }
}
</style> 