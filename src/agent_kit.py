"""Generates the Agent-mode work packet AGENT_INSTRUCTIONS."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def write_agent_kit(
    out_dir: Path,
    video_path: Path,
    duration: float,
    samples: list,
    interval: float,
    rhythm: dict | None = None,
    quality: dict | None = None,
) -> None:
    """Write the work packet for Skill/Agent mode (does not call the model)."""
    quality = quality or {}
    q_frames = {f.get("path"): f for f in (quality.get("frames") or []) if f.get("path")}
    frame_lines = []
    for s in samples:
        q = q_frames.get(str(s.path), {})
        st = q.get("status", "?")
        sc = q.get("score", "?")
        tag = f" [{st} score={sc}]"
        frame_lines.append(f"- t={s.time_sec:.2f}s | {s.path}{tag}")
    frame_lines_text = "\n".join(frame_lines)

    sharp_list = quality.get("sharp_for_analysis") or [str(s.path) for s in samples]
    sharp_lines = "\n".join(f"- {p}" for p in sharp_list)
    blurry = quality.get("blurry_remaining") or []
    blur_lines = (
        "\n".join(
            f"- t={b.get('time_sec')}s score={b.get('score')} | {b.get('path')}"
            for b in blurry
        )
        if blurry
        else "- (none)"
    )
    q_stats = quality.get("stats") or {}
    quality_line = (
        f"- Sharpness: sharp={q_stats.get('sharp')} rescued={q_stats.get('rescued')} "
        f"blurry={q_stats.get('blurry')} thr={quality.get('threshold')} "
        f"→ `{out_dir / 'frame_quality.json'}` / `{out_dir / 'frame_quality_brief.md'}`"
    )

    skill_tpl = ROOT / "skills" / "dance-video-to-prompt" / "templates"
    template_path = skill_tpl / "output_template.md"
    if not template_path.exists():
        template_path = ROOT / "templates" / "output_template.md"
    schema_path = skill_tpl / "stage1_schema.json"
    if not schema_path.exists():
        schema_path = ROOT / "templates" / "stage1_schema.json"
    template_text = (
        template_path.read_text(encoding="utf-8") if template_path.exists() else ""
    )
    schema_text = (
        schema_path.read_text(encoding="utf-8") if schema_path.exists() else "{}"
    )

    rhythm = rhythm or {}
    rhythm_ok = bool(rhythm.get("ok"))
    bpm = rhythm.get("bpm")
    rhythm_line = (
        f"- Rhythm analysis: succeeded, BPM≈{bpm} → `{out_dir / 'rhythm_analysis.json'}` / "
        f"`{out_dir / 'rhythm_brief.md'}`"
        if rhythm_ok
        else f"- Rhythm analysis: failed or no audio track ({rhythm.get('error')}) → still read "
        f"`{out_dir / 'rhythm_analysis.json'}`; do not force a fake BPM during fusion"
    )

    instructions = f"""# Agent Work Packet (no external vision API calls)

Use **the current CLI Agent's multimodal image-viewing capability** (read_file to read images) to complete the **visual analysis**;  
the rhythm values have already been written by a local script and must be interpreted by the **rhythm sub-agent**, after which the main agent **fuses** everything to write the Prompt.  
Do not call any HTTP/Vision API again.

## Inputs

- Video: `{video_path}`
- Duration: approx. {duration:.2f} seconds
- Frame extraction interval: {interval:.3f}s
- Frame count: {len(samples)}
- Output directory: `{out_dir}`
{quality_line}
{rhythm_line}

## Keyframe sharpness (must read before viewing images)

The script has already detected blur via Laplacian variance and performed **neighbor-frame rescue** on blurry frames (replacing the files).

### Priority analysis list `sharp_for_analysis` (you must read_file these first)

{sharp_lines}

### Still-blurry frames (do not scrutinize fingers/facial features; motion blur may be noted)

{blur_lines}

**Rules:**
1. **First read** `frame_quality.json` / `frame_quality_brief.md`
2. **Prioritize**: give fine-grained limb and expression descriptions only for `sharp_for_analysis`
3. Blurry frames: record only timeline placeholders and the rough pose; **do not invent** sharp hand-shape/brow/eye details
4. If too many frames are still blurry (>25%): describe movement trends and amplitude, and mark details as "motion blur, cannot confirm"; you may suggest the user re-extract with `--interval 0.25`

## All keyframes (with sharpness tags)

{frame_lines_text}

