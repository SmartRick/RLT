import { computed, reactive, watch } from 'vue';

// 参数定义，可以被多个组件引用
export const PARAM_SECTIONS = [
  {
    id: 'basic',
    title: '基础配置',
    always: true,
    params: [
      {
        name: 'model_train_type',
        label: '模型训练类型',
        type: 'select',
        options: [
          { value: 'flux-lora', label: 'Flux-Lora' },
          { value: 'sd-lora', label: 'SD1.5-Lora' },
          { value: 'sdxl-lora', label: 'SDXL-Lora' }
        ],
        placeholder: 'flux-lora',
        default: 'flux-lora',
        full: true
      },
      {
        name: 'flux_model_path',
        label: 'Flux模型路径',
        type: 'text',
        placeholder: './sd-models/flux1-dev.safetensors',
        default: '',
        full: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'sd_model_path',
        label: 'SD1.5模型路径',
        type: 'text',
        placeholder: './sd-models/v1-5-pruned-emaonly.safetensors',
        default: '',
        full: true,
        depends: 'model_train_type=sd-lora',
        theme: 'sd'
      },
      {
        name: 'sdxl_model_path',
        label: 'SDXL模型路径',
        type: 'text',
        placeholder: './sd-models/sdxl-base-1.0.safetensors',
        default: '',
        full: true,
        depends: 'model_train_type=sdxl-lora',
        theme: 'sdxl'
      },
      {
        name: 'v2',
        label: 'SD2.0+版本',
        type: 'select',
        options: [
          { value: false, label: '否' },
          { value: true, label: '是' }
        ],
        default: false,
        half: true,
        depends: 'model_train_type=sd-lora',
        theme: 'sd'
      },
      {
        name: 'ae',
        label: '自动编码器路径',
        type: 'text',
        placeholder: './sd-models/ae.sft',
        default: '',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'clip_l',
        label: 'CLIP-L模型路径',
        type: 'text',
        placeholder: './sd-models/clip_l.safetensors',
        default: '',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 't5xxl',
        label: 'T5XXL模型路径',
        type: 'text',
        placeholder: './sd-models/t5xxl_fp8_e4m3fn.safetensors',
        default: '',
        full: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'train_t5xxl',
        label: '训练T5XXL',
        type: 'select',
        options: [
          { value: 'false', label: '否' },
          { value: 'true', label: '是' }
        ],
        default: 'false',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'timestep_sampling',
        label: '时间步采样方式',
        type: 'select',
        options: [
          { value: 'sigmoid', label: 'sigmoid' },
          { value: 'uniform', label: 'uniform' },
          { value: 'uniform_noise', label: 'uniform_noise' }
        ],
        default: 'sigmoid',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'sigmoid_scale',
        label: 'Sigmoid缩放',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'model_prediction_type',
        label: '模型预测类型',
        type: 'select',
        options: [
          { value: 'raw', label: 'raw' },
          { value: 'v_prediction', label: 'v_prediction' },
          { value: 'epsilon', label: 'epsilon' }
        ],
        default: 'raw',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'discrete_flow_shift',
        label: '离散流偏移',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'loss_type',
        label: '损失类型',
        type: 'select',
        options: [
          { value: 'l2', label: 'l2' },
          { value: 'l1', label: 'l1' },
          { value: 'huber', label: 'huber' }
        ],
        default: 'l2',
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'guidance_scale',
        label: '引导尺度',
        type: 'number',
        placeholder: '1',
        step: 0.1,
        default: 1,
        half: true,
        depends: 'model_train_type=flux-lora',
        theme: 'flux'
      },
      {
        name: 'resolution',
        label: '分辨率',
        type: 'text',
        placeholder: '512,512',
        default: '512,512',
        half: true
      }
    ]
  },
  {
    id: 'training',
    title: '训练配置',
    always: true,
    params: [
      {
        name: 'max_train_epochs',
        label: '最大训练轮次',
        type: 'number',
        placeholder: '10',
        default: 10,
        half: true
      },
      {
        name: 'train_batch_size',
        label: '批量大小',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true
      },
      {
        name: 'repeat_num',
        label: '图片重复次数',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true
      },
      {
        name: 'gradient_checkpointing',
        label: '梯度检查点',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      },
      {
        name: 'gradient_accumulation_steps',
        label: '梯度累积步数',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true
      },
      {
        name: 'network_train_unet_only',
        label: '仅训练Unet',
        type: 'select',
        options: [
          { value: false, label: '否' },
          { value: true, label: '是' }
        ],
        default: false,
        half: true
      },
      {
        name: 'network_train_text_encoder_only',
        label: '仅训练文本编码器',
        type: 'select',
        options: [
          { value: false, label: '否' },
          { value: true, label: '是' }
        ],
        default: false,
        half: true
      },
      {
        name: 'network_module',
        label: '网络模块',
        type: 'select',
        options_by_type: {
          'flux-lora': [
            { value: 'networks.lora_flux', label: 'networks.lora_flux' },
            { value: 'networks.oft_flux', label: 'networks.oft_flux' },
            { value: 'lycoris.kohya', label: 'lycoris.kohya' }
          ],
          'sd-lora': [
            { value: 'networks.lora', label: 'networks.lora' },
            { value: 'networks.dylora', label: 'networks.dylora' },
            { value: 'networks.oft', label: 'networks.oft' },
            { value: 'lycoris.kohya', label: 'lycoris.kohya' }
          ],
          'sdxl-lora': [
            { value: 'networks.lora', label: 'networks.lora' },
            { value: 'networks.dylora', label: 'networks.dylora' },
            { value: 'networks.oft', label: 'networks.oft' },
            { value: 'lycoris.kohya', label: 'lycoris.kohya' }
          ]
        },
        placeholder: 'networks.lora_flux',
        default: 'networks.lora_flux',
        full: true
      },
      {
        name: 'network_dim',
        label: '网络维度 (Dim)',
        type: 'number',
        placeholder: '64',
        default: 64,
        half: true
      },
      {
        name: 'network_alpha',
        label: '网络Alpha值',
        type: 'number',
        placeholder: '32',
        default: 32,
        half: true
      },
      {
        name: 'learning_rate',
        label: '基础学习率',
        type: 'number',
        step: 0.0001,
        placeholder: '0.0001',
        default: 0.0001,
        full: true
      },
      {
        name: 'unet_lr',
        label: 'Unet学习率',
        type: 'number',
        step: 0.0001,
        placeholder: '0.0005',
        default: 0.0005,
        half: true
      },
      {
        name: 'text_encoder_lr',
        label: '文本编码器学习率',
        type: 'number',
        step: 0.00001,
        placeholder: '0.00001',
        default: 0.00001,
        half: true
      },
      {
        name: 'lr_scheduler',
        label: '学习率调度器',
        type: 'select',
        options: [
          { value: 'cosine_with_restarts', label: '余弦退火(cosine_with_restarts)' },
          { value: 'constant', label: '恒定(constant)' },
          { value: 'constant_with_warmup', label: '预热恒定(constant_with_warmup)' },
          { value: 'cosine', label: '余弦(cosine)' },
          { value: 'linear', label: '线性(linear)' },
          { value: 'polynomial', label: '多项式(polynomial)' }
        ],
        default: 'cosine_with_restarts',
        full: true
      }
    ]
  },
  {
    id: 'advanced',
    title: '高级配置',
    always: false,
    params: [
      {
        name: 'save_every_n_epochs',
        label: '每N轮保存一次',
        type: 'number',
        placeholder: '2',
        default: 2,
        half: true
      },
      {
        name: 'save_model_as',
        label: '模型保存格式',
        type: 'select',
        options: [
          { value: 'safetensors', label: 'safetensors' },
          { value: 'ckpt', label: 'ckpt' }
        ],
        default: 'safetensors',
        half: true
      },
      {
        name: 'lr_warmup_steps',
        label: '预热步数',
        type: 'number',
        placeholder: '0',
        default: 0,
        half: true
      },
      {
        name: 'lr_scheduler_num_cycles',
        label: '调度器循环次数',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true
      },
      {
        name: 'log_with',
        label: '日志工具',
        type: 'select',
        options: [
          { value: 'tensorboard', label: 'tensorboard' },
          { value: 'wandb', label: 'wandb' },
          { value: 'none', label: '不使用' }
        ],
        default: 'tensorboard',
        half: true
      },
      {
        name: 'logging_dir',
        label: '日志目录',
        type: 'text',
        placeholder: './logs',
        default: './logs',
        half: true
      },
      {
        name: 'optimizer_type',
        label: '优化器类型',
        type: 'select',
        options: [
          { value: 'AdamW8bit', label: 'AdamW8bit (推荐)' },
          { value: 'AdamW', label: 'AdamW' },
          { value: 'Lion', label: 'Lion' },
          { value: 'SGDNesterov', label: 'SGDNesterov' },
          { value: 'SGDNesterov8bit', label: 'SGDNesterov8bit' }
        ],
        default: 'AdamW8bit',
        full: true
      }
    ]
  },
  {
    id: 'preview',
    title: '预览图生成配置',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'generate_preview',
        label: '生成预览图',
        type: 'select',
        options: [
          { value: true, label: '是' },
          { value: false, label: '否' }
        ],
        default: true,
        half: true
      },
      {
        name: 'sample_every_n_epochs',
        label: '每N轮生成一次预览',
        type: 'number',
        placeholder: '2',
        default: 2,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'use_image_tags',
        label: '使用图片标签',
        type: 'select',
        options: [
          { value: false, label: '否' },
          { value: true, label: '是' }
        ],
        default: false,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'max_image_tags',
        label: '最多采用图片提示词数量',
        type: 'number',
        placeholder: '5',
        default: 5,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'positive_prompts',
        label: '正向提示词',
        type: 'textarea',
        placeholder: 'masterpiece, best quality, 1girl, solo',
        default: 'masterpiece, best quality, 1girl, solo',
        full: true,
        rows: 2,
        depends: 'generate_preview=true'
      },
      {
        name: 'negative_prompts',
        label: '负面提示词',
        type: 'textarea',
        placeholder: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry',
        default: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry',
        full: true,
        rows: 2,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_width',
        label: '预览图宽度',
        type: 'number',
        placeholder: '512',
        default: 512,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_height',
        label: '预览图高度',
        type: 'number',
        placeholder: '768',
        default: 768,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_cfg',
        label: 'CFG强度',
        type: 'number',
        placeholder: '7',
        step: 0.5,
        default: 7,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_steps',
        label: '迭代步数',
        type: 'number',
        placeholder: '24',
        default: 24,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_seed',
        label: '随机种子',
        type: 'number',
        placeholder: '1337',
        default: 1337,
        half: true,
        depends: 'generate_preview=true'
      },
      {
        name: 'sample_sampler',
        label: '采样器',
        type: 'select',
        options: [
          { value: 'euler_a', label: 'euler_a' },
          { value: 'euler', label: 'euler' },
          { value: 'ddpm', label: 'ddpm' },
          { value: 'ddim', label: 'ddim' },
          { value: 'dpm++_2m', label: 'dpm++_2m' },
          { value: 'dpm++_sde', label: 'dpm++_sde' }
        ],
        default: 'euler_a',
        half: true,
        depends: 'generate_preview=true'
      }
    ]
  },
  {
    id: 'bucket',
    title: '桶排序配置',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'enable_bucket',
        label: '启用桶排序',
        type: 'select',
        options: [
          { value: true, label: '是' },
          { value: false, label: '否' }
        ],
        default: true,
        half: true
      },
      {
        name: 'bucket_no_upscale',
        label: '无桶放大',
        type: 'select',
        options: [
          { value: true, label: '是' },
          { value: false, label: '否' }
        ],
        default: true,
        half: true
      },
      {
        name: 'min_bucket_reso',
        label: '最小桶分辨率',
        type: 'number',
        placeholder: '256',
        default: 256,
        half: true
      },
      {
        name: 'max_bucket_reso',
        label: '最大桶分辨率',
        type: 'number',
        placeholder: '1024',
        default: 1024,
        half: true
      },
      {
        name: 'bucket_reso_steps',
        label: '桶分辨率步长',
        type: 'number',
        placeholder: '32',
        default: 32,
        half: true
      }
    ]
  },
  {
    id: 'precision',
    title: '精度与计算优化',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'mixed_precision',
        label: '混合精度',
        type: 'select',
        options: [
          { value: 'bf16', label: 'bf16 (推荐)' },
          { value: 'no', label: '不使用(no)' },
          { value: 'fp16', label: 'fp16' }
        ],
        default: 'bf16',
        half: true
      },
      {
        name: 'save_precision',
        label: '保存精度',
        type: 'select',
        options: [
          { value: 'fp16', label: 'fp16 (推荐)' },
          { value: 'float', label: 'float' },
          { value: 'bf16', label: 'bf16' }
        ],
        default: 'fp16',
        half: true
      },
      {
        name: 'fp8_base',
        label: 'FP8基础',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true,
        depends: 'model_train_type=flux-lora'
      },
      {
        name: 'sdpa',
        label: 'SDPA优化',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      }
    ]
  },
  {
    id: 'memory',
    title: '内存优化',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'lowram',
        label: '低内存模式',
        type: 'select',
        options: [
          { value: false, label: '禁用' },
          { value: true, label: '启用' }
        ],
        default: false,
        half: true
      },
      {
        name: 'cache_latents',
        label: '缓存潜变量',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      },
      {
        name: 'cache_latents_to_disk',
        label: '潜变量缓存到磁盘',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      },
      {
        name: 'cache_text_encoder_outputs',
        label: '缓存文本编码器输出',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true,
        depends: 'model_train_type=flux-lora'
      },
      {
        name: 'cache_text_encoder_outputs_to_disk',
        label: '文本编码器输出缓存到磁盘',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true,
        depends: 'model_train_type=flux-lora'
      },
      {
        name: 'persistent_data_loader_workers',
        label: '持久数据加载器工作线程',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      }
    ]
  },
  {
    id: 'text_processing',
    title: '文本处理',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'caption_extension',
        label: '标题文件扩展名',
        type: 'text',
        placeholder: '.txt',
        default: '.txt',
        half: true
      },
      {
        name: 'shuffle_caption',
        label: '随机打乱标题',
        type: 'select',
        options: [
          { value: false, label: '禁用' },
          { value: true, label: '启用' }
        ],
        default: false,
        half: true
      },
      {
        name: 'keep_tokens',
        label: '保留令牌数',
        type: 'number',
        placeholder: '0',
        default: 0,
        half: true
      },
      {
        name: 'clip_skip',
        label: 'CLIP跳过层数',
        type: 'number',
        placeholder: '2',
        default: 2,
        half: true
      },
      {
        name: 'max_token_length',
        label: '最大令牌长度',
        type: 'number',
        placeholder: '255',
        default: 255,
        half: true
      },
      {
        name: 'prior_loss_weight',
        label: '先验损失权重',
        type: 'number',
        placeholder: '1',
        default: 1,
        half: true
      }
    ]
  },
  {
    id: 'full_precision',
    title: '全精度',
    subsection: true,
    parent: 'advanced',
    params: [
      {
        name: 'full_fp16',
        label: '全FP16精度',
        type: 'select',
        options: [
          { value: false, label: '禁用' },
          { value: true, label: '启用' }
        ],
        default: false,
        half: true
      },
      {
        name: 'full_bf16',
        label: '全BF16精度',
        type: 'select',
        options: [
          { value: true, label: '启用' },
          { value: false, label: '禁用' }
        ],
        default: true,
        half: true
      }
    ]
  }
];

// 创建默认参数值对象
const createDefaultParams = () => {
  const defaultParams = {};
  PARAM_SECTIONS.forEach(section => {
    section.params.forEach(param => {
      defaultParams[param.name] = param.default;
    });
  });
  return defaultParams;
};

export function useLoraParams(initialParams = {}) {
  // 合并默认参数与初始参数
  const mergedParams = {
    ...createDefaultParams(),
    ...initialParams
  };
  
  // 创建响应式数据
  const params = reactive(mergedParams);

  // 更新参数值的方法
  const updateParam = (name, value) => {
    params[name] = value;
  };

  // 获取所有参数的计算属性
  const allParams = computed(() => params);

  // 获取参数是否应该显示的方法
  const shouldShowParam = (param, allParams) => {
    if (!param.depends) return true;
    
    // 处理依赖条件
    const [dependName, dependValue] = param.depends.split('=');
    return String(allParams[dependName]) === dependValue;
  };

  return {
    params,
    updateParam,
    allParams,
    shouldShowParam,
    PARAM_SECTIONS
  };
} 