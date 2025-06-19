<template>
  <div class="task-config-card mac-card">
    <div class="tabs">
      <button class="tab-button" :class="{ active: activeTab === 'mark' }" @click="activeTab = 'mark'">
        打标配置
      </button>
      <button class="tab-button" :class="{ active: activeTab === 'training' }" @click="activeTab = 'training'">
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
            <input type="checkbox" id="use_global_mark_config" v-model="config.use_global_mark_config"
              :disabled="!canEdit">
            <label for="use_global_mark_config"></label>
          </div>
        </div>
      </div>

      <!-- 触发词配置，不受全局配置开关影响，始终显示 -->
      <div class="form-group full-width trigger-words-section">
        <label>
          <span class="label-text">触发词</span>
          <span class="label-en">trigger_words</span>
        </label>
        <textarea v-model="config.mark_config.trigger_words" placeholder="输入触发词，用逗号分隔" rows="3" class="mac-textarea"
          :disabled="!canEdit"></textarea>
      </div>

      <div v-if="config.use_global_mark_config" class="global-config-message">
        使用系统全局打标配置
      </div>
      <div v-else class="marking-config">
        <div class="config-form">
          <!-- 打标配置表单内容 -->
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">自动裁剪图片</span>
                <span class="label-en">auto_crop</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="auto_crop" v-model="config.mark_config.auto_crop" class="toggle-checkbox"
                  :disabled="!canEdit" />
                <label for="auto_crop" class="toggle-label"></label>
              </div>
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">默认裁剪比例</span>
                <span class="label-en">default_crop_ratio</span>
              </label>
              <select v-model="config.mark_config.default_crop_ratio" class="mac-input" :disabled="!canEdit">
                <option v-for="ratio in config.mark_config.crop_ratios" :key="ratio" :value="ratio">{{ ratio }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text">自动标签最小置信度</span>
              <span class="label-en">min_confidence</span>
            </label>
            <input type="range" v-model.number="config.mark_config.min_confidence" min="0" max="1" step="0.01"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.mark_config.min_confidence }}</div>
          </div>
          <div class="form-group">
            <label>
              <span class="label-text">最大标签数量</span>
              <span class="label-en">max_tags</span>
            </label>
            <input type="number" v-model.number="config.mark_config.max_tags" min="1" max="100" class="mac-input"
              :disabled="!canEdit" />
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
            <input type="checkbox" id="use_global_training_config" v-model="config.use_global_training_config"
              :disabled="!canEdit">
            <label for="use_global_training_config"></label>
          </div>
        </div>
      </div>

      <div v-if="config.use_global_training_config" class="global-config-message">
        使用系统全局训练参数配置
      </div>
      <div v-else class="training-config">
        <div class="config-form">
          <!-- 最重要的两个参数放在最前面 -->
          <div class="form-group">
            <label>
              <span class="label-text">最大训练轮次</span>
              <span class="label-en">max_train_epochs</span>
            </label>
            <input type="range" v-model.number="config.training_config.max_train_epochs" min="1" max="20" step="1"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.training_config.max_train_epochs }}</div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text">图片重复次数</span>
              <span class="label-en">repeat_num</span>
            </label>
            <input type="range" v-model.number="config.training_config.repeat_num" min="1" max="50" step="1"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.training_config.repeat_num }}</div>
          </div>

          <!-- 基础训练参数 -->
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">批量大小</span>
                <span class="label-en">train_batch_size</span>
              </label>
              <input type="number" v-model.number="config.training_config.train_batch_size" min="1" placeholder="1"
                class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">分辨率</span>
                <span class="label-en">resolution</span>
              </label>
              <input v-model="config.training_config.resolution" placeholder="512,512" class="mac-input"
                :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">网络维度 (Dim)</span>
                <span class="label-en">network_dim</span>
              </label>
              <input type="number" v-model.number="config.training_config.network_dim" min="1" placeholder="64"
                class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">网络Alpha值</span>
                <span class="label-en">network_alpha</span>
              </label>
              <input type="number" v-model.number="config.training_config.network_alpha" min="1" placeholder="32"
                class="mac-input" :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">基础学习率</span>
                <span class="label-en">learning_rate</span>
              </label>
              <input type="number" v-model.number="config.training_config.learning_rate" step="0.0001" min="0"
                placeholder="0.0001" class="mac-input" :disabled="!canEdit" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">Unet学习率</span>
                <span class="label-en">unet_lr</span>
              </label>
              <input type="number" v-model.number="config.training_config.unet_lr" step="0.0001" min="0"
                placeholder="0.0005" class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">文本编码器学习率</span>
                <span class="label-en">text_encoder_lr</span>
              </label>
              <input type="number" v-model.number="config.training_config.text_encoder_lr" step="0.00001" min="0"
                placeholder="0.00001" class="mac-input" :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text">学习率调度器</span>
              <span class="label-en">lr_scheduler</span>
            </label>
            <select v-model="config.training_config.lr_scheduler" class="mac-input" :disabled="!canEdit">
              <option value="cosine_with_restarts">余弦退火(cosine_with_restarts)</option>
              <option value="constant">恒定(constant)</option>
              <option value="constant_with_warmup">预热恒定(constant_with_warmup)</option>
              <option value="cosine">余弦(cosine)</option>
              <option value="linear">线性(linear)</option>
              <option value="polynomial">多项式(polynomial)</option>
            </select>
          </div>
          <div class="form-group">
            <label>
              <span class="label-text">优化器类型</span>
              <span class="label-en">optimizer_type</span>
            </label>
            <select v-model="config.training_config.optimizer_type" class="mac-input" :disabled="!canEdit">
              <option value="AdamW8bit">AdamW8bit (推荐)</option>
              <option value="AdamW">AdamW</option>
              <option value="Lion">Lion</option>
              <option value="SGDNesterov">SGDNesterov</option>
              <option value="SGDNesterov8bit">SGDNesterov8bit</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">预热步数</span>
                <span class="label-en">lr_warmup_steps</span>
              </label>
              <input type="number" v-model.number="config.training_config.lr_warmup_steps" min="0" placeholder="0"
                class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">学习率循环次数</span>
                <span class="label-en">lr_scheduler_num_cycles</span>
              </label>
              <input type="number" v-model.number="config.training_config.lr_scheduler_num_cycles" min="1"
                placeholder="1" class="mac-input" :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">每N轮保存一次</span>
                <span class="label-en">save_every_n_epochs</span>
              </label>
              <input type="number" v-model.number="config.training_config.save_every_n_epochs" min="1" placeholder="1"
                class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">每N轮采样一次</span>
                <span class="label-en">sample_every_n_epochs</span>
              </label>
              <input type="number" v-model.number="config.training_config.sample_every_n_epochs" min="1" placeholder="1"
                class="mac-input" :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">CLIP跳过层数</span>
                <span class="label-en">clip_skip</span>
              </label>
              <input type="number" v-model.number="config.training_config.clip_skip" min="1" max="12" placeholder="1"
                class="mac-input" :disabled="!canEdit" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">随机种子</span>
                <span class="label-en">seed</span>
              </label>
              <input type="number" v-model.number="config.training_config.seed" placeholder="42" class="mac-input"
                :disabled="!canEdit" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">混合精度</span>
                <span class="label-en">mixed_precision</span>
              </label>
              <select v-model="config.training_config.mixed_precision" class="mac-input" :disabled="!canEdit">
                <option value="bf16">bf16 (推荐)</option>
                <option value="no">不使用(no)</option>
                <option value="fp16">fp16</option>
              </select>
            </div>
          </div>

          <!-- 采样相关设置 -->
          <div class="section-divider">
            <h4>采样预览设置</h4>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text">生成预览图</span>
                <span class="label-en">generate_preview</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="generate_preview" v-model="config.training_config.generate_preview"
                  class="toggle-checkbox" :disabled="!canEdit" />
                <label for="generate_preview" class="toggle-label"></label>
              </div>
            </div>
            <div class="form-group" v-if="config.training_config.generate_preview">
              <label>
                <span class="label-text">使用图片标签</span>
                <span class="label-en">use_image_tags</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="use_image_tags" v-model="config.training_config.use_image_tags"
                  class="toggle-checkbox" :disabled="!canEdit" />
                <label for="use_image_tags" class="toggle-label"></label>
              </div>
            </div>
          </div>

          <div v-if="config.training_config.generate_preview" class="config-form">
            <div class="form-row" v-if="config.training_config.use_image_tags">
              <div class="form-group">
                <label>
                  <span class="label-text">最多采用图片提示词数量</span>
                  <span class="label-en">max_image_tags</span>
                </label>
                <input type="number" v-model.number="config.training_config.max_image_tags" min="0" placeholder="5"
                  class="mac-input" :disabled="!canEdit" />
              </div>
            </div>

            <div class="form-group full-width">
              <label>
                <span class="label-text">正向提示词</span>
                <span class="label-en">positive_prompt</span>
              </label>
              <textarea v-model="config.training_config.positive_prompt" placeholder="输入正向提示词" rows="2"
                class="mac-textarea" :disabled="!canEdit"></textarea>
            </div>

            <div class="form-group full-width">
              <label>
                <span class="label-text">负向提示词</span>
                <span class="label-en">negative_prompt</span>
              </label>
              <textarea v-model="config.training_config.negative_prompt" placeholder="输入负向提示词" rows="2"
                class="mac-textarea" :disabled="!canEdit"></textarea>
            </div>
            <div class="form-group">
              <label>
                <span class="label-text">采样器</span>
                <span class="label-en">sample_sampler</span>
              </label>
              <select v-model="config.training_config.sample_sampler" class="mac-input" :disabled="!canEdit">
                <option value="euler_a">euler_a</option>
                <option value="euler">euler</option>
                <option value="ddpm">ddpm</option>
                <option value="ddim">ddim</option>
                <option value="dpm++_2m">dpm++_2m</option>
                <option value="dpm++_sde">dpm++_sde</option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>
                  <span class="label-text">预览图宽度</span>
                  <span class="label-en">preview_width</span>
                </label>
                <input type="number" v-model.number="config.training_config.preview_width" min="64" step="8"
                  placeholder="512" class="mac-input" :disabled="!canEdit" />
              </div>
              <div class="form-group">
                <label>
                  <span class="label-text">预览图高度</span>
                  <span class="label-en">preview_height</span>
                </label>
                <input type="number" v-model.number="config.training_config.preview_height" min="64" step="8"
                  placeholder="768" class="mac-input" :disabled="!canEdit" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  <span class="label-text">CFG强度</span>
                  <span class="label-en">cfg_scale</span>
                </label>
                <input type="number" v-model.number="config.training_config.cfg_scale" min="1" step="0.5"
                  placeholder="7" class="mac-input" :disabled="!canEdit" />
              </div>
              <div class="form-group">
                <label>
                  <span class="label-text">迭代步数</span>
                  <span class="label-en">steps</span>
                </label>
                <input type="number" v-model.number="config.training_config.steps" min="1" placeholder="24"
                  class="mac-input" :disabled="!canEdit" />
              </div>
            </div>


          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { tasksApi } from '@/api/tasks'; // 导入任务API

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
  optimizer_type: 'AdamW8bit',
  repeat_num: 1,
  generate_preview: true,
  use_image_tags: false,
  max_image_tags: 5,
  positive_prompt: '1girl, solo',
  negative_prompt: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry',
  preview_width: 512,
  preview_height: 768,
  cfg_scale: 7,
  steps: 24,
  sample_sampler: 'euler_a'
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
  taskId: {
    type: [Number, String],
    required: true
  },
  canEdit: {
    type: Boolean,
    default: true
  }
});

