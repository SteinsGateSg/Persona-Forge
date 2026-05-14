#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import wave
from contextlib import closing
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASR_CSV = PROJECT_ROOT / "data" / "meta" / "transcripts.csv"
DEFAULT_WAV_DIR = PROJECT_ROOT / "data" / "raw" / "wav"
DEFAULT_OUTPUT_LIST = PROJECT_ROOT / "artifacts" / "manifests" / "train.list"
DEFAULT_STATS_JSON = PROJECT_ROOT / "artifacts" / "manifests" / "train.stats.json"
DEFAULT_REJECTS_CSV = PROJECT_ROOT / "artifacts" / "manifests" / "train.rejects.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a GPT-SoVITS .list manifest from a transcript CSV."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_ASR_CSV, help="Path to the transcript CSV")
    parser.add_argument("--wav-dir", type=Path, default=DEFAULT_WAV_DIR, help="Directory with WAV files")
    parser.add_argument(
        "--output-list",
        type=Path,
        default=DEFAULT_OUTPUT_LIST,
        help="Output GPT-SoVITS manifest (.list)",
    )
    parser.add_argument(
        "--stats-json",
        type=Path,
        default=DEFAULT_STATS_JSON,
        help="Output dataset statistics JSON",
    )
    parser.add_argument(
        "--rejects-csv",
        type=Path,
        default=DEFAULT_REJECTS_CSV,
        help="Output CSV for filtered-out rows",
    )
    parser.add_argument("--audio-column", default="voice_file", help="CSV column name for the audio filename")
    parser.add_argument("--text-column", default="asr_text", help="CSV column name for the transcript text")
    parser.add_argument("--ext-from", default=".OGG", help="Replace this source suffix in audio filenames")
    parser.add_argument("--ext-to", default=".wav", help="Target suffix to use for audio filenames")
    parser.add_argument("--speaker", default="speaker_0", help="Speaker name written into the manifest")
    parser.add_argument("--language", default="ja", help="Language tag for GPT-SoVITS")
    parser.add_argument("--min-sec", type=float, default=1.0, help="Reject clips shorter than this")
    parser.add_argument(
        "--max-sec",
        type=float,
        default=12.0,
        help="Reject clips longer than this. Set <= 0 to disable.",
    )
    return parser.parse_args(argv)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("|", "、")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_duration_seconds(wav_path: Path) -> float:
    with closing(wave.open(str(wav_path), "rb")) as handle:
        frames = handle.getnframes()
        sample_rate = handle.getframerate()
    return frames / float(sample_rate)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    max_sec = None if args.max_sec <= 0 else args.max_sec

    if args.min_sec < 0:
        raise ValueError("--min-sec must be >= 0")

    if not args.csv.exists():
        raise FileNotFoundError(args.csv)
    if not args.wav_dir.exists():
        raise FileNotFoundError(args.wav_dir)

    kept_lines: list[str] = []
    rejects: list[dict[str, str]] = []

    total_rows = 0
    total_duration_sec = 0.0
    kept_duration_sec = 0.0

    with args.csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_rows += 1
            voice_file = (row.get(args.audio_column) or "").strip()
            text = normalize_text(row.get(args.text_column) or "")
            wav_name = voice_file
            if args.ext_from:
                wav_name = wav_name.replace(args.ext_from, args.ext_to)
            wav_path = args.wav_dir / wav_name

            reject_reason = ""
            duration = 0.0

            if not voice_file:
                reject_reason = "missing_voice_file"
            elif not wav_path.exists():
                reject_reason = "missing_wav"
            elif not text:
                reject_reason = "empty_text"
            else:
                duration = get_duration_seconds(wav_path)
                total_duration_sec += duration
                if duration < args.min_sec:
                    reject_reason = "too_short"
                elif max_sec is not None and duration > max_sec:
                    reject_reason = "too_long"

            if reject_reason:
                rejects.append(
                    {
                        "voice_file": voice_file,
                        "wav_path": str(wav_path),
                        "duration_sec": f"{duration:.3f}",
                        "reason": reject_reason,
                        "text": text,
                    }
                )
                continue

            kept_duration_sec += duration
            kept_lines.append(f"{wav_path.resolve()}|{args.speaker}|{args.language}|{text}")

    stats = {
        "input_csv": str(args.csv.resolve()),
        "wav_dir": str(args.wav_dir.resolve()),
        "audio_column": args.audio_column,
        "text_column": args.text_column,
        "speaker": args.speaker,
        "language": args.language,
        "rows_total": total_rows,
        "rows_kept": len(kept_lines),
        "rows_rejected": len(rejects),
        "min_sec": args.min_sec,
        "max_sec": max_sec,
        "hours_total": round(total_duration_sec / 3600, 3),
        "hours_kept": round(kept_duration_sec / 3600, 3),
    }

    for path in (args.output_list, args.stats_json, args.rejects_csv):
        ensure_parent(path)

    args.output_list.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")

    with args.rejects_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["voice_file", "wav_path", "duration_sec", "reason", "text"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rejects)

    args.stats_json.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
