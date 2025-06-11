<template>
  <BaseModal
    v-model="show"
    :title="`${asset?.name} - ${activeTab === 'terminal' ? '终端' : '文件管理'}`"
    width="80vw"
    @close="handleClose"
  >
    <template #body>
      <div class="terminal-tabs">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'terminal' }"
          @click="activeTab = 'terminal'"
        >
          <CommandLineIcon class="tab-icon" />
          <span>终端</span>
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'fileManager' }"
          @click="activeTab = 'fileManager'"
        >
          <FolderIcon class="tab-icon" />
          <span>文件管理</span>
        </div>
      </div>
      
      <div class="tab-content">
        <!-- 终端标签页内容 -->
        <div v-show="activeTab === 'terminal'" class="terminal-container">
          <Terminal 
            v-if="asset?.id" 
            :assetId="asset.id"
            ref="terminalComponent"
          />
        </div>
        
        <!-- 文件管理标签页内容 -->
        <div v-show="activeTab === 'fileManager'" class="file-manager-container">
          <FileManager :asset="asset" v-if="asset" />
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import BaseModal from '@/components/common/Modal.vue'
import FileManager from '@/components/terminal/FileManager.vue'
import Terminal from '@/components/terminal/Terminal.vue'
import { CommandLineIcon, FolderIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: Boolean,
  asset: Object
})

const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 标签页状态
const activeTab = ref('terminal')
const terminalComponent = ref(null)

// 监听显示状态变化
watch(show, (newVal) => {
  if (!newVal) {
    // 当关闭窗口时，清理终端
    if (terminalComponent.value) {
      terminalComponent.value.cleanupTerminal()
    }
  }
})

const handleClose = () => {
  // 清理终端连接
  if (terminalComponent.value) {
    terminalComponent.value.cleanupTerminal()
  }
  show.value = false
}
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 580px;
  overflow: hidden;
  position: relative;
}

.terminal-tabs {
  display: flex;
  background: #f3f4f6;
  border-radius: 6px 6px 0 0;
  border-bottom: 1px solid #e5e7eb;
  overflow: hidden;
}

.tab-item {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #e5e7eb;
}

.tab-item:hover {
  background: #e5e7eb;
}

.tab-item.active {
  background: #fff;
  border-bottom: 2px solid #3b82f6;
  font-weight: 500;
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.tab-content {
  background: #fff;
  border-radius: 0 0 6px 6px;
}

.file-manager-container {
  height: 580px;
  overflow: auto;
  padding: 0;
  border-radius: 0 0 6px 6px;
}
</style> 