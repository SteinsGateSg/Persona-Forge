# Persona-Forge

English documentation: [README.md](README.md)

`Persona-Forge` 是一个面向二次元 / 角色语音项目的通用训练工具仓库，底层围绕本地 `GPT-SoVITS` 工作流组织。

GitHub 仓库：

- `https://github.com/SteinsGateSg/Persona-Forge`

项目主页：

- `docs/index.html`

它是“两个独立仓库”方案里的**通用框架仓库**：

- 框架仓库：可复用流程与工具
- 角色仓库：某一个具体角色的数据、参考库、权重与 demo

目前第一个完整角色实例是 `Mayuri-Amadeus`：

- `https://github.com/SteinsGateSg/Mayuri-Amadeus`

## 这个仓库负责什么

- 从转写 CSV 构建 GPT-SoVITS manifest
- 执行 `prepare`
- 训练 SoVITS
- 导出 SoVITS 推理权重
- 训练 GPT
- 用固定 GPT + SoVITS 模型组合执行推理
- 用 OpenAI 兼容接口标注参考音频情感
- 用 `doctor` 检查本地训练环境

## 仓库结构

```text
Persona-Forge/
  character_voice_lab/
    cli.py
    manifest.py
    gpt_sovits.py
    reference_bank.py
    synthesize.py
  examples/
    minimal_profile.yaml
  README.md
  README_ZH.md
  pyproject.toml
```

## 安装

```bash
git clone https://github.com/SteinsGateSg/Persona-Forge.git
cd Persona-Forge
pip install -e .
```

安装后主命令入口是：

```bash
persona-forge
```

兼容别名仍然保留：

```bash
character-voice-lab
```

## 常用命令

### 1. 构建 manifest

```bash
persona-forge build-manifest \
  --csv data/meta/transcripts.csv \
  --wav-dir data/raw/wav \
  --output-list artifacts/manifests/train.list \
  --speaker speaker_0 \
  --language ja
```

### 2. 执行 prepare

```bash
persona-forge prepare \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list \
  --version v2 \
  --exp-name example_character_v2 \
  --gpus 0
```

### 3. 训练 SoVITS

```bash
persona-forge train-sovits \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list \
  --version v2 \
  --exp-name example_character_v2 \
  --gpus 0 \
  --batch-size 4 \
  --epochs 16
```

### 4. 训练 GPT

```bash
persona-forge train-gpt \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list \
  --version v2 \
  --exp-name example_character_v2 \
  --gpus 0 \
  --batch-size 2 \
  --epochs 8
```

### 5. 生成试听 / 推理

```bash
persona-forge synthesize \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --gpt-model /path/to/GPT_weights/example-e8.ckpt \
  --sovits-model /path/to/SoVITS_weights/example_e20.pth \
  --ref-audio /path/to/refs/neutral/sample.wav \
  --ref-text-file /path/to/refs/neutral/sample.txt \
  --target-text "Hello again." \
  --ref-language 英文 \
  --target-language 英文 \
  --output-dir artifacts/preview/latest
```

### 6. 标注参考音频情感

```bash
persona-forge label-emotions \
  --manifest artifacts/manifests/train.list \
  --output-dir artifacts/reference_bank \
  --batch-size 5 \
  --resume
```

## 当前阶段的定位

这是第一版框架骨架，重点是先把 `Mayuri-Amadeus` 中已经验证过的通用流程抽出来：

- manifest 构建
- GPT-SoVITS 训练包装
- 参考库情感标注
- 通用推理入口

下一步还可以继续补：

- profile 驱动
- refs 自动整理
- 评测脚本
- CI smoke test

## 不包含什么

- 不直接内置 `GPT-SoVITS` 源码
- 不直接内置底模
- 不直接内置某个角色的数据和最终权重

这些内容应该由具体角色仓库承载。
