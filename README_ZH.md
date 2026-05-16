<div align="center">

# ✦ Persona-Forge ✦

<p><em>面向角色语音系统的星图式工具框架</em></p>

<p>
  <a href="https://steinsgatesg.github.io/Persona-Forge/">
    <img src="https://img.shields.io/badge/🌌%20Homepage-23384a?style=for-the-badge&logoColor=f4f8ff" alt="Homepage" />
  </a>
  <a href="https://github.com/SteinsGateSg/Persona-Forge">
    <img src="https://img.shields.io/badge/🐙%20GitHub-181717?style=for-the-badge&logo=github&logoColor=ffffff" alt="GitHub repository" />
  </a>
  <a href="https://github.com/SteinsGateSg/Mayuri-Amadeus">
    <img src="https://img.shields.io/badge/🪐%20Example-Mayuri--Amadeus-7b4f3b?style=for-the-badge&logoColor=fffaf4" alt="Example character repository" />
  </a>
</p>

<p>
  <img src="https://img.shields.io/badge/Workflow-GPT--SoVITS-27586b?style=flat-square" alt="Workflow" />
  <img src="https://img.shields.io/badge/Selector-通用-b55d3f?style=flat-square" alt="Selector" />
  <img src="https://img.shields.io/badge/Layout-双仓库-7e6b55?style=flat-square" alt="Layout" />
  <img src="https://img.shields.io/badge/Focus-本地迭代-b68d54?style=flat-square" alt="Focus" />
</p>

简体中文 · <a href="README.md">English</a>

</div>

`Persona-Forge` 是发布组合里的通用一侧：负责整理参考音频、构建 manifest、封装 GPT-SoVITS 训练阶段、选择参考提示，并把角色语音工作流组织成可复用的本地工具链。

## 这个仓库负责什么

- 从转写 CSV 构建 manifest
- 封装 GPT-SoVITS 的 `prepare`、`train-sovits`、`train-gpt`
- 提供面向 `refs/index.csv` 的通用参考音频 selector
- 提供固定 GPT + SoVITS 组合的推理入口
- 通过 OpenAI 兼容接口标注参考音频情感
- 通过 `doctor` 检查本地环境

## 安装

```bash
git clone https://github.com/SteinsGateSg/Persona-Forge.git
cd Persona-Forge
pip install -e .
```

主命令入口：

```bash
persona-forge
```

兼容别名：

```bash
character-voice-lab
```

## 核心命令

### 构建 manifest

```bash
persona-forge build-manifest \
  --csv data/meta/transcripts.csv \
  --wav-dir data/raw/wav \
  --output-list artifacts/manifests/train.list \
  --speaker speaker_0 \
  --language ja
```

### 执行 GPT-SoVITS prepare

```bash
persona-forge prepare \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list \
  --version v2 \
  --exp-name example_character_v2 \
  --gpus 0
```

### 训练 SoVITS

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

### 训练 GPT

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

### 选择参考音频

```bash
persona-forge select-reference \
  --refs-index /path/to/refs/index.csv \
  --asset-root /path/to/character-repo \
  --target-text "亲爱的你啊，好久不见。" \
  --target-language 中文 \
  --backend heuristic \
  --format json
```

### 执行推理

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

### 标注参考音频情感

```bash
persona-forge label-emotions \
  --manifest artifacts/manifests/train.list \
  --output-dir artifacts/reference_bank \
  --batch-size 5 \
  --resume
```

### 检查本地环境

```bash
persona-forge doctor \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list
```

## 仓库结构

```text
Persona-Forge/
  character_voice_lab/
    cli.py
    gpt_sovits.py
    manifest.py
    reference_bank.py
    selector.py
    synthesize.py
  docs/
  examples/
    minimal_profile.yaml
  README.md
  README_ZH.md
  pyproject.toml
```

## 示例组合

`Mayuri-Amadeus` 是当前第一套完整角色实例：

- 角色仓库：`Mayuri-Amadeus`
- 通用框架：`Persona-Forge`

## 说明

- `GPT-SoVITS` 源码不直接内置在本仓库中。
- 底模不直接内置在本仓库中。
- 最终大权重和原始数据集应放在角色仓库与 Hugging Face 发布物中。
- 为了兼容已有代码，内部 Python 包路径仍然保持为 `character_voice_lab`。
