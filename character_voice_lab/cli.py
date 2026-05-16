from __future__ import annotations

import sys

from . import __version__
from . import gpt_sovits, manifest, reference_bank, selector, synthesize


TOP_LEVEL_HELP = """persona-forge

Usage:
  persona-forge build-manifest [args...]
  persona-forge label-emotions [args...]
  persona-forge select-reference [args...]
  persona-forge prepare [args...]
  persona-forge train-sovits [args...]
  persona-forge export-sovits [args...]
  persona-forge train-gpt [args...]
  persona-forge doctor [args...]
  persona-forge synthesize [args...]
  persona-forge --version

Compatibility alias:
  character-voice-lab ...
"""


GPT_SOVITS_COMMANDS = {"prepare", "train-sovits", "export-sovits", "train-gpt", "doctor"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print(TOP_LEVEL_HELP.strip())
        return 0
    if args[0] in {"-V", "--version"}:
        print(__version__)
        return 0
    if args[0] == "build-manifest":
        return manifest.main(args[1:])
    if args[0] == "label-emotions":
        return reference_bank.main(args[1:])
    if args[0] == "select-reference":
        return selector.main(args[1:])
    if args[0] == "synthesize":
        return synthesize.main(args[1:])
    if args[0] in GPT_SOVITS_COMMANDS:
        return gpt_sovits.main(args)
    raise SystemExit(f"Unknown command: {args[0]}\n\n{TOP_LEVEL_HELP}")


if __name__ == "__main__":
    raise SystemExit(main())
