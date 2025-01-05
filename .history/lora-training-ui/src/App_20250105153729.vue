<template>
  <div id="app">
    <header>
      <h1>Lora 训练任务管理器</h1>
      <p class="subtitle">实时监控训练任务状态</p>
    </header>

    <section class="stats">
      <h2>任务统计</h2>
      <div class="stats-grid">
        <div class="stat-item">
          <h3>总任务数</h3>
          <p>{{ stats.total }}</p>
        </div>
        <div class="stat-item">
          <h3>下载中</h3>
          <p>{{ stats.downloading }}</p>
        </div>
        <div class="stat-item">
          <h3>等待训练</h3>
          <p>{{ stats.pending }}</p>
        </div>
        <div class="stat-item">
          <h3>训练中</h3>
          <p>{{ stats.training }}</p>
        </div>
        <div class="stat-item">
          <h3>等待上传</h3>
          <p>{{ stats.pending_upload }}</p>
        </div>
        <div class="stat-item">
          <h3>上传中</h3>
          <p>{{ stats.uploading }}</p>
        </div>
        <div class="stat-item">
          <h3>已完成</h3>
          <p>{{ stats.completed }}</p>
        </div>
        <div class="stat-item error">
          <h3>失败任务</h3>
          <div class="failed-stats">
            <p>下载: {{ stats.failed.download }}</p>
            <p>训练: {{ stats.failed.training }}</p>
            <p>上传: {{ stats.failed.upload }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="action-buttons">
      <button 
        class="action-btn"
        :class="{ active: showConfig }"
        @click="toggleConfig"
      >
        <span class="icon">⚙️</span>
        <span class="text">系统配置</span>
      </button>
      <button class="action-btn" disabled>
        <span class="icon">📊</span>
        <span class="text">数据分析</span>
      </button>
      <button 
        class="action-btn"
        :class="{ active: showLogs }"
        @click="toggleLogs"
      >
        <span class="icon">📝</span>
        <span class="text">日志查看</span>
      </button>
    </section>

    <section class="tasks">
      <div class="section-header">
        <h2>任务列表</h2>
        <div class="task-filters">
          <input 
            v-model="searchQuery" 
            placeholder="搜索任务..." 
            @input="filterTasks"
          >
          <div class="date-filters">
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
      <div class="task-list">
        <div 
          v-for="task in filteredTasks" 
          :key="task.folder_name" 
          :class="['task-item', task.status.toLowerCase()]"
        >
          <h3>{{ task.folder_name }}</h3>
          <div class="task-info">
            <p>
              <strong>状态:</strong>
              <span>{{ task.status }}</span>
            </p>
            <p>
              <strong>创建时间:</strong>
              <span>{{ formatDate(task.created_at) }}</span>
            </p>
            <p v-if="task.updated_at">
              <strong>更新时间:</strong>
              <span>{{ formatDate(task.updated_at) }}</span>
            </p>
            <p v-if="task.task_id">
              <strong>任务ID:</strong>
              <span>{{ task.task_id }}</span>
            </p>
            <p v-if="task.lora_path">
              <strong>Lora路径:</strong>
              <span>{{ task.lora_path }}</span>
            </p>
            <p v-if="task.error" class="error-message">
              <strong>错误信息:</strong>
              <span>{{ task.error }}</span>
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 配置模态框 -->
    <ConfigModal 
      v-if="showConfig"
      @close="toggleConfig"
    />

    <!-- 日志查看模态框 -->
    <div class="modal-overlay" v-if="showLogs" @click="toggleLogs"></div>
    <div class="modal logs-modal" v-if="showLogs">
      <!-- ... 日志查看模态框内容 ... -->
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ConfigModal from '@/components/ConfigModal.vue'

export default {
  name: 'App',
  components: {
    ConfigModal
  },
  data() {
    return {
      tasks: [],
      stats: {
        total: 0,
        downloading: 0,
        pending: 0,
        training: 0,
        training_completed: 0,
        pending_upload: 0,
        uploading: 0,
        completed: 0,
        failed: {
          download: 0,
          training: 0,
          upload: 0
        }
      },
      searchQuery: '',
      statusFilter: '',
      dateRange: {
        start: '',
        end: ''
      },
      showConfig: false,
      showLogs: false,
      statusOptions: [
        'DOWNLOADING',
        'PENDING',
        'TRAINING',
        'TRAINING_COMPLETED',
        'PENDING_UPLOAD',
        'UPLOADING',
        'COMPLETED',
        'DOWNLOAD_FAILED',
        'TRAINING_FAILED',
        'UPLOAD_FAILED'
      ]
    }
  },
  computed: {
    filteredTasks() {
      return this.tasks.filter(task => {
        const matchesSearch = task.folder_name.toLowerCase()
          .includes(this.searchQuery.toLowerCase())
        const matchesStatus = !this.statusFilter || 
          task.status === this.statusFilter
        let matchesDate = true
        if (this.dateRange.start || this.dateRange.end) {
          const taskDate = new Date(task.created_at)
          if (this.dateRange.start) {
            matchesDate = matchesDate && 
              taskDate >= new Date(this.dateRange.start)
          }
          if (this.dateRange.end) {
            matchesDate = matchesDate && 
              taskDate <= new Date(this.dateRange.end)
          }
        }
        return matchesSearch && matchesStatus && matchesDate
      })
    }
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await axios.get('/api/tasks')
        if (response.data.success) {
          this.tasks = response.data.data
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
      }
    },
    async fetchStats() {
      try {
        const response = await axios.get('/api/stats')
        if (response.data.success) {
          this.stats = response.data.data
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    },
    filterTasks() {
      // 通过计算属性自动处理
    },
    startPolling() {
      setInterval(() => {
        this.fetchTasks()
        this.fetchStats()
      }, 5000)
    },
    toggleConfig() {
      this.showConfig = !this.showConfig
    },
    toggleLogs() {
      this.showLogs = !this.showLogs
    }
  },
  mounted() {
    this.fetchTasks()
    this.fetchStats()
    this.startPolling()
  }
}
</script>

<style lang="scss">
@import '@/styles/main.scss';
</style>