// 修改emit，发送配置对象而不仅是通知
const emit = defineEmits(['config-changed']);

// 组件状态
const isLoading = ref(false);
const saveConfigTimer = ref(null);
const config = ref({
  task_id: null,
  task_name: '',
  use_global_mark_config: true,
  use_global_training_config: true,
  mark_config: { ...defaultMarkConfig },
  training_config: { ...defaultTrainingConfig }
});

// 激活的选项卡
const activeTab = ref('mark');

// 获取任务配置
const fetchConfig = async () => {
  if (!props.taskId) return;

  try {
    isLoading.value = true;
    const data = await tasksApi.getTaskConfig(props.taskId);
    if (data) {
      config.value = data
      // 组件挂载时获取配置后，也向父组件发送配置
      emit('config-changed', data);
    }
  } catch (error) {
    console.error('获取任务配置失败:', error);
  } finally {
    isLoading.value = false;
  }
};

// 保存配置到后端
const saveConfig = () => {
  if (!props.taskId || !props.canEdit) return;

  // 避免频繁请求，使用防抖处理
  if (saveConfigTimer.value) {
    clearTimeout(saveConfigTimer.value);
  }

  saveConfigTimer.value = setTimeout(async () => {
    try {
      isLoading.value = true;

      // 创建要发送的配置对象
      const updateData = {
        use_global_mark_config: config.value.use_global_mark_config,
        use_global_training_config: config.value.use_global_training_config
      };

      // 根据全局配置标志决定是否发送详细配置
      if (!config.value.use_global_mark_config) {
        updateData.mark_config = config.value.mark_config;
      } else if (config.value.mark_config?.trigger_words !== undefined) {
        // 特殊处理触发词：即使使用全局配置，也保留触发词设置
        updateData.mark_config = { trigger_words: config.value.mark_config.trigger_words };
      }

      if (!config.value.use_global_training_config) {
        updateData.training_config = config.value.training_config;
      }

      // 调用更新接口
      await tasksApi.updateTaskConfig(props.taskId, updateData);
      
      // 发送配置已更新事件
      emit('config-changed', config.value);
    } catch (error) {
      console.error('保存任务配置失败:', error);
    } finally {
      isLoading.value = false;
    }
  }, 500); // 500ms防抖
};

// 监听整个config对象的变化，一次性处理所有配置更新
watch(() => config.value, (newConfig) => {
  // 在保存到后端的同时通知父组件配置已变更
  saveConfig();
}, { deep: true, flush: 'post' });

// 监听taskId变化，重新获取配置
watch(() => props.taskId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    fetchConfig();
  }
});

// 组件挂载时获取配置
onMounted(() => {
  fetchConfig();
});
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

.toggle-switch input:checked+label {
  background: #007AFF;
}

.toggle-switch input:checked+label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.toggle-switch input:disabled+label {
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
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label-text {
  font-weight: 500;
}

.label-en {
  font-size: 12px;
  color: var(--text-tertiary, #9CA3AF);
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

.toggle-checkbox:checked+.toggle-label {
  background: #007AFF;
}

.toggle-checkbox:checked+.toggle-label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.toggle-checkbox:disabled+.toggle-label {
  opacity: 0.5;
  cursor: not-allowed;
}

.trigger-words-section {
  margin-top: 8px;
  margin-bottom: 16px;
}

.section-divider {
  border-top: 1px solid #E5E7EB;
  padding-top: 16px;
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