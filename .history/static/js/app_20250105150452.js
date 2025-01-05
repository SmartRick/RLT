new Vue({
    el: '#app',
    data: {
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
    },
    computed: {
        filteredTasks() {
            return this.tasks.filter(task => {
                const matchesSearch = task.folder_name.toLowerCase()
                    .includes(this.searchQuery.toLowerCase());
                const matchesStatus = !this.statusFilter || 
                    task.status === this.statusFilter;
                return matchesSearch && matchesStatus;
            });
        }
    },
    methods: {
        fetchTasks() {
            axios.get('/api/tasks')
                .then(response => {
                    if (response.data.success) {
                        this.tasks = response.data.data;
                    }
                })
                .catch(error => console.error('获取任务列表失败:', error));
        },
        fetchStats() {
            axios.get('/api/stats')
                .then(response => {
                    if (response.data.success) {
                        this.stats = response.data.data;
                    }
                })
                .catch(error => console.error('获取统计信息失败:', error));
        },
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleString();
        },
        filterTasks() {
            // 搜索和筛选逻辑已通过计算属性实现
        },
        startPolling() {
            setInterval(() => {
                this.fetchTasks();
                this.fetchStats();
            }, 5000); // 每5秒更新一次
        }
    },
    mounted() {
        this.fetchTasks();
        this.fetchStats();
        this.startPolling();
    }
}); 