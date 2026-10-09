"""Two-stage analysis: fact observation → template prompt → verification."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from extract_frames import FrameSample
from llm_client import VisionLLMClient
from prompts import (
    STAGE1_SYSTEM,
    STAGE1_USER_TEMPLATE,
    STAGE2_SYSTEM,
    STAGE2_USER_TEMPLATE,
    VERIFY_SYSTEM,
    VERIFY_USER_TEMPLATE,
)
from render_prompt import normalize_prompt_markdown, validate_prompt

logger = logging.getLogger(__name__)


def analyze_video_to_prompt(
    client: VisionLLMClient,
    samples: list[FrameSample],
    duration: float,
    video_name: str,
    verify: bool = True,
    rhythm: dict[str, Any] | None = None,
) -> dict[str, Any]:
    image_paths = [s.path for s in samples]
    frame_times = ", ".join(f"{s.time_sec:.2f}" for s in samples)

    # Stage 1: fact layer
    stage1_user = STAGE1_USER_TEMPLATE.format(
        video_name=video_name,
        duration=duration,
        frame_count=len(samples),
        frame_times=frame_times,
    )
    # Add a note explaining the time label on each image
    stage1_user = (
        "The following images are in chronological order; each filename contains its timestamp.\n" + stage1_user
    )
    raw_analysis = client.complete_with_images(
        system=STAGE1_SYSTEM,
        user_text=stage1_user,
        image_paths=image_paths,
        max_tokens=4096,
        temperature=0.1,
    )
    analysis = _parse_json_loose(raw_analysis)
    analysis_json = json.dumps(analysis, ensure_ascii=False, indent=2)
    logger.info("Stage 1 done: fact-observation JSON parsed")

    rhythm_json = json.dumps(rhythm or {}, ensure_ascii=False, indent=2)

    # Stage 2: template prompt (visual facts + rhythm fusion)
    stage2_user = STAGE2_USER_TEMPLATE.format(
        duration=duration,
        analysis_json=analysis_json,
        rhythm_json=rhythm_json,
    )
    # Stage 2 need not resend every frame, but attaching a few keyframes improves consistency
    key_paths = _pick_key_frames(samples, k=8)
    raw_prompt = client.complete_with_images(
        system=STAGE2_SYSTEM,
        user_text=stage2_user + "\n\nA few keyframes are also attached for checking actions and appearance.",
        image_paths=key_paths,
        max_tokens=4096,
        temperature=0.3,
    )
    prompt_md = normalize_prompt_markdown(raw_prompt)
    logger.info("Stage 2 done: template prompt generated")

    # Stage 3: verification
    if verify:
        verify_user = VERIFY_USER_TEMPLATE.format(
            analysis_json=analysis_json,
            rhythm_json=rhythm_json,
            prompt_md=prompt_md,
        )
        raw_verified = client.complete_with_images(
            system=VERIFY_SYSTEM,
            user_text=verify_user,
            image_paths=key_paths,
            max_tokens=4096,
            temperature=0.1,
        )
        prompt_md = normalize_prompt_markdown(raw_verified)
        logger.info("Verification done")

    issues = validate_prompt(prompt_md)
    if issues:
        logger.warning("Prompt structure issues: %s", "; ".join(issues))

    return {
        "analysis": analysis,
        "analysis_raw": raw_analysis,
        "prompt_md": prompt_md,
        "issues": issues,
        "duration": duration,
        "frame_count": len(samples),
    }


def _pick_key_frames(samples: list[FrameSample], k: int = 8) -> list[Path]:
    if len(samples) <= k:
        return [s.path for s in samples]
    idxs = sorted({round(i * (len(samples) - 1) / (k - 1)) for i in range(k)})
    return [samples[i].path for i in idxs]


def _parse_json_loose(text: str) -> dict[str, Any]:
    text = text.strip()
    # Strip code fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Slice from the first { to the last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    logger.warning("Fact-layer JSON parse failed; falling back to a raw wrapper")
    return {"raw": text}
