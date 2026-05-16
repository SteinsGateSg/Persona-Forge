from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
import urllib.error
from dataclasses import asdict, dataclass
from pathlib import Path

from .reference_bank import RETRYABLE_API_ERRORS, extract_json_payload, post_chat_completion


DEFAULT_API_BASE = os.environ.get("SELECTOR_API_BASE", "").strip()
DEFAULT_MODEL = os.environ.get("SELECTOR_MODEL", "").strip()
DEFAULT_API_KEY_ENV = "SELECTOR_API_KEY"
DEFAULT_TOP_K = 5


@dataclass
class ReferenceItem:
    emotion: str
    rank: int
    sample_id: str
    wav_path: str
    text_path: str
    duration_sec: float
    reference_score: int
    intensity: int
    text: str
    reason: str


@dataclass
class StylePlan:
    emotion: str
    intensity: int
    pace: str
    confidence: float
    reason: str
    alternate_emotions: list[str]
    backend: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a reference clip from an emotion-labeled reference bank."
    )
    parser.add_argument("--refs-index", required=True, help="Path to refs/index.csv")
    parser.add_argument(
        "--asset-root",
        default="",
        help="Optional project root used to resolve relative wav/text paths in output metadata",
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target-text", help="Target text content")
    target_group.add_argument("--target-text-file", help="Path to target text file")
    parser.add_argument("--target-language", default="日文", help="Target language label for planning context")
    parser.add_argument("--backend", choices=["api", "heuristic", "local"], default="heuristic")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="OpenAI-compatible base URL")
    parser.add_argument("--api-key", default="", help="API key; falls back to env vars")
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV, help="Primary environment variable name for API key lookup")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="API model name")
    parser.add_argument("--local-model", default="", help="Reserved local-model path placeholder for future use")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="How many candidates to return")
    parser.add_argument("--format", choices=["json", "ref-id", "shell"], default="json")
    parser.add_argument("--max-retries", type=int, default=3, help="API retry count")
    parser.add_argument("--sleep", type=float, default=1.5, help="Seconds to wait between API retries")
    return parser.parse_args(argv)


def resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    env_names = [args.api_key_env, "EMOTION_API_KEY", "OPENAI_API_KEY", "DASHSCOPE_API_KEY"]
    for env_name in env_names:
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def read_target_text(args: argparse.Namespace) -> str:
    if args.target_text:
        return args.target_text.strip()
    assert args.target_text_file
    return Path(args.target_text_file).expanduser().read_text(encoding="utf-8").strip()


def load_reference_bank(index_path: Path) -> list[ReferenceItem]:
    items: list[ReferenceItem] = []
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            items.append(
                ReferenceItem(
                    emotion=row["emotion"].strip(),
                    rank=int(row["rank"]),
                    sample_id=row["sample_id"].strip(),
                    wav_path=row["wav_path"].strip(),
                    text_path=row["text_path"].strip(),
                    duration_sec=float(row["duration_sec"]),
                    reference_score=int(row["reference_score"]),
                    intensity=int(row["intensity"]),
                    text=row["text"].strip(),
                    reason=row.get("reason", "").strip(),
                )
            )
    if not items:
        raise ValueError(f"No reference items found in {index_path}")
    return items


def build_api_messages(target_text: str, target_language: str, labels: list[str]) -> list[dict[str, str]]:
    instructions = f"""
You are selecting the speaking style for a character-voice reference bank.
Return strict JSON only:
{{
  "emotion": "one of {labels}",
  "intensity": 1,
  "pace": "slow|medium|fast",
  "confidence": 0.0,
  "reason": "short explanation",
  "alternate_emotions": ["optional secondary labels"]
}}

Rules:
- Choose exactly one primary emotion from the provided label list.
- intensity must be 1-5.
- confidence must be 0.0-1.0.
- pace must be one of slow, medium, fast.
- Keep reason short and concrete.
"""
    user_payload = {
        "target_language": target_language,
        "target_text": target_text,
        "available_emotions": labels,
    }
    return [
        {"role": "system", "content": "You are a careful prosody planner for character voice synthesis."},
        {"role": "user", "content": instructions + "\n\n" + json.dumps(user_payload, ensure_ascii=False, indent=2)},
    ]


