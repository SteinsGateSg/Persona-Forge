#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import http.client
import json
import math
import os
import re
import subprocess
import sys
import ssl
import time
import urllib.error
import urllib.request
import wave
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "artifacts" / "manifests" / "train.list"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "reference_bank"

DEFAULT_LABELS = [
    "neutral",
    "gentle",
    "happy",
    "excited",
    "worried",
    "sad",
    "teasing",
    "embarrassed",
    "serious",
    "other",
]


@dataclass
class Sample:
    sample_id: str
    wav_path: Path
    speaker: str
    language: str
    text: str
    duration_sec: float


class QuotaExhaustedError(RuntimeError):
    pass


class TeeWriter:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


@contextmanager
def tee_output(log_path: Path | None):
    if log_path is None:
        yield
        return

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        stdout_tee = TeeWriter(sys.stdout, log_file)
        stderr_tee = TeeWriter(sys.stderr, log_file)
        with redirect_stdout(stdout_tee), redirect_stderr(stderr_tee):
            yield


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Label emotion and reference suitability for training clips using an OpenAI-compatible API."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to GPT-SoVITS .list manifest")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for output metadata files")
    parser.add_argument("--api-base", default=os.environ.get("EMOTION_API_BASE", "").strip(), help="OpenAI-compatible base URL, e.g. https://dashscope.aliyuncs.com/compatible-mode/v1")
    parser.add_argument("--api-key", default="", help="API key. Falls back to EMOTION_API_KEY / QWEN_API_KEY / DASHSCOPE_API_KEY / OPENAI_API_KEY")
    parser.add_argument("--model", default=os.environ.get("EMOTION_MODEL", "").strip(), help="Model name, e.g. the Qwen model available in your account")
    parser.add_argument("--batch-size", type=int, default=12, help="Number of clips per API request")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N samples after filtering")
    parser.add_argument("--offset", type=int, default=0, help="Skip the first N samples")
    parser.add_argument("--resume", action="store_true", help="Resume from existing JSONL output if present")
    parser.add_argument("--top-per-emotion", type=int, default=5, help="How many top candidates per emotion to include in the shortlist CSV")
    parser.add_argument("--min-ref-sec", type=float, default=2.0, help="Minimum duration considered suitable for reference audio")
    parser.add_argument("--max-ref-sec", type=float, default=8.0, help="Maximum duration considered suitable for reference audio")
    parser.add_argument("--labels", default=",".join(DEFAULT_LABELS), help="Comma-separated emotion label set")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum API retries per batch")
    parser.add_argument("--sleep", type=float, default=1.5, help="Seconds to sleep between retry attempts")
    parser.add_argument("--log-file", default="", help="Optional log file path. Stdout/stderr will be appended to this file.")
    parser.add_argument("--shutdown-cmd", default="", help="Optional shell command to run after the script exits, e.g. /mnt/c/Windows/System32/shutdown.exe /s /t 60")
    parser.add_argument("--dry-run", action="store_true", help="Do not call the API; only print dataset summary")
    return parser.parse_args(argv)


def resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    for env_name in ("EMOTION_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def read_wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
    return frames / rate


def read_manifest(manifest_path: Path) -> list[Sample]:
    samples: list[Sample] = []
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        for index, raw_line in enumerate(manifest_file):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) != 4:
                raise ValueError(f"Invalid manifest line {index + 1}: {line}")
            wav_path_str, speaker, language, text = parts
            wav_path = Path(wav_path_str)
            sample_id = wav_path.stem
            samples.append(
                Sample(
                    sample_id=sample_id,
                    wav_path=wav_path,
                    speaker=speaker,
                    language=language,
                    text=text,
                    duration_sec=read_wav_duration(wav_path),
                )
            )
    return samples


def load_existing_ids(jsonl_path: Path) -> set[str]:
    if not jsonl_path.exists():
        return set()
    done_ids: set[str] = set()
    with jsonl_path.open("r", encoding="utf-8") as jsonl_file:
        for line in jsonl_file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            sample_id = str(record.get("sample_id", "")).strip()
            if sample_id:
                done_ids.add(sample_id)
    return done_ids


