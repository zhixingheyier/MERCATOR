---
library_name: peft
license: other
base_model: /media/guo/E/work/mywork_1/LLM_model/LLM-Research/Meta-Llama-3.1-8B
tags:
- llama-factory
- lora
- generated_from_trainer
model-index:
- name: train_2025-05-27-Llama-3.1-8B-10-epoch-320steps
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# train_2025-05-27-Llama-3.1-8B-10-epoch-320steps

This model is a fine-tuned version of [/media/guo/E/work/mywork_1/LLM_model/LLM-Research/Meta-Llama-3.1-8B](https://huggingface.co//media/guo/E/work/mywork_1/LLM_model/LLM-Research/Meta-Llama-3.1-8B) on the 5_27_train dataset.

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-05
- train_batch_size: 1
- eval_batch_size: 8
- seed: 42
- distributed_type: multi-GPU
- num_devices: 4
- gradient_accumulation_steps: 8
- total_train_batch_size: 32
- total_eval_batch_size: 32
- optimizer: Use adamw_torch with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_steps: 5
- num_epochs: 10.0

### Training results



### Framework versions

- PEFT 0.15.1
- Transformers 4.51.3
- Pytorch 2.6.0+cu124
- Datasets 3.5.0
- Tokenizers 0.21.1