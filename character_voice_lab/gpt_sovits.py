#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import OrderedDict
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "artifacts" / "manifests" / "train.list"
GENERATED_CONFIG_DIR = PROJECT_ROOT / "artifacts" / "generated"
PRETRAINED_PREFIX = Path("GPT_SoVITS/pretrained_models")

VERSION_META = {
    "v1": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/s2G488k.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2.json",
        "s1_config": "GPT_SoVITS/configs/s1longer.yaml",
        "sovits_weight_dir": "SoVITS_weights",
        "gpt_weight_dir": "GPT_weights",
    },
    "v2": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2.json",
        "s1_config": "GPT_SoVITS/configs/s1longer-v2.yaml",
        "sovits_weight_dir": "SoVITS_weights_v2",
        "gpt_weight_dir": "GPT_weights_v2",
    },
    "v2Pro": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2v2Pro.json",
        "s1_config": "GPT_SoVITS/configs/s1longer-v2.yaml",
        "sovits_weight_dir": "SoVITS_weights_v2Pro",
        "gpt_weight_dir": "GPT_weights_v2Pro",
    },
    "v2ProPlus": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2v2ProPlus.json",
        "s1_config": "GPT_SoVITS/configs/s1longer-v2.yaml",
        "sovits_weight_dir": "SoVITS_weights_v2ProPlus",
        "gpt_weight_dir": "GPT_weights_v2ProPlus",
    },
    "v3": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/s2Gv3.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2.json",
        "s1_config": "GPT_SoVITS/configs/s1longer-v2.yaml",
        "sovits_weight_dir": "SoVITS_weights_v3",
        "gpt_weight_dir": "GPT_weights_v3",
    },
    "v4": {
        "pretrained_s2g": "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth",
        "pretrained_s1": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "s2_config": "GPT_SoVITS/configs/s2.json",
        "s1_config": "GPT_SoVITS/configs/s1longer-v2.yaml",
        "sovits_weight_dir": "SoVITS_weights_v4",
        "gpt_weight_dir": "GPT_weights_v4",
    },
}


