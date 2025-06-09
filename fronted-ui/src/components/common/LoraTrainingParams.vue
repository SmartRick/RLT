<template>
  <div class="lora-training-params-container">
    <!-- 根据layout属性渲染不同的视图组件 -->
    <LoraParamAssetView 
      v-if="layout === 'asset'"
      v-model="localParams"
      :disabled="disabled"
      :showAllParams="showAllParams"
    />
    
    <LoraParamSettingsView
      v-else
      v-model="localParams"
      :disabled="disabled"
      :showAllParams="showAllParams"
    />
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch, toRaw } from 'vue';
import LoraParamAssetView from './LoraParamAssetView.vue';
import LoraParamSettingsView from './LoraParamSettingsView.vue';
import { useLoraParams } from '../../composables/useLoraParams';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  layout: {
    type: String,
    default: 'asset', // 'asset' 或 'settings'
    validator: (value) => ['asset', 'settings'].includes(value)
  },
  showAllParams: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

// 创建本地响应式参数
const localParams = ref({...props.modelValue});

// 单向数据流：只监听props变化更新本地状态
watch(() => props.modelValue, (newVal) => {
  // 使用JSON序列化进行深比较，避免不必要的更新
  if (JSON.stringify(toRaw(localParams.value)) !== JSON.stringify(newVal)) {
    localParams.value = JSON.parse(JSON.stringify(newVal));
  }
}, { immediate: true });

// 当本地参数变化时，发送更新事件（不监听深度变化）
watch(localParams, (newVal) => {
  emit('update:modelValue', toRaw(newVal));
}, { deep: true });
</script>

<style scoped>
.lora-training-params-container {
  width: 100%;
}
</style>