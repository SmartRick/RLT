<template>
  <div class="dashboard">
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

    <section class="recent-tasks">
      <h2>最近任务</h2>
      <div class="task-list">
        <div 
          v-for="task in recentTasks" 
          :key="task.id" 
          class="task-item"
        >
          <TaskCard :task="task" />
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import TaskCard from '@/components/tasks/TaskCard.vue'
import { trainingApi } from '@/api/training'

export default {
  name: 'DashboardView',
  components: {
    TaskCard
  },
  setup() {
    const stats = ref({
      total: 0,
      downloading: 0,
      pending: 0,
      training: 0,
      pending_upload: 0,
      uploading: 0,
      completed: 0,
      failed: {
        download: 0,
        training: 0,
        upload: 0
      }
    })
    const recentTasks = ref([])
    let pollingInterval = null

    const loadData = async () => {
      try {
        const [statsResponse, tasksResponse] = await Promise.all([
          trainingApi.getStats(),
          trainingApi.listTasks({ limit: 5 })
        ])
        stats.value = statsResponse.data
        recentTasks.value = tasksResponse.data
      } catch (error) {
        console.error('加载数据失败:', error)
      }
    }

    onMounted(() => {
      loadData()
      pollingInterval = setInterval(loadData, 5000)
    })

    onUnmounted(() => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    })

    return {
      stats,
      recentTasks
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 20px;

  .stats {
    margin-bottom: 30px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-top: 20px;
  }

  .stat-item {
    background: var(--card-background);
    padding: 20px;
    border-radius: var(--border-radius);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h3 {
      margin: 0 0 10px 0;
      color: var(--text-secondary);
      font-size: 1em;
    }

    p {
      margin: 0;
      font-size: 1.5em;
      font-weight: 500;
    }

    &.error {
      border-left: 4px solid var(--error-color);

      .failed-stats {
        p {
          font-size: 1em;
          margin: 5px 0;
        }
      }
    }
  }

  .recent-tasks {
    h2 {
      margin-bottom: 20px;
    }

    .task-list {
      display: grid;
      gap: 15px;
    }
  }
}
</style> 