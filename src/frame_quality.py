#!/usr/bin/env python3
"""Sharpness check for extracted frames: Laplacian variance + neighbor-frame rescue to replace blurry frames."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
from PIL import Image

from extract_frames import FrameSample

logger = logging.getLogger("frame_quality")

# Absolute floor: below this a frame is almost certainly blurry (resolution-dependent; re-judged after rescue)
ABS_MIN_SHARP = 35.0
# Ratio relative to the median: score < median * REL_FACTOR counts as blurry
REL_FACTOR = 0.40
# Rescue search offsets (seconds)
RESCUE_OFFSETS = (-0.10, -0.06, -0.03, 0.03, 0.06, 0.10, 0.15, -0.15)
# A rescue only succeeds if the new frame is at least this many times better than the original
RESCUE_IMPROVE = 1.25


@dataclass
class FrameQuality:
    index: int
    time_sec: float
    path: str
    score: float
    status: str  # sharp | rescued | blurry
    rescued_offset: float | None = None
    score_before: float | None = None


def laplacian_score_bgr(frame_bgr) -> float:
    if frame_bgr is None or frame_bgr.size == 0:
        return 0.0
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def laplacian_score_path(path: Path) -> float:
    img = cv2.imread(str(path))
    if img is None:
        return 0.0
    return laplacian_score_bgr(img)


def _read_frame_at(cap: cv2.VideoCapture, time_sec: float, fps: float, frame_count: int):
    idx = min(int(round(time_sec * fps)), max(frame_count - 1, 0))
    if idx < 0:
        idx = 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, frame = cap.read()
    if not ok or frame is None:
        return None, idx
    return frame, idx


def _adaptive_threshold(scores: list[float]) -> float:
    if not scores:
        return ABS_MIN_SHARP
    arr = sorted(scores)
    mid = arr[len(arr) // 2]
    # Fall back to the absolute floor when the median is low
    return max(ABS_MIN_SHARP, mid * REL_FACTOR)


def check_and_rescue_frames(
    video_path: Path,
    samples: list[FrameSample],
    output_dir: Path,
    duration: float,
) -> dict[str, Any]:
    """
    Check each frame's sharpness; if blurry, re-grab the sharpest frame from its neighborhood and overwrite the original file.
    Write frame_quality.json and return the report dict.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if not samples:
        report = {
            "ok": False,
            "error": "No frames to check",
            "frames": [],
            "sharp_for_analysis": [],
            "blurry_remaining": [],
            "stats": {},
        }
        _write_report(output_dir, report)
        return report

    # Initial screening scores
    raw_scores = [laplacian_score_path(s.path) for s in samples]
    threshold = _adaptive_threshold(raw_scores)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        report = {
            "ok": False,
            "error": f"Could not open video for rescue: {video_path}",
            "threshold": threshold,
            "frames": [],
            "sharp_for_analysis": [str(s.path) for s in samples],
            "blurry_remaining": [],
            "stats": {"total": len(samples), "note": "rescue skipped"},
        }
        _write_report(output_dir, report)
        return report

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    results: list[FrameQuality] = []
    for s, score0 in zip(samples, raw_scores):
        if score0 >= threshold:
            results.append(
                FrameQuality(
                    index=s.index,
                    time_sec=s.time_sec,
                    path=str(s.path),
                    score=round(score0, 2),
                    status="sharp",
                )
            )
            continue

        # Neighbor-frame rescue
        best_score = score0
        best_frame = None
        best_off = 0.0
        for off in RESCUE_OFFSETS:
            t2 = s.time_sec + off
            if t2 < 0 or t2 > duration + 0.05:
                continue
            frame, _ = _read_frame_at(cap, t2, fps, frame_count)
            if frame is None:
                continue
            sc = laplacian_score_bgr(frame)
            if sc > best_score:
                best_score = sc
                best_frame = frame
                best_off = off

        if best_frame is not None and best_score >= score0 * RESCUE_IMPROVE and best_score >= threshold * 0.85:
            rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
            Image.fromarray(rgb).save(s.path, quality=92, optimize=True)
            # Update the sample time label: the filename may keep the original timestamp; the report records the actual offset
            results.append(
                FrameQuality(
                    index=s.index,
                    time_sec=s.time_sec,
                    path=str(s.path),
                    score=round(best_score, 2),
                    status="rescued",
                    rescued_offset=round(best_off, 3),
                    score_before=round(score0, 2),
                )
            )
            logger.info(
                "Blurry frame rescued t=%.2fs score %.1f→%.1f offset=%+.3fs",
                s.time_sec,
                score0,
                best_score,
                best_off,
            )
        else:
            results.append(
                FrameQuality(
                    index=s.index,
                    time_sec=s.time_sec,
                    path=str(s.path),
                    score=round(score0, 2),
                    status="blurry",
                    score_before=round(score0, 2),
                )
            )
            logger.warning("Frame still blurry t=%.2fs score=%.1f thr=%.1f", s.time_sec, score0, threshold)

    cap.release()

    sharp_paths = [r.path for r in results if r.status in ("sharp", "rescued")]
    blurry = [r for r in results if r.status == "blurry"]
    # If there are too few sharp frames: add the relatively sharpest ones to the analysis list (still marked blurry)
    min_need = max(4, len(samples) // 3)
    if len(sharp_paths) < min_need:
        ranked = sorted(results, key=lambda x: x.score, reverse=True)
        for r in ranked:
            if r.path not in sharp_paths:
                sharp_paths.append(r.path)
            if len(sharp_paths) >= min_need:
                break

    n_sharp = sum(1 for r in results if r.status == "sharp")
    n_rescued = sum(1 for r in results if r.status == "rescued")
    n_blur = len(blurry)
    ok = n_blur <= max(2, len(samples) // 4) and len(sharp_paths) >= 3

    report: dict[str, Any] = {
        "ok": ok,
        "method": "laplacian_variance",
        "threshold": round(threshold, 2),
        "rel_factor": REL_FACTOR,
        "abs_min": ABS_MIN_SHARP,
        "rescue_offsets_sec": list(RESCUE_OFFSETS),
        "frames": [asdict(r) for r in results],
        "sharp_for_analysis": sharp_paths,
        "blurry_remaining": [asdict(r) for r in blurry],
        "stats": {
            "total": len(results),
            "sharp": n_sharp,
            "rescued": n_rescued,
            "blurry": n_blur,
            "sharp_for_analysis_count": len(sharp_paths),
            "mean_score": round(sum(r.score for r in results) / max(len(results), 1), 2),
        },
        "agent_rules": {
            "prefer_paths": "sharp_for_analysis",
            "blurry_use": "Use only as a time placeholder; do not write fine finger/facial-feature details from it; may write \"motion blur / movement transition\"",
            "if_many_blurry": "Action entries describe amplitude and trend, with lower confidence on details; may suggest the user re-extract with --interval 0.25",
        },
    }
    _write_report(output_dir, report)
    _write_brief(output_dir, report)
    logger.info(
        "Sharpness: total=%d sharp=%d rescued=%d blurry=%d thr=%.1f ok=%s",
        len(results),
        n_sharp,
        n_rescued,
        n_blur,
        threshold,
        ok,
    )
    return report


def _write_report(out_dir: Path, report: dict[str, Any]) -> None:
    (out_dir / "frame_quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _write_brief(out_dir: Path, report: dict[str, Any]) -> None:
    st = report.get("stats") or {}
    lines = [
        "# Keyframe Sharpness Brief",
        "",
        f"- Method: Laplacian variance",
        f"- Threshold: {report.get('threshold')}",
        f"- Stats: {st.get('total')} frames total | sharp {st.get('sharp')} | rescued {st.get('rescued')} | still blurry {st.get('blurry')}",
        f"- Priority frames for analysis: {st.get('sharp_for_analysis_count')}",
        f"- Status ok: {report.get('ok')}",
        "",
        "## Still-Blurry Moments (do not scrutinize fingers or facial features)",
    ]
    blur = report.get("blurry_remaining") or []
    if not blur:
        lines.append("- (none)")
    else:
        for r in blur:
            lines.append(f"- t={r.get('time_sec')}s score={r.get('score')} → `{r.get('path')}`")
    lines += [
        "",
        "## Visual Agent Rules",
        "1. **Prefer** read_file on the paths in the `sharp_for_analysis` list",
        "2. Blurry frames: you may note the time and rough pose; **do not** invent sharp hand-shape / facial-feature details",
        "3. If there are too many blurry frames: the Action List describes trend and amplitude; for details write \"cannot be confirmed due to motion blur\"",
        "",
    ]
    (out_dir / "frame_quality_brief.md").write_text("\n".join(lines), encoding="utf-8")
