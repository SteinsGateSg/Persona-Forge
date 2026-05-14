# Persona-Forge

Chinese documentation: [README_ZH.md](README_ZH.md)

`Persona-Forge` is a reusable training toolkit for anime / character voice projects built around a local `GPT-SoVITS` workflow.

GitHub repo:

- `https://github.com/SteinsGateSg/Persona-Forge`

Project homepage:

- `docs/index.html`

This repository is the framework half of a two-repo split:

- framework repo: reusable workflow and tooling
- character repo: one concrete character dataset, refs, weights, and demos

The first full character instance is `Mayuri-Amadeus`:

- `https://github.com/SteinsGateSg/Mayuri-Amadeus`

## What It Covers

- build GPT-SoVITS manifests from CSV transcripts
- run GPT-SoVITS `prepare`
- train SoVITS
- export SoVITS inference weights
- train GPT
- run inference with a fixed GPT + SoVITS model pair
- label a reference bank with an OpenAI-compatible API
- check local prerequisites with `doctor`

## Repository Layout

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

## Installation

```bash
git clone https://github.com/SteinsGateSg/Persona-Forge.git
cd Persona-Forge
pip install -e .
```

After installation, the primary CLI entrypoint is:

```bash
persona-forge
```

Backward-compatible alias:

```bash
character-voice-lab
```

## Commands

### Build a manifest

```bash
persona-forge build-manifest \
  --csv data/meta/transcripts.csv \
  --wav-dir data/raw/wav \
  --output-list artifacts/manifests/train.list \
  --speaker speaker_0 \
  --language ja
```

### Run GPT-SoVITS prepare

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

### Run inference

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

### Label reference emotions

```bash
persona-forge label-emotions \
  --manifest artifacts/manifests/train.list \
  --output-dir artifacts/reference_bank \
  --batch-size 5 \
  --resume
```

## Notes

- This repo does not bundle `GPT-SoVITS` itself.
- This repo does not bundle pretrained base models.
- Character-specific data and final weights should live in a separate character repo.
- The internal Python package path remains `character_voice_lab` for stability.
