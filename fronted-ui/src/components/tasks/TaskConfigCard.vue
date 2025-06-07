<template>
  <div class="task-config-card mac-card">
    <div class="tabs">
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'mark' }" 
        @click="activeTab = 'mark'"
      >
        打标配置
      </button>
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'training' }" 
        @click="activeTab = 'training'"
      >
        训练参数
      </button>
    </div>
    
    <!-- 打标配置 -->
    <div v-if="activeTab === 'mark'" class="config-section">
      <div class="card-header">
        <h3>打标配置</h3>
        <div class="toggle-switch-container">
          <span class="toggle-switch-label">使用全局配置</span>
          <div class="toggle-switch">
            <input 
              type="checkbox" 
              id="use_global_mark_config" 
              v-model="localConfig.useGlobalMarkConfig"
              :disabled="!canEdit"
            >
            <label for="use_global_mark_config"></label>
          </div>
        </div>
      </div>
      
      <!-- 触发词配置，不受全局配置开关影响，始终显示 -->
      <div class="form-group full-width trigger-words-section">
        <label>触发词</label>
        <textarea
          v-model="localConfig.markConfig.trigger_words"
          placeholder="输入触发词，用逗号分隔"
          rows="3"
          class="mac-textarea"
        ></textarea>
      </div>
      
      <div v-if="localConfig.useGlobalMarkConfig" class="global-config-message">
        使用系统全局打标配置
      </div>
      <div v-else class="marking-config">
        <div class="config-form">
          <!-- 打标配置表单内容 -->
          <div class="form-row">
            <div class="form-group">
              <label>自动裁剪图片</label>
              <div class="switch-wrapper">
                <input 
                  type="checkbox" 
                  id="auto_crop" 
                  v-model="localConfig.markConfig.auto_crop"
                  class="toggle-checkbox"
                  :disabled="!canEdit"
                />
                <label for="auto_crop" class="toggle-label"></label>
              </div>
            </div>
            <div class="form-group">
              <label>默认裁剪比例</label>
              <select 
                v-model="localConfig.markConfig.default_crop_ratio" 
                class="mac-input"
                :disabled="!canEdit"
              >
                <option v-for="ratio in localConfig.markConfig.crop_ratios" :key="ratio" :value="ratio">{{ ratio }}</option>
              </select>
            </div>
          </div>
          
            <div class="form-group">
              <label>自动标签最小置信度</label>
              <input 
                type="range" 
                v-model.number="localConfig.markConfig.min_confidence" 
                min="0" 
                max="1" 
                step="0.01" 
                class="mac-slider"
                :disabled="!canEdit"
              />
              <div class="slider-value">{{ localConfig.markConfig.min_confidence }}</div>
            </div>
            <div class="form-group">
              <label>最大标签数量</label>
              <input 
                type="number" 
                v-model.number="localConfig.markConfig.max_tags" 
                min="1" 
                max="100" 
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
        </div>
      </div>
    </div>
    
    <!-- 训练参数 -->
    <div v-if="activeTab === 'training'" class="config-section">
      <div class="card-header">
        <h3>训练参数</h3>
        <div class="toggle-switch-container">
          <span class="toggle-switch-label">使用全局配置</span>
          <div class="toggle-switch">
            <input 
              type="checkbox" 
              id="use_global_training_config" 
              v-model="localConfig.useGlobalTrainingConfig"
              :disabled="!canEdit"
            >
            <label for="use_global_training_config"></label>
          </div>
        </div>
      </div>
      
      <div v-if="localConfig.useGlobalTrainingConfig" class="global-config-message">
        使用系统全局训练参数配置
      </div>
      <div v-else class="training-config">
        <div class="config-form">
          <!-- 基础训练参数 -->
          <div class="form-row">
            <div class="form-group">
              <label>最大训练轮次</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.max_train_epochs" 
                min="1"
                placeholder="10"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>批量大小</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.train_batch_size" 
                min="1"
                placeholder="1"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>网络维度 (Dim)</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.network_dim" 
                min="1"
                placeholder="64"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>网络Alpha值</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.network_alpha" 
                min="1"
                placeholder="32"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>基础学习率</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.learning_rate" 
                step="0.0001"
                min="0"
                placeholder="0.0001"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>分辨率</label>
              <input 
                v-model="localConfig.trainingConfig.resolution" 
                placeholder="512,512"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
            <div class="form-group">
              <label>Unet学习率</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.unet_lr" 
                step="0.0001"
                min="0"
                placeholder="0.0005"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>文本编码器学习率</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.text_encoder_lr" 
                step="0.00001"
                min="0"
                placeholder="0.00001"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          
            <div class="form-group">
              <label>学习率调度器</label>
              <select 
                v-model="localConfig.trainingConfig.lr_scheduler" 
                class="mac-input"
                :disabled="!canEdit"
              >
                <option value="cosine_with_restarts">余弦退火(cosine_with_restarts)</option>
                <option value="constant">恒定(constant)</option>
                <option value="constant_with_warmup">预热恒定(constant_with_warmup)</option>
                <option value="cosine">余弦(cosine)</option>
                <option value="linear">线性(linear)</option>
                <option value="polynomial">多项式(polynomial)</option>
              </select>
            </div>
            <div class="form-group">
              <label>优化器类型</label>
              <select 
                v-model="localConfig.trainingConfig.optimizer_type" 
                class="mac-input"
                :disabled="!canEdit"
              >
                <option value="AdamW8bit">AdamW8bit (推荐)</option>
                <option value="AdamW">AdamW</option>
                <option value="Lion">Lion</option>
                <option value="SGDNesterov">SGDNesterov</option>
                <option value="SGDNesterov8bit">SGDNesterov8bit</option>
              </select>
            </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>预热步数</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.lr_warmup_steps" 
                min="0"
                placeholder="0"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>学习率循环次数</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.lr_scheduler_num_cycles" 
                min="1"
                placeholder="1"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>每N轮保存一次</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.save_every_n_epochs" 
                min="1"
                placeholder="1"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>每N轮采样一次</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.sample_every_n_epochs" 
                min="1"
                placeholder="1"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>CLIP跳过层数</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.clip_skip" 
                min="1"
                max="12"
                placeholder="1"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
            <div class="form-group">
              <label>随机种子</label>
              <input 
                type="number" 
                v-model.number="localConfig.trainingConfig.seed" 
                placeholder="42"
                class="mac-input"
                :disabled="!canEdit"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>混合精度</label>
              <select 
                v-model="localConfig.trainingConfig.mixed_precision" 
                class="mac-input"
                :disabled="!canEdit"
              >
                <option value="bf16">bf16 (推荐)</option>
                <option value="no">不使用(no)</option>
                <option value="fp16">fp16</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, defineProps, defineEmits } from 'vue';
