<template>
  <div class="lora-training-params settings-view">
    <!-- 遍历所有参数分节 -->
    <div v-for="section in visibleSections" :key="section.id" class="settings-section">
      <h4 class="subsection-title">{{ section.title }}</h4>

      <!-- 主要参数网格 -->
      <div class="settings-grid">
        <!-- 渲染普通参数 -->
        <template v-for="param in section.params" :key="param.name">
          <!-- 所有参数在设置页面都是统一布局 -->
          <div v-if="shouldShowParam(param, modelValue)" class="settings-item">
            <label>
              <div class="label-text">
                {{ param.label }}
                <TooltipText v-if="param.tooltip" width="320px">{{ param.tooltip }}</TooltipText>
              </div>
              <span class="param-name">{{ param.name }}</span>
            </label>

            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" class="mac-input" :class="getThemeClass(param)" :disabled="disabled"
                :title="modelValue[param.name]" />
            </template>

            <template v-else-if="param.type === 'number'">
              <input :value="modelValue[param.name]" @input="updateValue(param.name, Number($event.target.value))"
                type="number" :placeholder="param.placeholder" :step="param.step" class="mac-input" :class="getThemeClass(param)"
                :disabled="disabled" :title="modelValue[param.name]" />
            </template>

            <template v-else-if="param.type === 'select'">
              <select :value="String(modelValue[param.name])" @change="updateValue(param.name, $event.target.value)"
                class="mac-input" :class="getThemeClass(param)" :disabled="disabled">
                <option v-for="option in getParamOptions(param, modelValue)" :key="option.value"
                  :value="String(option.value)">
                  {{ option.label }}
                </option>
              </select>
            </template>

            <template v-else-if="param.type === 'textarea'">
              <textarea :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" class="mac-textarea" :rows="param.rows || 2"
                :disabled="disabled" :title="modelValue[param.name]"></textarea>
            </template>
          </div>
        </template>
      </div>

      <!-- 子分节 -->
      <template v-for="subsection in getSubsections(section)" :key="subsection.id">
        <div class="settings-subsection">
          <h5 class="subsection-subtitle">{{ subsection.title }}</h5>

          <div class="settings-grid">
            <template v-for="param in subsection.params" :key="param.name">
              <div v-if="shouldShowParam(param, modelValue)"
                :class="['settings-item', param.type === 'textarea' ? 'settings-item-full' : '']">
                <label>
                  <div class="label-text">
                    {{ param.label }}
                    <TooltipText v-if="param.tooltip" width="320px">{{ param.tooltip }}</TooltipText>
                  </div>
                  <span class="param-name">{{ param.name }}</span>
                </label>

                <template v-if="param.type === 'text'">
                  <input :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" class="mac-input" :disabled="disabled" 
                    :title="modelValue[param.name]" />
                </template>

                <template v-else-if="param.type === 'number'">
                  <input :value="modelValue[param.name]" @input="updateValue(param.name, Number($event.target.value))"
                    type="number" :placeholder="param.placeholder" :step="param.step" class="mac-input"
                    :disabled="disabled" :title="modelValue[param.name]" />
                </template>

                <template v-else-if="param.type === 'select'">
                  <select :value="String(modelValue[param.name])" @change="updateValue(param.name, $event.target.value)"
                    class="mac-input" :class="getThemeClass(param)" :disabled="disabled">
                    <option v-for="option in getParamOptions(param, modelValue)" :key="option.value"
                      :value="String(option.value)">
                      {{ option.label }}
                    </option>
                  </select>
                </template>

                <template v-else-if="param.type === 'textarea'">
                  <textarea :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" class="mac-textarea" :rows="param.rows || 2"
                    :disabled="disabled" :title="modelValue[param.name]"></textarea>
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
import { defineProps, defineEmits, computed, onMounted } from 'vue';
import { PARAM_SECTIONS } from '../../composables/useLoraParams';
import TooltipText from './TooltipText.vue';
import { getParamOptions, getParamThemeClass, updateModelValue, shouldShowParam } from '../../utils/paramUtils';

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

// 在组件挂载时，根据当前model_train_type设置依赖默认值
onMounted(() => {
  if (props.modelValue.model_train_type) {
    // 创建一个新对象，避免直接修改props
    const updatedModel = { ...props.modelValue };

    // 发出更新事件
    emit('update:modelValue', updatedModel);
  }
});

// 更新值的方法，使用公共工具函数
const updateValue = (key, value) => {
  const updatedModel = updateModelValue(key, value, props.modelValue, PARAM_SECTIONS);
  emit('update:modelValue', updatedModel);
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

// 根据参数主题获取对应的CSS类
const getThemeClass = getParamThemeClass;
</script>

<style scoped>
/* 设置页面样式 */
.settings-section {
  margin-bottom: 24px;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 16px 0 12px;
  color: var(--text-primary, #333333);
}

.settings-grid {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.settings-item {
  display: inline-block;
  vertical-align: top;
  width: 290px;
  margin-right: 16px;
  margin-bottom: 16px;
}

.settings-item-full {
  width: 100%;
  margin-right: 0;
}

.settings-subsection {
  margin: 8px 0 16px;
}

.subsection-subtitle {
  font-size: 14px;
  font-weight: 500;
  margin: 8px 0 12px;
  color: var(--text-secondary, #6B7280);
}

/* 通用样式 */
.mac-input, .mac-textarea {
  width: 100%;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  transition: all 0.2s ease;
  /* 添加悬停提示样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mac-input {
  height: 36px;
  padding: 0 12px;
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

.mac-input:hover, .mac-textarea:hover {
  background-color: #F9FAFB;
  z-index: 5;
  position: relative;
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
  margin-bottom: 6px;
}

.label-text {
  font-size: 12px;
  color: #6B7280;
  font-weight: normal;
}

.mac-textarea {
  min-height: 80px;
  padding: 12px;
  line-height: 1.5;
  resize: vertical;
  white-space: normal; /* 文本域需要正常换行 */
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
  .settings-item {
    width: 100%;
    margin-right: 0;
  }
}

.theme-flux {
  border-color: #0A84FF;
}
.theme-flux:focus {
  border-color: #0A84FF;
  box-shadow: 0 0 0 2px rgba(10, 132, 255, 0.2);
}
.theme-sd {
  border-color: #30D158;
}
.theme-sd:focus {
  border-color: #30D158;
  box-shadow: 0 0 0 2px rgba(48, 209, 88, 0.2);
}
.theme-sdxl {
  border-color: #FF9F0A;
}
.theme-sdxl:focus {
  border-color: #FF9F0A;
  box-shadow: 0 0 0 2px rgba(255, 159, 10, 0.2);
}
</style>