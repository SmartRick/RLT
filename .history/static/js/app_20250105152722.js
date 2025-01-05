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
        dateRange: {
            start: '',
            end: ''
        },
        showConfig: false,
        configJson: '',
        configError: '',
        configChanged: false,
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
        ],
        configForm: {
            source_dir: '',
            lora_output_path: '',
            scheduling_minute: 2,
            url: 'http://127.0.0.1:28000',
            mark_pan_dir: '/loraFile/mark',
            lora_pan_upload_dir: '/loraFile/lora'
        },
        showLogs: false,
        logFiles: [],
        currentLog: null,
        logContent: [],
        logLines: "100",
        logAutoRefresh: false,
        logRefreshInterval: null,
        logRefreshRate: 5000, // 5秒刷新一次
    },
    computed: {
        filteredTasks() {
            return this.tasks.filter(task => {
                const matchesSearch = task.folder_name.toLowerCase()
                    .includes(this.searchQuery.toLowerCase());
                const matchesStatus = !this.statusFilter || 
                    task.status === this.statusFilter;
                let matchesDate = true;
                if (this.dateRange.start || this.dateRange.end) {
                    const taskDate = new Date(task.created_at);
                    if (this.dateRange.start) {
                        matchesDate = matchesDate && taskDate >= new Date(this.dateRange.start);
                    }
                    if (this.dateRange.end) {
                        matchesDate = matchesDate && taskDate <= new Date(this.dateRange.end);
                    }
                }
                return matchesSearch && matchesStatus && matchesDate;
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
        },
        async loadConfig() {
            try {
                const response = await axios.get('/api/config');
                if (response.data.success) {
                    const config = response.data.data;
                    this.configForm = {
                        source_dir: config.source_dir || '',
                        lora_output_path: config.lora_output_path || '',
                        scheduling_minute: config.scheduling_minute || 2,
                        url: config.url || 'http://127.0.0.1:28000',
                        mark_pan_dir: config.mark_pan_dir || '/loraFile/mark',
                        lora_pan_upload_dir: config.lora_pan_upload_dir || '/loraFile/lora'
                    };
                    this.configChanged = false;
                    this.configError = '';
                }
            } catch (error) {
                console.error('加载配置失败:', error);
                this.configError = '加载配置失败';
            }
        },
        async saveConfig() {
            try {
                const config = {
                    source_dir: this.configForm.source_dir,
                    lora_output_path: this.configForm.lora_output_path,
                    scheduling_minute: parseInt(this.configForm.scheduling_minute),
                    url: this.configForm.url,
                    mark_pan_dir: this.configForm.mark_pan_dir,
                    lora_pan_upload_dir: this.configForm.lora_pan_upload_dir
                };
                
                const response = await axios.post('/api/config', config);
                if (response.data.success) {
                    this.configError = '';
                    this.configChanged = false;
                    this.showConfig = false;
                    alert('配置已保存');
                }
            } catch (error) {
                console.error('保存配置失败:', error);
                this.configError = error.message || '保存配置失败';
            }
        },
        onConfigChange() {
            this.configChanged = true;
        },
        toggleConfig() {
            this.showConfig = !this.showConfig;
            if (this.showConfig) {
                this.loadConfig();  // 每次打开时重新加载配置
            }
        },
        async loadLogFiles() {
            try {
                const response = await axios.get('/api/logs');
                if (response.data.success) {
                    this.logFiles = response.data.data;
                }
            } catch (error) {
                console.error('获取日志列表失败:', error);
            }
        },
        async loadLogContent() {
            if (!this.currentLog) return;
            
            try {
                const response = await axios.get(`/api/logs/${this.currentLog}`, {
                    params: { lines: this.logLines }
                });
                if (response.data.success) {
                    const wasScrolledToBottom = this.isScrolledToBottom();
                    this.logContent = response.data.data.content;
                    
                    // 如果之前在底部，更新后保持在底部
                    if (wasScrolledToBottom) {
                        this.$nextTick(() => {
                            this.scrollToBottom();
                        });
                    }
                }
            } catch (error) {
                console.error('读取日志内容失败:', error);
            }
        },
        selectLog(filename) {
            this.currentLog = filename;
            this.loadLogContent();
            if (this.logAutoRefresh) {
                this.startLogRefresh();
            }
        },
        toggleLogs() {
            this.showLogs = !this.showLogs;
            if (this.showLogs) {
                this.loadLogFiles();
            } else {
                this.stopLogRefresh();
                this.logAutoRefresh = false;
            }
        },
        formatFileSize(bytes) {
            const units = ['B', 'KB', 'MB', 'GB'];
            let size = bytes;
            let unitIndex = 0;
            
            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }
            
            return `${size.toFixed(1)} ${units[unitIndex]}`;
        },
        toggleAutoRefresh() {
            this.logAutoRefresh = !this.logAutoRefresh;
            if (this.logAutoRefresh) {
                this.startLogRefresh();
            } else {
                this.stopLogRefresh();
            }
        },
        startLogRefresh() {
            this.loadLogContent(); // 立即刷新一次
            this.logRefreshInterval = setInterval(() => {
                this.loadLogContent();
            }, this.logRefreshRate);
        },
        stopLogRefresh() {
            if (this.logRefreshInterval) {
                clearInterval(this.logRefreshInterval);
                this.logRefreshInterval = null;
            }
        },
        isScrolledToBottom() {
            const viewer = this.$refs.logViewer;
            if (!viewer) return false;
            return Math.abs(viewer.scrollHeight - viewer.scrollTop - viewer.clientHeight) < 1;
        },
        scrollToBottom() {
            const viewer = this.$refs.logViewer;
            if (viewer) {
                viewer.scrollTop = viewer.scrollHeight;
            }
        }
    },
    mounted() {
        this.fetchTasks();
        this.fetchStats();
        this.startPolling();
    }
}); 