import deepEqual from '@/utils/object';

// 训练参数默认值
const defaultTrainingConfig = {
  max_train_epochs: 10,
  train_batch_size: 1,
  network_dim: 64,
  network_alpha: 32,
  learning_rate: 0.0001,
  unet_lr: 0.0005,
  text_encoder_lr: 0.00001,
  resolution: '512,512',
  lr_scheduler: 'cosine_with_restarts',
  lr_warmup_steps: 0,
  lr_scheduler_num_cycles: 1,
  save_every_n_epochs: 1,
  sample_every_n_epochs: 1,
  clip_skip: 1,
  seed: 42,
  mixed_precision: 'bf16',
  optimizer_type: 'AdamW8bit'
};

// 打标配置默认值
const defaultMarkConfig = {
  auto_crop: true,
  crop_ratios: ['1:1', '3:2', '4:3', '2:3', '16:9', '9:16'],
  default_crop_ratio: '1:1',
  min_confidence: 0.6,
  max_tags: 20,
  trigger_words: ''
};

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  canEdit: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:task']);

// 激活的选项卡
const activeTab = ref('mark');

// 创建一个包含所有配置的本地对象
const localConfig = ref({
  useGlobalMarkConfig: props.task.use_global_mark_config !== false,
  useGlobalTrainingConfig: props.task.use_global_training_config !== false,
  markConfig: structuredClone({...defaultMarkConfig, ...props.task.mark_config || {}}),
  trainingConfig: structuredClone({...defaultTrainingConfig, ...props.task.training_config || {}})
});

// 监听外部任务变化
watch(() => props.task, (newTask) => {
  // 使用structuredClone避免引用问题
  const updatedConfig = structuredClone(localConfig.value);
  let hasChanged = false;
  
  // 检查全局配置是否有变化
  if (updatedConfig.useGlobalMarkConfig !== (newTask.use_global_mark_config !== false)) {
    updatedConfig.useGlobalMarkConfig = newTask.use_global_mark_config !== false;
    hasChanged = true;
  }
  
  if (updatedConfig.useGlobalTrainingConfig !== (newTask.use_global_training_config !== false)) {
    updatedConfig.useGlobalTrainingConfig = newTask.use_global_training_config !== false;
    hasChanged = true;
  }
  
  // 只在真正有变化时更新本地配置
  if (!deepEqual(newTask.mark_config, updatedConfig.markConfig)) {
    updatedConfig.markConfig = {...defaultMarkConfig, ...newTask.mark_config || {}};
    hasChanged = true;
  }
  
  if (!deepEqual(newTask.training_config, updatedConfig.trainingConfig)) {
    updatedConfig.trainingConfig = {...defaultTrainingConfig, ...newTask.training_config || {}};
    hasChanged = true;
  }
  
  // 只有在配置确实发生变化时才更新
  if (hasChanged) {
    localConfig.value = updatedConfig;
  }
}, { deep: true });

