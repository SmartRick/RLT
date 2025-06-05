<template>
  <div class="lora-training-params">
    <!-- 基础参数 -->
    <div class="params-section">
      <h4 :class="[layout === 'settings' ? 'subsection-title' : 'params-section-title']">基础配置</h4>
      <div :class="[layout === 'settings' ? 'settings-grid' : 'params-grid']">
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">模型训练类型</div>
            <span class="param-name">model_train_type</span>
          </label>
          <input 
            :value="modelValue.model_train_type" 
            @input="updateValue('model_train_type', $event.target.value)"
            placeholder="flux-lora"
            class="mac-input"
            :disabled="disabled"
          />
        </div>
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">预训练模型路径</div>
            <span class="param-name">pretrained_model_name_or_path</span>
          </label>
          <input 
            :value="modelValue.pretrained_model_name_or_path" 
            @input="updateValue('pretrained_model_name_or_path', $event.target.value)"
            placeholder="./sd-models/flux1-dev.safetensors"
            class="mac-input"
            :disabled="disabled"
          />
        </div>
        
        <!-- 添加额外模型路径配置 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">自动编码器路径</div>
              <span class="param-name">ae</span>
            </label>
            <input 
              :value="modelValue.ae" 
              @input="updateValue('ae', $event.target.value)"
              placeholder="./sd-models/ae.sft"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">CLIP-L模型路径</div>
              <span class="param-name">clip_l</span>
            </label>
            <input 
              :value="modelValue.clip_l" 
              @input="updateValue('clip_l', $event.target.value)"
              placeholder="./sd-models/clip_l.safetensors"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">T5XXL模型路径</div>
            <span class="param-name">t5xxl</span>
          </label>
          <input 
            :value="modelValue.t5xxl" 
            @input="updateValue('t5xxl', $event.target.value)"
            placeholder="./sd-models/t5xxl_fp8_e4m3fn.safetensors"
            class="mac-input"
            :disabled="disabled"
          />
        </div>
        
        <!-- 添加模型预测配置 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">时间步采样方式</div>
              <span class="param-name">timestep_sampling</span>
            </label>
            <select 
              :value="modelValue.timestep_sampling" 
              @change="updateValue('timestep_sampling', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="sigmoid">sigmoid</option>
              <option value="uniform">uniform</option>
              <option value="uniform_noise">uniform_noise</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">Sigmoid缩放</div>
              <span class="param-name">sigmoid_scale</span>
            </label>
            <input 
              :value="modelValue.sigmoid_scale" 
              @input="updateValue('sigmoid_scale', Number($event.target.value))"
              type="number"
              placeholder="1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">模型预测类型</div>
              <span class="param-name">model_prediction_type</span>
            </label>
            <select 
              :value="modelValue.model_prediction_type" 
              @change="updateValue('model_prediction_type', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="raw">raw</option>
              <option value="v_prediction">v_prediction</option>
              <option value="epsilon">epsilon</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">离散流偏移</div>
              <span class="param-name">discrete_flow_shift</span>
            </label>
            <input 
              :value="modelValue.discrete_flow_shift" 
              @input="updateValue('discrete_flow_shift', Number($event.target.value))"
              type="number"
              placeholder="1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">损失类型</div>
              <span class="param-name">loss_type</span>
            </label>
            <select 
              :value="modelValue.loss_type" 
              @change="updateValue('loss_type', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="l2">l2</option>
              <option value="l1">l1</option>
              <option value="huber">huber</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">引导尺度</div>
              <span class="param-name">guidance_scale</span>
            </label>
            <input 
              :value="modelValue.guidance_scale" 
              @input="updateValue('guidance_scale', Number($event.target.value))"
              type="number"
              placeholder="1"
              step="0.1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 输入和输出目录放在同一组 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">训练数据目录</div>
              <span class="param-name">train_data_dir</span>
            </label>
            <input 
              :value="modelValue.train_data_dir" 
              @input="updateValue('train_data_dir', $event.target.value)"
              placeholder="./train/data"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">输出目录</div>
              <span class="param-name">output_dir</span>
            </label>
            <input 
              :value="modelValue.output_dir" 
              @input="updateValue('output_dir', $event.target.value)"
              placeholder="./output"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 输出名称和分辨率放在同一组 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">输出名称</div>
              <span class="param-name">output_name</span>
            </label>
            <input 
              :value="modelValue.output_name" 
              @input="updateValue('output_name', $event.target.value)"
              placeholder="model_v1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">分辨率</div>
              <span class="param-name">resolution</span>
            </label>
            <input 
              :value="modelValue.resolution" 
              @input="updateValue('resolution', $event.target.value)"
              placeholder="512,512"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 训练参数 -->
    <div class="params-section">
      <h4 :class="[layout === 'settings' ? 'subsection-title' : 'params-section-title']">训练配置</h4>
      <div :class="[layout === 'settings' ? 'settings-grid' : 'params-grid']">
        <!-- 将最大训练轮次和批量大小放在同一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">最大训练轮次</div>
              <span class="param-name">max_train_epochs</span>
            </label>
            <input 
              :value="modelValue.max_train_epochs" 
              @input="updateValue('max_train_epochs', Number($event.target.value))"
              type="number"
              placeholder="10"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">批量大小</div>
              <span class="param-name">train_batch_size</span>
            </label>
            <input 
              :value="modelValue.train_batch_size" 
              @input="updateValue('train_batch_size', Number($event.target.value))"
              type="number"
              placeholder="1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 梯度相关参数 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">梯度检查点</div>
              <span class="param-name">gradient_checkpointing</span>
            </label>
            <select 
              :value="modelValue.gradient_checkpointing" 
              @change="updateValue('gradient_checkpointing', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="true">启用</option>
              <option value="false">禁用</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">梯度累积步数</div>
              <span class="param-name">gradient_accumulation_steps</span>
            </label>
            <input 
              :value="modelValue.gradient_accumulation_steps" 
              @input="updateValue('gradient_accumulation_steps', Number($event.target.value))"
              type="number"
              placeholder="1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 网络训练限制 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">仅训练Unet</div>
              <span class="param-name">network_train_unet_only</span>
            </label>
            <select 
              :value="modelValue.network_train_unet_only" 
              @change="updateValue('network_train_unet_only', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="false">否</option>
              <option value="true">是</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">仅训练文本编码器</div>
              <span class="param-name">network_train_text_encoder_only</span>
            </label>
            <select 
              :value="modelValue.network_train_text_encoder_only" 
              @change="updateValue('network_train_text_encoder_only', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="false">否</option>
              <option value="true">是</option>
            </select>
          </div>
        </div>
        
        <!-- 将网络维度和Alpha放在一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">网络维度 (Dim)</div>
              <span class="param-name">network_dim</span>
            </label>
            <input 
              :value="modelValue.network_dim" 
              @input="updateValue('network_dim', Number($event.target.value))"
              type="number"
              placeholder="64"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">网络Alpha值</div>
              <span class="param-name">network_alpha</span>
            </label>
            <input 
              :value="modelValue.network_alpha" 
              @input="updateValue('network_alpha', Number($event.target.value))"
              type="number"
              placeholder="32"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 基础学习率单独一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">基础学习率</div>
            <span class="param-name">learning_rate</span>
          </label>
          <input 
            :value="modelValue.learning_rate" 
            @input="updateValue('learning_rate', Number($event.target.value))"
            type="number"
            step="0.0001"
            placeholder="0.0001"
            class="mac-input"
            :disabled="disabled"
          />
        </div>
        
        <!-- 将unet_lr和text_encoder_lr放在一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">Unet学习率</div>
              <span class="param-name">unet_lr</span>
            </label>
            <input 
              :value="modelValue.unet_lr" 
              @input="updateValue('unet_lr', Number($event.target.value))"
              type="number"
              step="0.0001"
              placeholder="0.0005"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">文本编码器学习率</div>
              <span class="param-name">text_encoder_lr</span>
            </label>
            <input 
              :value="modelValue.text_encoder_lr" 
              @input="updateValue('text_encoder_lr', Number($event.target.value))"
              type="number"
              step="0.00001"
              placeholder="0.00001"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 学习率调度器单独一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">学习率调度器</div>
            <span class="param-name">lr_scheduler</span>
          </label>
          <select 
            :value="modelValue.lr_scheduler" 
            @change="updateValue('lr_scheduler', $event.target.value)"
            class="mac-input"
            :disabled="disabled"
          >
            <option value="cosine_with_restarts">余弦退火(cosine_with_restarts)</option>
            <option value="constant">恒定(constant)</option>
            <option value="constant_with_warmup">预热恒定(constant_with_warmup)</option>
            <option value="cosine">余弦(cosine)</option>
            <option value="linear">线性(linear)</option>
            <option value="polynomial">多项式(polynomial)</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- 高级参数 -->
    <div class="params-section" v-if="showAllParams">
      <h4 :class="[layout === 'settings' ? 'subsection-title' : 'params-section-title']">高级配置</h4>
      <div :class="[layout === 'settings' ? 'settings-grid' : 'params-grid']">
        <!-- 添加学习率预热与循环配置 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">预热步数</div>
              <span class="param-name">lr_warmup_steps</span>
            </label>
            <input 
              :value="modelValue.lr_warmup_steps" 
              @input="updateValue('lr_warmup_steps', Number($event.target.value))"
              type="number"
              placeholder="0"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">调度器循环次数</div>
              <span class="param-name">lr_scheduler_num_cycles</span>
            </label>
            <input 
              :value="modelValue.lr_scheduler_num_cycles" 
              @input="updateValue('lr_scheduler_num_cycles', Number($event.target.value))"
              type="number"
              placeholder="1"
              class="mac-input"
              :disabled="disabled"
            />
          </div>
        </div>
        
        <!-- 优化器类型单独一行 -->
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item param-item-full']">
          <label>
            <div class="label-text">优化器类型</div>
            <span class="param-name">optimizer_type</span>
          </label>
          <select 
            :value="modelValue.optimizer_type" 
            @change="updateValue('optimizer_type', $event.target.value)"
            class="mac-input"
            :disabled="disabled"
          >
            <option value="AdamW8bit">AdamW8bit (推荐)</option>
            <option value="AdamW">AdamW</option>
            <option value="Lion">Lion</option>
            <option value="SGDNesterov">SGDNesterov</option>
            <option value="SGDNesterov8bit">SGDNesterov8bit</option>
          </select>
        </div>
        
        <!-- 添加采样提示词配置 -->
        <div :class="[layout === 'settings' ? 'settings-item settings-item-full' : 'param-item param-item-full']">
          <label>
            <div class="label-text">采样提示词</div>
            <span class="param-name">sample_prompts</span>
          </label>
          <textarea 
            :value="modelValue.sample_prompts" 
            @input="updateValue('sample_prompts', $event.target.value)"
            placeholder="(masterpiece, best quality:1.2), 1girl, solo, --n lowres, bad anatomy..."
            class="mac-textarea"
            rows="3"
            :disabled="disabled"
          ></textarea>
        </div>
        
        <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-group']">
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">采样器</div>
              <span class="param-name">sample_sampler</span>
            </label>
            <select 
              :value="modelValue.sample_sampler" 
              @change="updateValue('sample_sampler', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="euler_a">euler_a</option>
              <option value="euler">euler</option>
              <option value="ddpm">ddpm</option>
              <option value="ddim">ddim</option>
              <option value="dpm++_2m">dpm++_2m</option>
              <option value="dpm++_sde">dpm++_sde</option>
            </select>
          </div>
          <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
            <label>
              <div class="label-text">日志工具</div>
              <span class="param-name">log_with</span>
            </label>
            <select 
              :value="modelValue.log_with" 
              @change="updateValue('log_with', $event.target.value)"
              class="mac-input"
              :disabled="disabled"
            >
              <option value="tensorboard">tensorboard</option>
              <option value="wandb">wandb</option>
              <option value="none">不使用</option>
            </select>
          </div>
        </div>
        
        <!-- 桶排序参数和精度与计算优化放在同一行 -->
        <div class="params-subsection">
          <div :class="[layout === 'settings' ? 'bucket-precision-settings' : 'bucket-precision-container']">
            <div :class="[layout === 'settings' ? 'settings-section' : 'bucket-section']">
              <h5 :class="[layout === 'settings' ? 'subsection-subtitle' : 'params-subsection-title']">桶排序配置</h5>
              <div :class="[layout === 'settings' ? 'settings-grid' : 'param-item-group']">
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">启用桶排序</div>
                    <span class="param-name">enable_bucket</span>
                  </label>
                  <select 
                    :value="modelValue.enable_bucket" 
                    @change="updateValue('enable_bucket', $event.target.value)"
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option value="true">是</option>
                    <option value="false">否</option>
                  </select>
                </div>
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">无桶放大</div>
                    <span class="param-name">bucket_no_upscale</span>
                  </label>
                  <select 
                    :value="modelValue.bucket_no_upscale" 
                    @change="updateValue('bucket_no_upscale', $event.target.value)"
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option value="true">是</option>
                    <option value="false">否</option>
                  </select>
                </div>
              </div>
              
              <div :class="[layout === 'settings' ? 'settings-grid' : 'param-item-group']">
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">最小桶分辨率</div>
                    <span class="param-name">min_bucket_reso</span>
                  </label>
                  <input 
                    :value="modelValue.min_bucket_reso" 
                    @input="updateValue('min_bucket_reso', Number($event.target.value))"
                    type="number"
                    placeholder="256"
                    class="mac-input"
                    :disabled="disabled"
                  />
                </div>
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">最大桶分辨率</div>
                    <span class="param-name">max_bucket_reso</span>
                  </label>
                  <input 
                    :value="modelValue.max_bucket_reso" 
                    @input="updateValue('max_bucket_reso', Number($event.target.value))"
                    type="number"
                    placeholder="1024"
                    class="mac-input"
                    :disabled="disabled"
                  />
                </div>
              </div>
            </div>
            
            <div :class="[layout === 'settings' ? 'settings-section' : 'precision-section']">
              <h5 :class="[layout === 'settings' ? 'subsection-subtitle' : 'params-subsection-title']">精度与计算优化</h5>
              <div :class="[layout === 'settings' ? 'settings-grid' : 'param-item-group']">
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">混合精度</div>
                    <span class="param-name">mixed_precision</span>
                  </label>
                  <select 
                    :value="modelValue.mixed_precision" 
                    @change="updateValue('mixed_precision', $event.target.value)"
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option value="bf16">bf16 (推荐)</option>
                    <option value="no">不使用(no)</option>
                    <option value="fp16">fp16</option>
                  </select>
                </div>
                <div :class="[layout === 'settings' ? 'settings-item' : 'param-item-half']">
                  <label>
                    <div class="label-text">保存精度</div>
                    <span class="param-name">save_precision</span>
                  </label>
                  <select 
                    :value="modelValue.save_precision" 
                    @change="updateValue('save_precision', $event.target.value)"
                    class="mac-input"
                    :disabled="disabled"
                  >
                    <option value="fp16">fp16 (推荐)</option>
                    <option value="float">float</option>
                    <option value="bf16">bf16</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

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

