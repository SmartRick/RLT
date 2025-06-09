<template>
  <div class="lora-training-params asset-view">
    <!-- 遍历所有参数分节 -->
    <div v-for="section in visibleSections" :key="section.id" class="params-section">
      <h4 class="params-section-title">{{ section.title }}</h4>

      <!-- 主要参数网格 -->
      <div class="params-grid">
        <!-- 渲染普通参数 -->
        <template v-for="param in section.params" :key="param.name">
          <!-- 特殊参数：单独一行显示 -->
          <div v-if="shouldShowParam(param, modelValue) && 
                   (param.name === 'model_train_type' || 
                    param.name === 'pretrained_model_name_or_path' ||
                    param.name === 'ae' ||
                    param.name === 'clip_l' ||
                    param.name === 't5xxl')"
               class="param-item param-item-full">
            <label>
              <div class="label-text">{{ param.label }}</div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" 
                class="mac-input" 
                :disabled="disabled" 
              />
            </template>
            
            <template v-else-if="param.type === 'number'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, Number($event.target.value))"
                type="number" 
                :placeholder="param.placeholder" 
                :step="param.step" 
                class="mac-input"
                :disabled="disabled" 
              />
            </template>
            
            <template v-else-if="param.type === 'select'">
              <select 
                :value="modelValue[param.name]"
                @change="updateValue(param.name, $event.target.value)" 
                class="mac-input"
                :disabled="disabled"
              >
                <option 
                  v-for="option in param.options" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </template>
          </div>

          <!-- 文本区域类型的参数（正向提示词、负面提示词）：独立一行 -->
          <div v-else-if="shouldShowParam(param, modelValue) && param.type === 'textarea'"
               class="param-item param-item-full">
            <label>
              <div class="label-text">{{ param.label }}</div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <textarea 
              :value="modelValue[param.name]" 
              @input="updateValue(param.name, $event.target.value)"
              :placeholder="param.placeholder" 
              class="mac-textarea" 
              :rows="param.rows || 2"
              :disabled="disabled"
            ></textarea>
          </div>

          <!-- 默认情况：一行两个配置 -->
          <div v-else-if="shouldShowParam(param, modelValue)" class="param-item-half">
            <label>
              <div class="label-text">{{ param.label }}</div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" 
                class="mac-input" 
                :disabled="disabled" 
              />
            </template>
            
            <template v-else-if="param.type === 'number'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, Number($event.target.value))"
                type="number" 
                :placeholder="param.placeholder" 
                :step="param.step" 
                class="mac-input"
                :disabled="disabled" 
              />
            </template>
            
            <template v-else-if="param.type === 'select'">
              <select 
                :value="modelValue[param.name]"
                @change="updateValue(param.name, $event.target.value)" 
                class="mac-input"
                :disabled="disabled"
              >
                <option 
                  v-for="option in param.options" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </template>
          </div>
        </template>
      </div>

      <!-- 子分节 -->
      <template v-for="subsection in getSubsections(section)" :key="subsection.id">
        <div class="params-subsection">
          <h5 class="params-subsection-title">{{ subsection.title }}</h5>
          
          <!-- 如果是桶排序和精度的特殊布局 -->
          <div v-if="subsection.id === 'bucket' || subsection.id === 'precision'" class="params-grid">
            <!-- 参数直接使用统一布局，不再区分特殊容器 -->
            <template v-for="param in subsection.params" :key="param.name">
              <div v-if="shouldShowParam(param, modelValue)" class="param-item-half">
                <label>
                  <div class="label-text">{{ param.label }}</div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <template v-if="param.type === 'text'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" 
                    class="mac-input" 
                    :disabled="disabled" 
                  />
                </template>
                
                <template v-else-if="param.type === 'number'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, Number($event.target.value))"
                    type="number" 
                    :placeholder="param.placeholder" 
                    :step="param.step" 
                    class="mac-input"
                    :disabled="disabled" 
                  />
                </template>
                
                <template v-else-if="param.type === 'select'">
                  <select 
                    :value="modelValue[param.name]"
                    @change="updateValue(param.name, $event.target.value)" 
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option 
                      v-for="option in param.options" 
                      :key="option.value" 
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </template>
              </div>
            </template>
          </div>
          
          <div v-else class="params-grid">
            <template v-for="param in subsection.params" :key="param.name">
              <!-- 文本区域类型的参数（正向提示词、负面提示词）：独立一行 -->
              <div v-if="shouldShowParam(param, modelValue) && 
                        (param.type === 'textarea' || 
                         param.name === 'positive_prompt' || 
                         param.name === 'negative_prompt')"
                   class="param-item param-item-full">
                <label>
                  <div class="label-text">{{ param.label }}</div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <textarea 
                  :value="modelValue[param.name]" 
                  @input="updateValue(param.name, $event.target.value)"
                  :placeholder="param.placeholder" 
                  class="mac-textarea" 
                  :rows="param.rows || 2"
                  :disabled="disabled"
                ></textarea>
              </div>

              <!-- 默认情况：一行两个配置 -->
              <div v-else-if="shouldShowParam(param, modelValue)" class="param-item-half">
                <label>
                  <div class="label-text">{{ param.label }}</div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <template v-if="param.type === 'text'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" 
                    class="mac-input" 
                    :disabled="disabled" 
                  />
                </template>
                
                <template v-else-if="param.type === 'number'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, Number($event.target.value))"
                    type="number" 
                    :placeholder="param.placeholder" 
                    :step="param.step" 
                    class="mac-input"
                    :disabled="disabled" 
                  />
                </template>
                
                <template v-else-if="param.type === 'select'">
                  <select 
                    :value="modelValue[param.name]"
                    @change="updateValue(param.name, $event.target.value)" 
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option 
                      v-for="option in param.options" 
                      :key="option.value" 
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </template>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue';
import { PARAM_SECTIONS, useLoraParams } from '../../composables/useLoraParams';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showAllParams: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

