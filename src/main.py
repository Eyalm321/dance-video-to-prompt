#!/usr/bin/env python3
"""CLI: local short video → 7-section structured video-generation prompt.

Supports two modes:
- agent: frame extraction only, plus Agent work instructions (no API calls; for the Skill/CLI model to view the images)
- api: frame extraction + three-stage vision API analysis
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_rhythm import analyze_video_rhythm  # noqa: E402
from extract_frames import extract_frames  # noqa: E402
from frame_quality import check_and_rescue_frames  # noqa: E402


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "analyze.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


from agent_kit import write_agent_kit  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Reverse-engineer a local dance video (≤10s) into a 7-section video-generation prompt"
    )
    p.add_argument("video", type=Path, help="Path to the local video")
    p.add_argument(
        "--mode",
        choices=("agent", "api"),
        default="agent",
        help="agent=frame extraction + work kit only (default, for the Skill/CLI model); api=call the vision API",
    )
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory, default output/<video name>_<timestamp>",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Frame extraction interval in seconds, default FRAME_INTERVAL or 0.33",
    )
    p.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of frames, default MAX_FRAMES or 36",
    )
    p.add_argument(
        "--model",
        type=str,
        default=None,
        help="[api] Vision model name",
    )
    p.add_argument(
        "--no-verify",
        action="store_true",
        help="[api] Skip the third-round verification",
    )
    p.add_argument(
        "--frames-only",
        action="store_true",
        help="Legacy compatibility flag: equivalent to --mode agent; can be ignored when detailed instructions are not needed",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env_file(ROOT / "config" / "settings.env")

    setup_logging(ROOT / "logs")
    logger = logging.getLogger("main")

    mode = "agent" if args.frames_only else args.mode

    video_path: Path = args.video.expanduser().resolve()
    if not video_path.exists():
        logger.error("Video does not exist: %s", video_path)
        return 1

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else ROOT / "output" / f"{video_path.stem}_{stamp}"
    )
    frames_dir = out_dir / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    interval = args.interval or float(os.getenv("FRAME_INTERVAL", "0.33"))
    max_frames = args.max_frames or int(os.getenv("MAX_FRAMES", "36"))

    logger.info("Mode: %s", mode)
    logger.info("Video: %s", video_path)
    logger.info("Output: %s", out_dir)
    logger.info("Frame extraction interval=%.3fs max_frames=%d", interval, max_frames)

    samples, duration = extract_frames(
        video_path=video_path,
        output_dir=frames_dir,
        interval_sec=interval,
        max_frames=max_frames,
    )

    # Before viewing images: sharpness check + neighbor-frame rescue
    logger.info("Starting keyframe sharpness check...")
    quality = check_and_rescue_frames(
        video_path=video_path,
        samples=samples,
        output_dir=out_dir,
        duration=duration,
    )
    q_by_path = {f["path"]: f for f in (quality.get("frames") or [])}
    logger.info(
        "Sharpness check done: sharp=%s rescued=%s blurry=%s ok=%s",
        (quality.get("stats") or {}).get("sharp"),
        (quality.get("stats") or {}).get("rescued"),
        (quality.get("stats") or {}).get("blurry"),
        quality.get("ok"),
    )

    meta = {
        "video": str(video_path),
        "duration_sec": duration,
        "interval_sec": interval,
        "mode": mode,
        "frame_quality_ok": quality.get("ok"),
        "frame_quality_threshold": quality.get("threshold"),
        "frames": [
            {
                "time_sec": s.time_sec,
                "path": str(s.path),
                "w": s.width,
                "h": s.height,
                "sharpness": (q_by_path.get(str(s.path)) or {}).get("score"),
                "quality_status": (q_by_path.get(str(s.path)) or {}).get("status"),
            }
            for s in samples
        ],
        "sharp_for_analysis": quality.get("sharp_for_analysis") or [],
    }
    (out_dir / "frames_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # After frame extraction, always run rhythm analysis (written to disk in both agent and api modes, for fusion)
    logger.info("Starting rhythm analysis...")
    rhythm = analyze_video_rhythm(video_path=video_path, out_dir=out_dir, keep_wav=True)
    logger.info(
        "Rhythm analysis done: ok=%s bpm=%s",
        rhythm.get("ok"),
        rhythm.get("bpm"),
    )

    if mode == "agent":
        write_agent_kit(
            out_dir,
            video_path,
            duration,
            samples,
            interval,
            rhythm=rhythm,
            quality=quality,
        )
        logger.info("Agent mode: frame extraction + sharpness + rhythm done, %d frames total", len(samples))
        logger.info("Work instructions: %s", out_dir / "AGENT_INSTRUCTIONS.md")
        print(str(out_dir))
        print(f"FRAME_COUNT={len(samples)}")
        print(f"DURATION_SEC={duration:.3f}")
        print(f"QUALITY_OK={1 if quality.get('ok') else 0}")
        print(f"SHARP={(quality.get('stats') or {}).get('sharp')}")
        print(f"RESCUED={(quality.get('stats') or {}).get('rescued')}")
        print(f"BLURRY={(quality.get('stats') or {}).get('blurry')}")
        print(f"RHYTHM_OK={1 if rhythm.get('ok') else 0}")
        print(f"BPM={rhythm.get('bpm')}")
        print(f"QUALITY_JSON={out_dir / 'frame_quality.json'}")
        print(f"RHYTHM_JSON={out_dir / 'rhythm_analysis.json'}")
        print(f"INSTRUCTIONS={out_dir / 'AGENT_INSTRUCTIONS.md'}")
        return 0

    # API mode: prefer sending sharp frames to the vision model
    from analyze import analyze_video_to_prompt  # noqa: WPS433
    from llm_client import VisionLLMClient  # noqa: WPS433

    sharp_set = set(quality.get("sharp_for_analysis") or [])
    if sharp_set:
        samples_for_api = [s for s in samples if str(s.path) in sharp_set] or samples
    else:
        samples_for_api = samples

    client = VisionLLMClient(model=args.model)
    result = analyze_video_to_prompt(
        client=client,
        samples=samples_for_api,
        duration=duration,
        video_name=video_path.name,
        verify=not args.no_verify,
        rhythm=rhythm,
    )

    prompt_path = out_dir / "prompt.md"
    analysis_path = out_dir / "analysis.json"
    prompt_path.write_text(result["prompt_md"], encoding="utf-8")
    analysis_path.write_text(
        json.dumps(result["analysis"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "video": str(video_path),
                "duration_sec": result["duration"],
                "frame_count": result["frame_count"],
                "model": client.model,
                "mode": "api",
                "issues": result["issues"],
                "verify": not args.no_verify,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    logger.info("Prompt written to: %s", prompt_path)
    if result["issues"]:
        logger.warning("Structure issues: %s", "; ".join(result["issues"]))

    print("\n========== Video Generation Prompt ==========\n")
    print(result["prompt_md"])
    print("====================================")
    print(f"\nSaved: {prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