def clamp_intensity(raw: object) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, value))


def clamp_confidence(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, value))


def normalize_pace(raw: object) -> str:
    value = str(raw or "").strip().lower()
    if value in {"slow", "medium", "fast"}:
        return value
    return "medium"


def normalize_emotion(raw: object, labels: list[str]) -> str:
    value = str(raw or "").strip().lower()
    if value in labels:
        return value
    return "neutral" if "neutral" in labels else labels[0]


def parse_plan(payload: dict, labels: list[str], backend: str) -> StylePlan:
    alt = [
        normalize_emotion(item, labels)
        for item in payload.get("alternate_emotions", [])
        if normalize_emotion(item, labels) != normalize_emotion(payload.get("emotion"), labels)
    ]
    return StylePlan(
        emotion=normalize_emotion(payload.get("emotion"), labels),
        intensity=clamp_intensity(payload.get("intensity")),
        pace=normalize_pace(payload.get("pace")),
        confidence=clamp_confidence(payload.get("confidence")),
        reason=str(payload.get("reason", "")).strip() or "No reason provided.",
        alternate_emotions=list(dict.fromkeys(alt)),
        backend=backend,
    )


def plan_with_api(args: argparse.Namespace, target_text: str, labels: list[str]) -> StylePlan:
    if not args.api_base:
        raise ValueError("API backend selected but --api-base is empty.")
    if not args.model:
        raise ValueError("API backend selected but --model is empty.")
    api_key = resolve_api_key(args)
    if not api_key:
        raise ValueError(
            f"API backend selected but no API key found. Set --api-key or env {args.api_key_env}."
        )

    messages = build_api_messages(target_text, args.target_language, labels)
    last_error: Exception | None = None
    for attempt in range(1, args.max_retries + 1):
        try:
            content = post_chat_completion(args.api_base, api_key, args.model, messages)
            payload = extract_json_payload(content)
            return parse_plan(payload, labels, "api")
        except RETRYABLE_API_ERRORS as exc:
            last_error = exc
            if attempt == args.max_retries:
                break
            time.sleep(args.sleep * attempt)
    assert last_error is not None
    raise last_error


def heuristic_emotion(text: str, labels: list[str]) -> tuple[str, int, str, list[str]]:
    lowered = text.strip().lower()

    patterns = [
        ("sad", [r"悲しい", r"行かないで", r"やだ", r"寂しい", r"cry", r"miss you", r"难过", r"别走"], 4, "slow", ["gentle"]),
        ("gentle", [r"大好き", r"元気出して", r"お帰り", r"どうした", r"please", r"gentle", r"亲爱的", r"好久不见"], 3, "slow", ["neutral"]),
        ("excited", [r"!+", r"わあ", r"すごい", r"じゃんじゃん", r"amazing", r"excited", r"太棒", r"哇"], 4, "fast", ["happy"]),
        ("happy", [r"幸せ", r"かわいい", r"えへへ", r"happy", r"love", r"开心", r"可爱"], 4, "medium", ["gentle"]),
        ("teasing", [r"へへ", r"胡散臭い", r"だめだよ", r"tease", r"逗", r"坏"], 3, "medium", ["neutral"]),
        ("worried", [r"大丈夫", r"心配", r"どうする", r"worried", r"担心"], 3, "medium", ["gentle"]),
        ("serious", [r"第三次世界大戦", r"しないで", r"must", r"should", r"serious", r"重要", r"必须"], 4, "medium", ["neutral"]),
        ("embarrassed", [r"恥ずかしい", r"あうう", r"embarrass", r"害羞"], 3, "medium", ["gentle"]),
    ]

    for emotion, regexes, intensity, pace, alternates in patterns:
        if emotion not in labels:
            continue
        if any(re.search(regex, lowered, re.I) for regex in regexes):
            return emotion, intensity, pace, alternates

    if "?" in text or "？" in text:
        fallback = "gentle" if "gentle" in labels else labels[0]
        return fallback, 2, "medium", ["neutral"] if "neutral" in labels else []

    fallback = "neutral" if "neutral" in labels else labels[0]
    return fallback, 2, "medium", []