const { shouldShowParam } = useLoraParams();

// 更新值的方法，避免直接修改props
const updateValue = (key, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value
  });
};

// 根据showAllParams过滤可见的分节
const visibleSections = computed(() => {
  return PARAM_SECTIONS.filter(section => {
    // 如果是子分节，则不在顶层显示
    if (section.subsection) {
      return false;
    }
    
    // 如果不是高级配置，或者showAllParams为true，则显示
    return section.always || props.showAllParams;
  });
});

// 获取某个分节的子分节
const getSubsections = (section) => {
  if (!props.showAllParams && section.id !== 'advanced') {
    return [];
  }
  
  return PARAM_SECTIONS.filter(subsection => 
    subsection.subsection && subsection.parent === section.id
  );
};
</script>

<style scoped>
/* 资产表单样式 */
.params-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px dashed #E5E7EB;
  padding-top: 16px;
}

.params-section:first-child {
  border-top: none;
  padding-top: 0;
}

.params-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #4B5563;
  margin: 0;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 4px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.param-item label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-half {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  min-width: 0;
}

.param-item-half label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-full {
  grid-column: span 2;
}

.param-item-group {
  display: flex;
  gap: 12px;
}

/* 通用样式 */
.mac-input {
  width: 100%;
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

.param-name {
  font-size: 11px;
  color: #6B7280;
  opacity: 0.8;
  font-weight: normal;
  display: block;
  margin-top: 2px;
}

label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
}

.label-text {
  font-size: 12px;
  color: #6B7280;
  font-weight: normal;
}

.params-subsection {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #E5E7EB;
  grid-column: 1 / -1;
}

.params-subsection-title {
  font-size: 13px;
  font-weight: 500;
  color: #4B5563;
  margin: 0 0 12px 0;
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

.mac-textarea:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

/* 媒体查询适配 */
@media (max-width: 768px) {
  .params-grid {
    grid-template-columns: 1fr;
  }
}
</style> 