// 更新值的方法，避免直接修改props
const updateValue = (key, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value
  });
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
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 4px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-group {
  display: flex;
  gap: 12px;
  grid-column: span 2;
}

.param-item-half {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item-half label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-full {
  grid-column: span 2;
}

/* 设置页面样式 */
.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 16px 0 12px;
  color: var(--text-primary);
}

/* 新增设置页面简单横向布局 */
.settings-grid {
  display: block;
  margin-bottom: 16px;
}

.settings-item {
  display: inline-block;
  vertical-align: top;
  width: auto;
  min-width: 280px;
  margin-right: 16px;
  margin-bottom: 16px;
}

.settings-item-full {
  width: 100%;
  margin-right: 0;
}

.settings-section {
  display: inline-block;
  vertical-align: top;
  min-width: 280px;
  margin-right: 16px;
  margin-bottom: 16px;
}

.bucket-precision-settings {
  display: block;
  width: 100%;
}

.form-group label,
.settings-item label {
  font-size: 14px;
  color: var(--text-secondary);
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

/* 媒体查询适配 */
@media (max-width: 768px) {
  .settings-item,
  .settings-section {
    display: block;
    width: 100%;
    margin-right: 0;
  }
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

.subsection-subtitle {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 12px 0;
  color: var(--text-secondary);
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

.config-group-wide {
  grid-column: 1 / -1;
}

/* 为桶排序和精度计算布局添加的样式 */
.bucket-precision-container {
  display: flex;
  gap: 20px;
  width: 100%;
}

.bucket-section, 
.precision-section {
  flex: 1;
  min-width: 0;
}

/* 媒体查询适配 */
@media (max-width: 768px) {
  .bucket-precision-container {
    flex-direction: column;
    gap: 16px;
  }
}
</style> 