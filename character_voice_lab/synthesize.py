from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .gpt_sovits import (
    DEFAULT_GPT_SOVITS_ROOT,
    ensure_dir,
    extend_pythonpath,
    require_exists,
    resolve_path,
    run_command,
)


REF_LANGUAGE_CHOICES = ["中文", "英文", "日文"]
TARGET_LANGUAGE_CHOICES = ["中文", "英文", "日文", "中英混合", "日英混合", "多语种混合"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GPT-SoVITS inference for a trained character voice.")
    parser.add_argument("--gpt-sovits-root", default=DEFAULT_GPT_SOVITS_ROOT, help="Path to GPT-SoVITS root")
    parser.add_argument("--gpt-model", required=True, help="Path to the GPT inference checkpoint")
    parser.add_argument("--sovits-model", required=True, help="Path to the SoVITS inference weights")
    parser.add_argument("--ref-audio", required=True, help="Path to the reference audio clip")

    ref_group = parser.add_mutually_exclusive_group(required=True)
    ref_group.add_argument("--ref-text-file", help="Path to the reference text file")
    ref_group.add_argument("--ref-text", help="Reference text content")

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target-text-file", help="Path to the target text file")
    target_group.add_argument("--target-text", help="Target text content")

    parser.add_argument("--ref-language", required=True, choices=REF_LANGUAGE_CHOICES)
    parser.add_argument("--target-language", required=True, choices=TARGET_LANGUAGE_CHOICES)
    parser.add_argument("--output-dir", required=True, help="Directory to store synthesis outputs")
    return parser.parse_args(argv)


def materialize_text(path: str | None, text: str | None, output_dir: Path, filename: str) -> Path:
    if path:
        resolved = resolve_path(path)
        require_exists(resolved, filename)
        return resolved
    assert text is not None
    ensure_dir(output_dir)
    temp_path = output_dir / filename
    temp_path.write_text(text.strip() + "\n", encoding="utf-8")
    return temp_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    gpt_root = resolve_path(args.gpt_sovits_root)
    gpt_model = resolve_path(args.gpt_model)
    sovits_model = resolve_path(args.sovits_model)
    ref_audio = resolve_path(args.ref_audio)
    output_dir = resolve_path(args.output_dir)

    require_exists(gpt_root, "GPT-SoVITS root")
    require_exists(gpt_model, "GPT model")
    require_exists(sovits_model, "SoVITS model")
    require_exists(ref_audio, "reference audio")
    ensure_dir(output_dir)

    ref_text_path = materialize_text(args.ref_text_file, args.ref_text, output_dir, "reference.txt")
    target_text_path = materialize_text(args.target_text_file, args.target_text, output_dir, "target.txt")

    env = extend_pythonpath(os.environ.copy(), gpt_root)

    cmd = [
        sys.executable,
        "-m",
        "GPT_SoVITS.inference_cli",
        "--gpt_model",
        str(gpt_model),
        "--sovits_model",
        str(sovits_model),
        "--ref_audio",
        str(ref_audio),
        "--ref_text",
        str(ref_text_path),
        "--ref_language",
        args.ref_language,
        "--target_text",
        str(target_text_path),
        "--target_language",
        args.target_language,
        "--output_path",
        str(output_dir),
    ]
    run_command(cmd, gpt_root, env)
    print(f"[done] synthesized audio under {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