// 使用一个函数来处理配置更改并同步到父组件
const syncConfigChanges = () => {
  console.log("syncConfigChanges",localConfig.value)
  const updatedTask = { ...props.task };
  let hasChanged = false;
  
  // 检查全局配置是否有变化
  if (updatedTask.use_global_mark_config !== localConfig.value.useGlobalMarkConfig) {
    updatedTask.use_global_mark_config = localConfig.value.useGlobalMarkConfig;
    hasChanged = true;
  }
  
  if (updatedTask.use_global_training_config !== localConfig.value.useGlobalTrainingConfig) {
    updatedTask.use_global_training_config = localConfig.value.useGlobalTrainingConfig;
    hasChanged = true;
  }

  // 仅当不使用全局配置且配置有变化时才同步具体配置
  if (!localConfig.value.useGlobalMarkConfig) {
    if (!deepEqual(updatedTask.mark_config, localConfig.value.markConfig)) {
      updatedTask.mark_config = structuredClone(localConfig.value.markConfig);
      hasChanged = true;
    }
  }
  
  if (!localConfig.value.useGlobalTrainingConfig) {
    if (!deepEqual(updatedTask.training_config, localConfig.value.trainingConfig)) {
      updatedTask.training_config = structuredClone(localConfig.value.trainingConfig);
      hasChanged = true;
    }
  }
  
  // 只有在配置确实发生变化时才发送更新
  if (hasChanged) {
    emit('update:task', updatedTask);
  }
};

// 监听本地配置变化，使用深度监听，但避免直接在watch中触发emit
watch(localConfig, () => {
  syncConfigChanges();
}, { deep: true });

</script>

<style scoped>
.tabs {
  display: flex;
  border-bottom: 1px solid #E5E7EB;
  margin-bottom: 16px;
}

.tab-button {
  padding: 0px 16px 16px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #6B7280;
  position: relative;
  transition: all 0.2s;
}

.tab-button.active {
  color: #007AFF;
  font-weight: 500;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #007AFF;
}

.tab-button:hover:not(.active) {
  color: #374151;
  background-color: rgba(0, 0, 0, 0.02);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 16px;
  margin: 0;
}

.toggle-switch-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-switch-label {
  font-size: 14px;
  color: #6B7280;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  height: 0;
  width: 0;
  visibility: hidden;
  position: absolute;
}

.toggle-switch label {
  cursor: pointer;
  width: 48px;
  height: 24px;
  background: #E5E7EB;
  display: block;
  border-radius: 24px;
  position: relative;
  transition: 0.3s;
}

.toggle-switch label:after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-switch input:checked + label {
  background: #007AFF;
}

.toggle-switch input:checked + label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.toggle-switch input:disabled + label {
  opacity: 0.5;
  cursor: not-allowed;
}

.global-config-message {
  padding: 24px;
  text-align: center;
  background-color: #F9FAFB;
  border-radius: 8px;
  color: #6B7280;
  font-style: italic;
}

.config-section {
  padding: 0 0 16px 0;
}

.marking-config,
.training-config {
  width: 100%;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  width: 100%;
  min-width: 100%;
}

.form-group label {
  font-size: 14px;
  color: var(--text-secondary, #6B7280);
}

.mac-input {
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  transition: all 0.2s ease;
}

.mac-input:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-input:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

.mac-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
}

.mac-textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-slider {
  width: 100%;
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  outline: none;
  -webkit-appearance: none;
}

.mac-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007AFF;
  cursor: pointer;
}

.slider-value {
  font-size: 14px;
  color: #6B7280;
  text-align: center;
  margin-top: 4px;
}

.switch-wrapper {
  position: relative;
  display: inline-block;
}

.toggle-checkbox {
  height: 0;
  width: 0;
  visibility: hidden;
  position: absolute;
}

.toggle-label {
  cursor: pointer;
  width: 48px;
  height: 24px;
  background: #E5E7EB;
  display: block;
  border-radius: 24px;
  position: relative;
}

.toggle-label:after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-checkbox:checked + .toggle-label {
  background: #007AFF;
}

.toggle-checkbox:checked + .toggle-label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.trigger-words-section {
  margin-top: 8px;
  margin-bottom: 16px;
  padding: 0 16px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
  
  .form-group {
    width: 100%;
  }
}
</style> 