def plan_with_heuristic(target_text: str, labels: list[str]) -> StylePlan:
    emotion, intensity, pace, alternates = heuristic_emotion(target_text, labels)
    return StylePlan(
        emotion=emotion,
        intensity=intensity,
        pace=pace,
        confidence=0.42,
        reason="Selected by built-in heuristic rules.",
        alternate_emotions=alternates,
        backend="heuristic",
    )


def plan_with_local_model(args: argparse.Namespace, labels: list[str]) -> StylePlan:
    raise NotImplementedError(
        "Local selector backend is reserved but not implemented yet. Use --backend api or --backend heuristic."
    )


def preferred_duration(pace: str) -> float:
    if pace == "slow":
        return 5.6
    if pace == "fast":
        return 3.9
    return 4.7


def score_reference(item: ReferenceItem, plan: StylePlan) -> float:
    score = 0.0
    if item.emotion == plan.emotion:
        score += 50.0
    elif item.emotion in plan.alternate_emotions:
        score += 30.0
    elif item.emotion == "neutral":
        score += 10.0

    score += max(0.0, 20.0 - abs(item.intensity - plan.intensity) * 5.0)
    score += item.reference_score * 5.0
    score += max(0.0, 8.0 - (item.rank - 1) * 1.5)
    score += max(0.0, 8.0 - abs(item.duration_sec - preferred_duration(plan.pace)) * 2.2)
    return score


def select_references(items: list[ReferenceItem], plan: StylePlan, top_k: int) -> list[dict]:
    ranked = []
    for item in items:
        ranked.append(
            {
                "sample_id": item.sample_id,
                "emotion": item.emotion,
                "rank": item.rank,
                "intensity": item.intensity,
                "reference_score": item.reference_score,
                "duration_sec": item.duration_sec,
                "wav_path": item.wav_path,
                "text_path": item.text_path,
                "text": item.text,
                "reason": item.reason,
                "selector_score": round(score_reference(item, plan), 3),
            }
        )
    ranked.sort(key=lambda record: (-record["selector_score"], record["rank"], record["sample_id"]))
    return ranked[: max(1, top_k)]


def maybe_resolve_asset_paths(records: list[dict], asset_root: Path | None) -> list[dict]:
    if asset_root is None:
        return records
    resolved = []
    for record in records:
        updated = dict(record)
        updated["wav_abspath"] = str((asset_root / record["wav_path"]).resolve())
        updated["text_abspath"] = str((asset_root / record["text_path"]).resolve())
        resolved.append(updated)
    return resolved


def emit_result(args: argparse.Namespace, result: dict) -> int:
    selection = result["selection"]
    if args.format == "ref-id":
        print(selection["sample_id"])
        return 0
    if args.format == "shell":
        print(f'REF_ID="{selection["sample_id"]}"')
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    refs_index = Path(args.refs_index).expanduser().resolve()
    asset_root = Path(args.asset_root).expanduser().resolve() if args.asset_root else None
    target_text = read_target_text(args)
    items = load_reference_bank(refs_index)
    labels = sorted({item.emotion for item in items})

    if args.backend == "api":
        plan = plan_with_api(args, target_text, labels)
    elif args.backend == "local":
        plan = plan_with_local_model(args, labels)
    else:
        plan = plan_with_heuristic(target_text, labels)

    top_candidates = maybe_resolve_asset_paths(select_references(items, plan, args.top_k), asset_root)
    result = {
        "target_text": target_text,
        "target_language": args.target_language,
        "plan": asdict(plan),
        "selection": top_candidates[0],
        "alternatives": top_candidates[1:],
        "labels": labels,
    }
    return emit_result(args, result)


if __name__ == "__main__":
    raise SystemExit(main())
