<div align="center">

# ✦ Persona-Forge ✦

<p><em>Constellation Toolkit for Character Voice Systems</em></p>

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
  <img src="https://img.shields.io/badge/Selector-Generic-a55d3f?style=flat-square" alt="Selector" />
  <img src="https://img.shields.io/badge/Layout-Two%20Repositories-7e6b55?style=flat-square" alt="Layout" />
  <img src="https://img.shields.io/badge/Focus-Local%20Iteration-b68d54?style=flat-square" alt="Focus" />
</p>

English · <a href="README_ZH.md">简体中文</a>

</div>

`Persona-Forge` is the reusable half of the release pair: a local-first framework for curating references, preparing manifests, training GPT-SoVITS stages, selecting prompts, and packaging character-voice workflows.

## What Lives Here

- manifest construction from transcript CSV files
- GPT-SoVITS `prepare`, `train-sovits`, and `train-gpt` wrappers
- generic reference selector for curated `refs/index.csv` banks
- synthesis entrypoint for fixed GPT + SoVITS pairs
- reference-bank emotion labeling through OpenAI-compatible APIs
- environment checks through `doctor`

## Installation

```bash
git clone https://github.com/SteinsGateSg/Persona-Forge.git
cd Persona-Forge
pip install -e .
```

Primary CLI:

```bash
persona-forge
```

Compatibility alias:

```bash
character-voice-lab
```

## Core Commands

### Build a manifest

```bash
persona-forge build-manifest \
  --csv data/meta/transcripts.csv \
  --wav-dir data/raw/wav \
  --output-list artifacts/manifests/train.list \
  --speaker speaker_0 \
  --language ja
```

### Prepare GPT-SoVITS features

```bash
persona-forge prepare \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list \
  --version v2 \
  --exp-name example_character_v2 \
  --gpus 0
```

### Train SoVITS

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

### Train GPT

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

### Select a reference

```bash
persona-forge select-reference \
  --refs-index /path/to/refs/index.csv \
  --asset-root /path/to/character-repo \
  --target-text "亲爱的你啊，好久不见。" \
  --target-language 中文 \
  --backend heuristic \
  --format json
```

### Run synthesis

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

### Label a reference bank

```bash
persona-forge label-emotions \
  --manifest artifacts/manifests/train.list \
  --output-dir artifacts/reference_bank \
  --batch-size 5 \
  --resume
```

### Inspect the local environment

```bash
persona-forge doctor \
  --gpt-sovits-root /path/to/GPT-SoVITS \
  --pretrained-root /path/to/GPT-SoVITS-models \
  --manifest artifacts/manifests/train.list
```

## Repository Layout

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

## Example Pair

`Mayuri-Amadeus` is the first complete character repository built on top of this workflow:

- character repo: `Mayuri-Amadeus`
- framework repo: `Persona-Forge`

## Notes

- `GPT-SoVITS` source code is external.
- Pretrained base models are external.
- Final large weights and raw datasets belong in character repositories and Hugging Face releases.
- The internal Python package path remains `character_voice_lab` for compatibility.