def default_gpt_sovits_root() -> Path:
    env_root = os.environ.get("GPT_SOVITS_ROOT", "").strip()
    candidates = []
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend(
        [
            PROJECT_ROOT / "third_party" / "GPT-SoVITS",
            PROJECT_ROOT.parent / "GPT-SoVITS",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DEFAULT_GPT_SOVITS_ROOT = default_gpt_sovits_root()


def default_pretrained_root() -> Path:
    env_root = os.environ.get("GPT_SOVITS_MODEL_ROOT", "").strip()
    candidates = []
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend(
        [
            PROJECT_ROOT / "third_party" / "GPT-SoVITS-models",
            PROJECT_ROOT / "models" / "GPT-SoVITS",
            PROJECT_ROOT.parent / "models" / "GPT-SoVITS",
            Path.home() / "models" / "GPT-SoVITS",
            DEFAULT_GPT_SOVITS_ROOT,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


DEFAULT_PRETRAINED_ROOT = default_pretrained_root()


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def parse_gpu_list(raw: str) -> list[str]:
    items = [part.strip() for part in re.split(r"[-,]", raw) if part.strip()]
    if not items:
        raise ValueError("No GPU index was provided")
    return items


def strtobool(value: bool | str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def version_meta(version: str) -> dict[str, str]:
    if version not in VERSION_META:
        raise KeyError(f"Unsupported version: {version}")
    return VERSION_META[version]


def model_relative_path(path_str: str) -> Path:
    path = Path(path_str)
    try:
        return path.relative_to(PRETRAINED_PREFIX)
    except ValueError:
        return path


def resolve_model_file(models_root: Path, gpt_root: Path, path_str: str) -> Path:
    model_path = models_root / model_relative_path(path_str)
    repo_path = gpt_root / path_str
    if model_path.exists():
        return model_path
    if repo_path.exists():
        return repo_path
    return model_path


def gpt_sovits_defaults(gpt_root: Path, models_root: Path, version: str) -> dict[str, Path]:
    meta = version_meta(version)
    pretrained_s2g = resolve_model_file(models_root, gpt_root, meta["pretrained_s2g"])
    return {
        "bert_pretrained_dir": gpt_root / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large",
        "cnhubert_base_dir": gpt_root / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base",
        "pretrained_s2g": pretrained_s2g,
        "pretrained_s2d": Path(str(pretrained_s2g).replace("s2G", "s2D")),
        "pretrained_s1": resolve_model_file(models_root, gpt_root, meta["pretrained_s1"]),
        "s2_config": gpt_root / meta["s2_config"],
        "s1_config": gpt_root / meta["s1_config"],
        "sovits_weight_dir": gpt_root / meta["sovits_weight_dir"],
        "gpt_weight_dir": gpt_root / meta["gpt_weight_dir"],
    }


def require_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def print_command(cmd: list[str], cwd: Path) -> None:
    rendered = " ".join(cmd)
    print(f"[run] (cwd={cwd}) {rendered}")


def extend_pythonpath(env: dict[str, str], gpt_root: Path) -> dict[str, str]:
    extra_paths = [
        str(gpt_root),
        str(gpt_root / "GPT_SoVITS"),
        str(gpt_root / "GPT_SoVITS" / "BigVGAN"),
        str(gpt_root / "tools"),
        str(gpt_root / "tools" / "asr"),
        str(gpt_root / "tools" / "uvr5"),
    ]
    current = env.get("PYTHONPATH", "")
    combined = extra_paths + ([current] if current else [])
    env["PYTHONPATH"] = os.pathsep.join(combined)
    return env


def run_command(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print_command(cmd, cwd)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def run_parallel(cmds: list[tuple[list[str], dict[str, str]]], cwd: Path) -> None:
    procs = []
    exit_codes: list[int] = []
    try:
        for cmd, env in cmds:
            print_command(cmd, cwd)
            procs.append(subprocess.Popen(cmd, cwd=cwd, env=env))
        exit_codes = [proc.wait() for proc in procs]
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
    for code in exit_codes:
        if code != 0:
            raise subprocess.CalledProcessError(code, cmds)


def remove_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def merge_text_parts(exp_dir: Path, part_count: int) -> Path:
    lines: list[str] = []
    for idx in range(part_count):
        part_path = exp_dir / f"2-name2text-{idx}.txt"
        require_exists(part_path, "text shard")
        shard_lines = [line for line in part_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        lines.extend(shard_lines)
        part_path.unlink()
    merged = exp_dir / "2-name2text.txt"
    merged.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return merged


def merge_semantic_parts(exp_dir: Path, part_count: int) -> Path:
    lines = ["item_name\tsemantic_audio"]
    for idx in range(part_count):
        part_path = exp_dir / f"6-name2semantic-{idx}.tsv"
        require_exists(part_path, "semantic shard")
        shard_lines = [line for line in part_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        lines.extend(shard_lines)
        part_path.unlink()
    merged = exp_dir / "6-name2semantic.tsv"
    merged.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return merged


def prepare(args: argparse.Namespace) -> int:
    gpt_root = resolve_path(args.gpt_sovits_root)
    models_root = resolve_path(args.pretrained_root)
    manifest = resolve_path(args.manifest)
    require_exists(gpt_root, "GPT-SoVITS root")
    require_exists(manifest, "manifest")

    defaults = gpt_sovits_defaults(gpt_root, models_root, args.version)
    bert_pretrained_dir = resolve_path(args.bert_pretrained_dir or defaults["bert_pretrained_dir"])
    cnhubert_base_dir = resolve_path(args.cnhubert_base_dir or defaults["cnhubert_base_dir"])
    pretrained_s2g = resolve_path(args.pretrained_s2g or defaults["pretrained_s2g"])

    require_exists(bert_pretrained_dir, "BERT pretrained dir")
    require_exists(cnhubert_base_dir, "CNHubert pretrained dir")
    if not args.skip_semantic:
        require_exists(pretrained_s2g, "pretrained s2G")

    gpu_parts = parse_gpu_list(args.gpus)
    gpu_dash = "-".join(gpu_parts)
    exp_dir = gpt_root / "logs" / args.exp_name
    ensure_dir(exp_dir)

    if args.force:
        for relative in ("2-name2text.txt", "3-bert", "4-cnhubert", "5-wav32k", "6-name2semantic.tsv"):
            remove_if_exists(exp_dir / relative)

    text_output = exp_dir / "2-name2text.txt"
    if text_output.exists():
        print(f"[skip] text metadata already exists: {text_output}")
    else:
        for idx in range(len(gpu_parts)):
            remove_if_exists(exp_dir / f"2-name2text-{idx}.txt")
        cmds: list[tuple[list[str], dict[str, str]]] = []
        for idx, gpu in enumerate(gpu_parts):
            env = extend_pythonpath(os.environ.copy(), gpt_root)
            env.update(
                {
                    "inp_text": str(manifest),
                    "inp_wav_dir": "",
                    "exp_name": args.exp_name,
                    "opt_dir": str(exp_dir),
                    "bert_pretrained_dir": str(bert_pretrained_dir),
                    "i_part": str(idx),
                    "all_parts": str(len(gpu_parts)),
                    "_CUDA_VISIBLE_DEVICES": gpu,
                    "is_half": str(args.is_half),
                    "version": args.version,
                }
            )
            cmds.append(([sys.executable, "GPT_SoVITS/prepare_datasets/1-get-text.py"], env))
        run_parallel(cmds, gpt_root)
        merge_text_parts(exp_dir, len(gpu_parts))

    hubert_dir = exp_dir / "4-cnhubert"
    wav32_dir = exp_dir / "5-wav32k"
    if hubert_dir.exists() and wav32_dir.exists() and any(hubert_dir.glob("*.pt")) and any(wav32_dir.glob("*.wav")):
        print(f"[skip] hubert/wav32k features already exist under {exp_dir}")
    else:
        cmds = []
        for idx, gpu in enumerate(gpu_parts):
            env = extend_pythonpath(os.environ.copy(), gpt_root)
            env.update(
                {
                    "inp_text": str(manifest),
                    "inp_wav_dir": "",
                    "exp_name": args.exp_name,
                    "opt_dir": str(exp_dir),
                    "cnhubert_base_dir": str(cnhubert_base_dir),
                    "i_part": str(idx),
                    "all_parts": str(len(gpu_parts)),
                    "_CUDA_VISIBLE_DEVICES": gpu,
                    "is_half": str(args.is_half),
                }
            )
            cmds.append(([sys.executable, "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"], env))
        run_parallel(cmds, gpt_root)

    if args.skip_semantic:
        print("[done] skipped semantic extraction")
        return 0

    semantic_output = exp_dir / "6-name2semantic.tsv"
    if semantic_output.exists():
        print(f"[skip] semantic metadata already exists: {semantic_output}")
    else:
        for idx in range(len(gpu_parts)):
            remove_if_exists(exp_dir / f"6-name2semantic-{idx}.tsv")
        cmds = []
        for idx, gpu in enumerate(gpu_parts):
            env = extend_pythonpath(os.environ.copy(), gpt_root)
            env.update(
                {
                    "inp_text": str(manifest),
                    "exp_name": args.exp_name,
                    "opt_dir": str(exp_dir),
                    "pretrained_s2G": str(pretrained_s2g),
                    "s2config_path": str(defaults["s2_config"]),
                    "i_part": str(idx),
                    "all_parts": str(len(gpu_parts)),
                    "_CUDA_VISIBLE_DEVICES": gpu,
                    "is_half": str(args.is_half),
                }
            )
            cmds.append(([sys.executable, "GPT_SoVITS/prepare_datasets/3-get-semantic.py"], env))
        run_parallel(cmds, gpt_root)
        merge_semantic_parts(exp_dir, len(gpu_parts))

    print(f"[done] prepared dataset at {exp_dir}")
    print(f"[info] gpu groups used: {gpu_dash}")
    return 0


def load_yaml_module():
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for the training subcommands") from exc
    return yaml


def load_torch_module():
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is required for checkpoint export") from exc
    return torch


def train_sovits(args: argparse.Namespace) -> int:
    gpt_root = resolve_path(args.gpt_sovits_root)
    models_root = resolve_path(args.pretrained_root)
    defaults = gpt_sovits_defaults(gpt_root, models_root, args.version)
    exp_dir = gpt_root / "logs" / args.exp_name
    s2_resume_dir = exp_dir / f"logs_s2_{args.version}"

    require_exists(exp_dir / "2-name2text.txt", "phoneme metadata")
    require_exists(exp_dir / "6-name2semantic.tsv", "semantic metadata")

    pretrained_s2g = resolve_path(args.pretrained_s2g or defaults["pretrained_s2g"])
    pretrained_s2d = resolve_path(args.pretrained_s2d or defaults["pretrained_s2d"])
    require_exists(pretrained_s2g, "pretrained s2G")
    require_exists(pretrained_s2d, "pretrained s2D")

    base_config_path = defaults["s2_config"]
    require_exists(base_config_path, "SoVITS base config")
    config = json.loads(base_config_path.read_text(encoding="utf-8"))

    config["train"]["batch_size"] = args.batch_size
    config["train"]["epochs"] = args.epochs
    config["train"]["text_low_lr_rate"] = args.text_low_lr_rate
    config["train"]["pretrained_s2G"] = str(pretrained_s2g)
    config["train"]["pretrained_s2D"] = str(pretrained_s2d)
    config["train"]["if_save_latest"] = args.save_latest
    config["train"]["if_save_every_weights"] = args.save_every_weights
    config["train"]["save_every_epoch"] = args.save_every_epoch
    config["train"]["gpu_numbers"] = "-".join(parse_gpu_list(args.gpus))
    config["train"]["grad_ckpt"] = args.grad_ckpt
    config["train"]["fp16_run"] = args.is_half
    config["model"]["version"] = args.version
    config["data"]["exp_dir"] = str(exp_dir)
    config["s2_ckpt_dir"] = str(exp_dir)
    config["save_weight_dir"] = str(defaults["sovits_weight_dir"])
    config["name"] = args.exp_name
    config["version"] = args.version
    if args.lora_rank is not None:
        config["train"]["lora_rank"] = args.lora_rank

    ensure_dir(defaults["sovits_weight_dir"])
    ensure_dir(GENERATED_CONFIG_DIR)
    # Upstream s2_train.py saves checkpoints into logs/<exp>/logs_s2_<version>
    # but does not always create that directory before the first save.
    ensure_dir(s2_resume_dir)
    out_config = GENERATED_CONFIG_DIR / f"{args.exp_name}.s2.{args.version}.json"
    out_config.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    trainer = "GPT_SoVITS/s2_train.py" if args.version in {"v1", "v2", "v2Pro", "v2ProPlus"} else "GPT_SoVITS/s2_train_v3_lora.py"
    env = extend_pythonpath(os.environ.copy(), gpt_root)
    run_command([sys.executable, trainer, "--config", str(out_config)], gpt_root, env)

    print(f"[done] SoVITS training config written to {out_config}")
    return 0


def export_sovits(args: argparse.Namespace) -> int:
    torch = load_torch_module()
    gpt_root = resolve_path(args.gpt_sovits_root)
    models_root = resolve_path(args.pretrained_root)
    defaults = gpt_sovits_defaults(gpt_root, models_root, args.version)
    exp_dir = gpt_root / "logs" / args.exp_name
    ckpt_dir = exp_dir / f"logs_s2_{args.version}"
    checkpoint = ckpt_dir / args.checkpoint_name

    require_exists(checkpoint, "SoVITS checkpoint")

    config_candidates = [
        exp_dir / "config.json",
        GENERATED_CONFIG_DIR / f"{args.exp_name}.s2.{args.version}.json",
        defaults["s2_config"],
    ]
    config_path = next((path for path in config_candidates if path.exists()), None)
    if config_path is None:
        raise FileNotFoundError("No SoVITS config found for export")

    export_dir = resolve_path(args.output_dir or defaults["sovits_weight_dir"])
    ensure_dir(export_dir)

    data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    state_dict = data["model"]
    iteration = int(data.get("iteration", 0))
    export_name = args.output_name or f"{args.exp_name}_e{iteration}"
    export_path = export_dir / f"{export_name}.pth"

    config = json.loads(config_path.read_text(encoding="utf-8"))
    exported = OrderedDict()
    exported["weight"] = OrderedDict()
    for key, value in state_dict.items():
        if "enc_q" in key:
            continue
        exported["weight"][key] = value.half()
    exported["config"] = config
    exported["info"] = f"{iteration}epoch_exported_from_checkpoint"

    tmp_path = export_path.with_suffix(export_path.suffix + ".tmp")
    torch.save(exported, tmp_path)
    tmp_path.replace(export_path)

    print(f"[done] exported SoVITS weights to {export_path}")
    print(f"[info] source checkpoint: {checkpoint}")
    print(f"[info] embedded config: {config_path}")
    return 0


def train_gpt(args: argparse.Namespace) -> int:
    yaml = load_yaml_module()
    gpt_root = resolve_path(args.gpt_sovits_root)
    models_root = resolve_path(args.pretrained_root)
    defaults = gpt_sovits_defaults(gpt_root, models_root, args.version)
    exp_dir = gpt_root / "logs" / args.exp_name

    require_exists(exp_dir / "2-name2text.txt", "phoneme metadata")
    require_exists(exp_dir / "6-name2semantic.tsv", "semantic metadata")

    pretrained_s1 = resolve_path(args.pretrained_s1 or defaults["pretrained_s1"])
    require_exists(pretrained_s1, "pretrained s1")
    require_exists(defaults["s1_config"], "GPT base config")

    config = yaml.safe_load(defaults["s1_config"].read_text(encoding="utf-8"))
    config["train"]["batch_size"] = args.batch_size
    config["train"]["epochs"] = args.epochs
    config["train"]["save_every_n_epoch"] = args.save_every_epoch
    config["train"]["if_save_every_weights"] = args.save_every_weights
    config["train"]["if_save_latest"] = args.save_latest
    config["train"]["if_dpo"] = args.if_dpo
    config["train"]["half_weights_save_dir"] = str(defaults["gpt_weight_dir"])
    config["train"]["exp_name"] = args.exp_name
    config["pretrained_s1"] = str(pretrained_s1)
    config["train_semantic_path"] = str(exp_dir / "6-name2semantic.tsv")
    config["train_phoneme_path"] = str(exp_dir / "2-name2text.txt")
    config["output_dir"] = str(exp_dir / f"logs_s1_{args.version}")

    ensure_dir(defaults["gpt_weight_dir"])
    ensure_dir(GENERATED_CONFIG_DIR)
    out_config = GENERATED_CONFIG_DIR / f"{args.exp_name}.s1.{args.version}.yaml"
    out_config.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")

    env = extend_pythonpath(os.environ.copy(), gpt_root)
    env["_CUDA_VISIBLE_DEVICES"] = ",".join(parse_gpu_list(args.gpus))
    env["hz"] = "25hz"
    # PyTorch 2.6 changed torch.load() to default to weights_only=True.
    # Lightning's GPT training checkpoints in this repo are trusted local files
    # and may contain non-tensor metadata such as pathlib.PosixPath, so resuming
    # training needs the old full-checkpoint load behavior.
    env["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
    run_command([sys.executable, "GPT_SoVITS/s1_train.py", "--config_file", str(out_config)], gpt_root, env)

    print(f"[done] GPT training config written to {out_config}")
    return 0


def doctor(args: argparse.Namespace) -> int:
    gpt_root = resolve_path(args.gpt_sovits_root)
    models_root = resolve_path(args.pretrained_root)
    manifest = resolve_path(args.manifest)
    defaults = gpt_sovits_defaults(gpt_root, models_root, args.version)

    checks = [
        ("GPT-SoVITS root", gpt_root),
        ("pretrained root", models_root),
        ("manifest", manifest),
        ("BERT pretrained dir", defaults["bert_pretrained_dir"]),
        ("CNHubert dir", defaults["cnhubert_base_dir"]),
        ("pretrained s2G", defaults["pretrained_s2g"]),
        ("pretrained s2D", defaults["pretrained_s2d"]),
        ("pretrained s1", defaults["pretrained_s1"]),
    ]

    failed = False
    for label, path in checks:
        status = "OK" if path.exists() else "MISSING"
        print(f"{status:7} {label}: {path}")
        failed = failed or not path.exists()

    ffmpeg_path = shutil.which("ffmpeg")
    print(f"{'OK' if ffmpeg_path else 'WARN':7} ffmpeg: {ffmpeg_path or 'not found in PATH'}")

    try:
        gpu_output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            text=True,
        ).strip()
        print(f"OK      nvidia-smi: {gpu_output}")
    except Exception:
        print("WARN    nvidia-smi: unavailable")

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Thin wrappers around a local GPT-SoVITS checkout for character voice projects."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--gpt-sovits-root", default=DEFAULT_GPT_SOVITS_ROOT, help="Path to GPT-SoVITS root")
    common.add_argument(
        "--pretrained-root",
        default=DEFAULT_PRETRAINED_ROOT,
        help="Path to pretrained GPT-SoVITS weights",
    )
    common.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to the GPT-SoVITS .list manifest")
    common.add_argument("--version", default="v2", choices=sorted(VERSION_META), help="Base model version")
    common.add_argument("--exp-name", default="character_v2", help="Experiment name written into GPT-SoVITS/logs")
    common.add_argument("--gpus", default="0", help="GPU list such as '0' or '0-1'")

    prepare_parser = subparsers.add_parser("prepare", parents=[common], help="Run dataset preparation steps")
    prepare_parser.add_argument("--bert-pretrained-dir", default="", help="Override chinese-roberta-wwm-ext-large path")
    prepare_parser.add_argument("--cnhubert-base-dir", default="", help="Override chinese-hubert-base path")
    prepare_parser.add_argument("--pretrained-s2g", default="", help="Override pretrained s2G path")
    prepare_parser.add_argument("--is-half", type=strtobool, default=True, help="Use fp16 where GPT-SoVITS supports it")
    prepare_parser.add_argument("--force", action="store_true", help="Delete existing prepared artifacts before rerunning")
    prepare_parser.add_argument("--skip-semantic", action="store_true", help="Stop after text + hubert/wav32k extraction")
    prepare_parser.set_defaults(func=prepare)

    sovits_parser = subparsers.add_parser("train-sovits", parents=[common], help="Train the SoVITS stage")
    sovits_parser.add_argument("--batch-size", type=int, default=4)
    sovits_parser.add_argument("--epochs", type=int, default=16)
    sovits_parser.add_argument("--save-every-epoch", type=int, default=4)
    sovits_parser.add_argument("--text-low-lr-rate", type=float, default=0.4)
    sovits_parser.add_argument("--save-latest", type=strtobool, default=True)
    sovits_parser.add_argument("--save-every-weights", type=strtobool, default=True)
    sovits_parser.add_argument("--grad-ckpt", type=strtobool, default=False)
    sovits_parser.add_argument("--is-half", type=strtobool, default=True)
    sovits_parser.add_argument("--lora-rank", type=int, default=32)
    sovits_parser.add_argument("--pretrained-s2g", default="")
    sovits_parser.add_argument("--pretrained-s2d", default="")
    sovits_parser.set_defaults(func=train_sovits)

    export_sovits_parser = subparsers.add_parser(
        "export-sovits",
        parents=[common],
        help="Export an inference-ready SoVITS .pth from the latest training checkpoint",
    )
    export_sovits_parser.add_argument("--checkpoint-name", default="G_233333333333.pth")
    export_sovits_parser.add_argument("--output-dir", default="")
    export_sovits_parser.add_argument("--output-name", default="")
    export_sovits_parser.set_defaults(func=export_sovits)

    gpt_parser = subparsers.add_parser("train-gpt", parents=[common], help="Train the GPT stage")
    gpt_parser.add_argument("--batch-size", type=int, default=2)
    gpt_parser.add_argument("--epochs", type=int, default=12)
    gpt_parser.add_argument("--save-every-epoch", type=int, default=2)
    gpt_parser.add_argument("--save-latest", type=strtobool, default=True)
    gpt_parser.add_argument("--save-every-weights", type=strtobool, default=True)
    gpt_parser.add_argument("--if-dpo", type=strtobool, default=False)
    gpt_parser.add_argument("--pretrained-s1", default="")
    gpt_parser.set_defaults(func=train_gpt)

    doctor_parser = subparsers.add_parser("doctor", parents=[common], help="Check local prerequisites")
    doctor_parser.set_defaults(func=doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