## Mandatory multi-stage workflow (sharpness → visuals ∥ rhythm → fusion)

### Stage 0: Confirm sharpness (already done by the script; the Agent must respect the results)

- Report: `{out_dir / "frame_quality.json"}`
- Do not ignore the blurry tags and force-invent details

### Stage A: Visual agent — fact observation (describe only, do not create)

1. **Prioritize** reading with read_file per `sharp_for_analysis`; if there are many frames, cover the first and last plus evenly spaced sharp frames.
2. Write only what can be confirmed in the frames; no invention; do not invent details for blurry frames.
3. Write to: `{out_dir / "analysis.json"}`
4. The JSON must conform to the schema:

```json
{schema_text}
```

Requirements:
- Split segments into 0.5~1.5 second spans covering the whole video
- Each segment's action: left/right limbs, angle/amplitude, hand shape, gaze
- Each segment's expression: brows/eyes/mouth/emotion + change relative to the previous segment; "natural expression" is forbidden
- Outfit: fill in `subject.outfit` item by item with color and style (cut/length/waistline)
- Shooting scene: fill in `scene` with venue, subject placement, background, floor, furnishings, time/setting
- Dialogue/subtitles: write "none" if absent
- audio_guess can be rough; **the final BPM comes from the rhythm file; the visual agent must not invent a precise beat table**

### Stage B: Rhythm sub-agent — beat-sync planning (can run in parallel with A)

1. Read only: `{out_dir / "rhythm_analysis.json"}`, `{out_dir / "rhythm_brief.md"}`
2. Role description in the skill: `skills/dance-video-to-prompt/agents/rhythm_agent.md`
3. **Do not** substitute frame viewing for the rhythm numbers; **do not** write prompt.md directly
4. Write to: `{out_dir / "rhythm_plan.json"}` (structure in templates/rhythm_plan_schema.json)

You can use spawn_subagent to complete Stage B independently; without spawn, the main session switches roles to complete it.

### Stage C: Fusion — 7-section generation prompt (main agent)

Write the Prompt **based on both** `analysis.json` + `rhythm_plan.json` (and the rhythm_analysis beat table).

You must strictly use the 7 level-2 headings (do not add or remove any):

## Visual Style
## Scene Narrative
## Shooting Scene
## Cinematography
## Action List
## Dialogue/Text
## Background Audio

Writing guidelines:
- Accurate: do not invent key movements/clothing/scenes/expressions that are not in analysis
- Scene Narrative: the person's body features + outfit (each item's color and style); no environment details
- Shooting Scene: venue, spatial relationships, background, floor, furnishings, time/setting and ambient light, atmosphere, scene changes
- Five action elements: left/right limbs, angle/amplitude, hand shape, gaze, facial expression; no vague words
- **If rhythm is ok**: align movement timing with the beats/accents; on strong beats write a planted step/micro-pause/limb flick, etc.; Background Audio must state the BPM and the beat-sync timestamps in seconds
- **If rhythm analysis failed**: do not force a fake BPM; movements follow the visual timeline
- Cinematography: shooting method / camera movement / focal emphasis / camera / lens / lighting / mood
- English

Template reference:

```markdown
{template_text}
```

Write to: `{out_dir / "prompt.md"}`

### Stage D: Verification

- Visuals: no invention, left/right correct, all five elements present, expressions change or are stated as holding
- Outfit: Scene Narrative includes color and style for each item; `subject.outfit.items` is filled in
- Shooting Scene: its own section; venue + background with ≥2 elements + subject placement
- Sharpness: no fine-grained hand shape/facial features invented for blurry frames
- Rhythm: when ok, whether the BPM and major beat-sync points made it into the Action List and Background Audio
- Overwrite `prompt.md` with the result

## Completion criteria

- [ ] Read frame_quality.json and prioritized analyzing sharp_for_analysis
- [ ] analysis.json is valid (includes segments[].expression, subject.outfit, and the scene venue fields)
- [ ] rhythm_plan.json is written (a conservative plan is required even if rhythm analysis failed)
- [ ] prompt.md contains all 7 section headings (including Shooting Scene)
- [ ] Each outfit item includes color and style; Shooting Scene is not redundantly piled onto Scene Narrative
- [ ] All five elements present in the Action List; beat-sync reflected when rhythm is available
- [ ] Print prompt.md to the user, and give the analysis / frame_quality / rhythm_* / frames paths
"""
    (out_dir / "AGENT_INSTRUCTIONS.md").write_text(instructions, encoding="utf-8")