def batched(items: list[Sample], batch_size: int) -> list[list[Sample]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def build_prompt(samples: list[Sample], labels: list[str], min_ref_sec: float, max_ref_sec: float) -> list[dict[str, str]]:
    label_text = ", ".join(labels)
    criteria = (
        "你在为单角色语音系统筛选参考音频候选。"
        "你只能根据文本内容和时长做初筛，不能判断真实录音里的噪声、重叠说话或演技细节。"
        "请对每条样本输出结构化 JSON。"
    )
    instructions = f"""
输出一个 JSON 对象，格式必须是：
{{
  "items": [
    {{
      "sample_id": "MAY_0000",
      "primary_emotion": "从 [{label_text}] 中选一个",
      "secondary_emotions": ["可空数组"],
      "intensity": 1,
      "reference_score": 1,
      "is_reference_candidate": true,
      "reason": "一句简短中文说明",
      "notes": "可选，简短中文备注"
    }}
  ]
}}

判定标准：
1. `primary_emotion` 必须从给定标签中选一个。
2. `intensity` 取 1-5，越大表示情绪越明显。
3. `reference_score` 取 1-5，越大表示越适合作为推理参考音频。
4. `is_reference_candidate` 只有在文本完整、情绪比较明确、适合单句参考时才给 true。
5. 时长建议区间是 {min_ref_sec:.1f}-{max_ref_sec:.1f} 秒，明显太短或太长应降低 `reference_score`。
6. 对于上下文依赖强、像残句、旁白、信息不完整的句子，应降低 `reference_score`。
7. 只输出 JSON，不要输出解释文字，不要用 Markdown 代码块。
"""
    items = []
    for sample in samples:
        items.append(
            {
                "sample_id": sample.sample_id,
                "text": sample.text,
                "duration_sec": round(sample.duration_sec, 3),
                "language": sample.language,
            }
        )

    return [
        {"role": "system", "content": criteria},
        {"role": "user", "content": instructions + "\n\n待标注样本：\n" + json.dumps(items, ensure_ascii=False, indent=2)},
    ]


def post_chat_completion(api_base: str, api_key: str, model: str, messages: list[dict[str, str]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "top_p": 0.9,
    }
    url = api_base.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = getattr(exc, "code", None)
        lowered = body.lower()
        quota_markers = (
            "insufficient_quota",
            "quota_exceeded",
            "quota",
            "bill exhausted",
            "balance",
            "额度",
            "余量",
            "欠费",
            "用完",
            "exhausted",
        )
        if status in (402, 403, 429) and any(marker in lowered for marker in quota_markers):
            raise QuotaExhaustedError(f"Quota exhausted for model {model}: HTTP {status} {body}") from exc
        raise urllib.error.HTTPError(exc.url, exc.code, f"{exc.reason}: {body}", exc.hdrs, exc.fp) from exc
    data = json.loads(body)
    return data["choices"][0]["message"]["content"]


RETRYABLE_API_ERRORS = (
    urllib.error.URLError,
    urllib.error.HTTPError,
    TimeoutError,
    ConnectionResetError,
    ConnectionAbortedError,
    http.client.RemoteDisconnected,
    ssl.SSLError,
)


def extract_json_payload(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if match:
            text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.S)
        if not match:
            raise
        return json.loads(match.group(1))


def normalize_item(raw_item: dict, sample_index: dict[str, Sample], labels: set[str], min_ref_sec: float, max_ref_sec: float) -> dict:
    sample_id = str(raw_item.get("sample_id", "")).strip()
    if sample_id not in sample_index:
        raise ValueError(f"Unknown sample_id returned by model: {sample_id}")
    sample = sample_index[sample_id]

    primary_emotion = str(raw_item.get("primary_emotion", "other")).strip().lower()
    if primary_emotion not in labels:
        primary_emotion = "other"

    secondary_emotions = raw_item.get("secondary_emotions", [])
    if not isinstance(secondary_emotions, list):
        secondary_emotions = []
    secondary_emotions = [str(item).strip().lower() for item in secondary_emotions if str(item).strip()]
    secondary_emotions = [item for item in secondary_emotions if item in labels and item != primary_emotion]

    intensity = raw_item.get("intensity", 1)
    reference_score = raw_item.get("reference_score", 1)
    try:
        intensity = max(1, min(5, int(intensity)))
    except Exception:
        intensity = 1
    try:
        reference_score = max(1, min(5, int(reference_score)))
    except Exception:
        reference_score = 1

    duration_ok = min_ref_sec <= sample.duration_sec <= max_ref_sec
    is_candidate = bool(raw_item.get("is_reference_candidate", False))
    if not duration_ok and reference_score >= 4:
        reference_score = 3
    if not duration_ok:
        is_candidate = False

    reason = str(raw_item.get("reason", "")).strip()
    notes = str(raw_item.get("notes", "")).strip()

    return {
        "sample_id": sample.sample_id,
        "wav_path": str(sample.wav_path),
        "text": sample.text,
        "language": sample.language,
        "duration_sec": round(sample.duration_sec, 3),
        "primary_emotion": primary_emotion,
        "secondary_emotions": secondary_emotions,
        "intensity": intensity,
        "reference_score": reference_score,
        "is_reference_candidate": is_candidate,
        "reason": reason,
        "notes": notes,
    }


def write_jsonl(path: Path, records: list[dict], mode: str = "w") -> None:
    with path.open(mode, encoding="utf-8") as jsonl_file:
        for record in records:
            jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict]) -> None:
    fieldnames = [
        "sample_id",
        "wav_path",
        "text",
        "language",
        "duration_sec",
        "primary_emotion",
        "secondary_emotions",
        "intensity",
        "reference_score",
        "is_reference_candidate",
        "reason",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["secondary_emotions"] = ",".join(row["secondary_emotions"])
            writer.writerow(row)


def build_shortlist(records: list[dict], top_per_emotion: int) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for record in records:
        if not record["is_reference_candidate"]:
            continue
        grouped.setdefault(record["primary_emotion"], []).append(record)

    shortlist: list[dict] = []
    for emotion, items in sorted(grouped.items()):
        items.sort(
            key=lambda item: (
                -item["reference_score"],
                -item["intensity"],
                abs(item["duration_sec"] - 4.5),
                item["sample_id"],
            )
        )
        for rank, item in enumerate(items[:top_per_emotion], start=1):
            shortlist.append(
                {
                    "emotion": emotion,
                    "rank": rank,
                    "sample_id": item["sample_id"],
                    "wav_path": item["wav_path"],
                    "duration_sec": item["duration_sec"],
                    "reference_score": item["reference_score"],
                    "intensity": item["intensity"],
                    "text": item["text"],
                    "reason": item["reason"],
                }
            )
    return shortlist


def write_shortlist_csv(path: Path, records: list[dict]) -> None:
    fieldnames = ["emotion", "rank", "sample_id", "wav_path", "duration_sec", "reference_score", "intensity", "text", "reason"]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_summary(path: Path, records: list[dict], total_samples: int, labels: list[str]) -> None:
    emotion_counts = {label: 0 for label in labels}
    candidate_counts = {label: 0 for label in labels}
    for record in records:
        emotion = record["primary_emotion"]
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        if record["is_reference_candidate"]:
            candidate_counts[emotion] = candidate_counts.get(emotion, 0) + 1

    summary = {
        "total_samples": total_samples,
        "labeled_samples": len(records),
        "emotion_counts": emotion_counts,
        "reference_candidate_counts": candidate_counts,
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_main(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    labels = [label.strip().lower() for label in args.labels.split(",") if label.strip()]
    label_set = set(labels)

    samples = read_manifest(manifest_path)
    samples = samples[args.offset :]
    if args.limit > 0:
        samples = samples[: args.limit]

    jsonl_path = output_dir / "emotion_labels.jsonl"
    csv_path = output_dir / "emotion_labels.csv"
    shortlist_path = output_dir / "reference_shortlist.csv"
    summary_path = output_dir / "emotion_summary.json"

    done_ids: set[str] = set()
    if args.resume:
        done_ids = load_existing_ids(jsonl_path)
        samples = [sample for sample in samples if sample.sample_id not in done_ids]

    print(f"manifest: {manifest_path}")
    print(f"output_dir: {output_dir}")
    print(f"samples_to_process: {len(samples)}")
    print(f"labels: {', '.join(labels)}")

    if args.dry_run:
        return 0

    api_base = args.api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key = resolve_api_key(args)
    model = args.model.strip()
    if not api_key:
        raise SystemExit("Missing API key. Set --api-key or EMOTION_API_KEY / QWEN_API_KEY / DASHSCOPE_API_KEY.")
    if not model:
        raise SystemExit("Missing model name. Set --model or EMOTION_MODEL.")

    mode = "a" if args.resume and jsonl_path.exists() else "w"
    sample_index = {sample.sample_id: sample for sample in read_manifest(manifest_path)}

    all_records: list[dict] = []
    if args.resume and jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as existing_file:
            for line in existing_file:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))

    quota_exhausted_message = ""
    stopped_early = False

    for batch_no, batch in enumerate(batched(samples, args.batch_size), start=1):
        messages = build_prompt(batch, labels, args.min_ref_sec, args.max_ref_sec)
        for attempt in range(1, args.max_retries + 1):
            try:
                content = post_chat_completion(api_base, api_key, model, messages)
                payload = extract_json_payload(content)
                raw_items = payload.get("items", [])
                if not isinstance(raw_items, list):
                    raise ValueError("Response JSON does not contain an 'items' list")
                records = [
                    normalize_item(item, sample_index, label_set, args.min_ref_sec, args.max_ref_sec)
                    for item in raw_items
                ]
                returned_ids = {record["sample_id"] for record in records}
                expected_ids = {sample.sample_id for sample in batch}
                missing_ids = expected_ids - returned_ids
                if missing_ids:
                    raise ValueError(f"Model response missing sample ids: {sorted(missing_ids)}")
                write_jsonl(jsonl_path, records, mode=mode)
                mode = "a"
                all_records.extend(records)
                print(f"batch {batch_no}: labeled {len(records)} samples")
                break
            except QuotaExhaustedError as exc:
                quota_exhausted_message = str(exc)
                print(f"[stop] {quota_exhausted_message}")
                stopped_early = True
                break
            except RETRYABLE_API_ERRORS + (ValueError, json.JSONDecodeError) as exc:
                if attempt >= args.max_retries:
                    raise
                wait_sec = args.sleep * attempt
                print(f"batch {batch_no}: retry {attempt}/{args.max_retries} after error: {exc} (sleep {wait_sec:.1f}s)")
                time.sleep(wait_sec)
        if stopped_early:
            break

    all_records.sort(key=lambda record: record["sample_id"])
    write_csv(csv_path, all_records)
    shortlist = build_shortlist(all_records, args.top_per_emotion)
    write_shortlist_csv(shortlist_path, shortlist)
    write_summary(summary_path, all_records, len(all_records), labels)

    if stopped_early:
        print("[stopped] labeling paused because model quota appears exhausted")
    print(f"[done] jsonl: {jsonl_path}")
    print(f"[done] csv: {csv_path}")
    print(f"[done] shortlist: {shortlist_path}")
    print(f"[done] summary: {summary_path}")
    return 0


def run_shutdown_command(command: str) -> None:
    command = command.strip()
    if not command:
        return
    print(f"[shutdown] running: {command}")
    subprocess.run(command, shell=True, check=False)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_path = Path(args.log_file).expanduser().resolve() if args.log_file.strip() else None
    exit_code = 0
    try:
        with tee_output(log_path):
            exit_code = run_main(args)
    finally:
        run_shutdown_command(args.shutdown_cmd)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
