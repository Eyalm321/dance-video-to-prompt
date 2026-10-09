---
name: dance-video-to-prompt
description: >
  Reverse-engineer local short videos (dance / pose showcase / outfit change / travel check-in / outfit walk, etc.; ideally ≤10s, longer also works) into
  structured English prompts that are "ready to use directly for AI video generation".
  Always outputs 7 sections: Visual Style, Scene Narrative, Shooting Scene, Cinematography, Action List, Dialogue/Text, Background Audio.
  The pipeline includes: dense frame sampling, keyframe sharpness check with neighbor-frame rescue, local audio-track rhythm analysis (BPM/beats),
  visual fact observation, a rhythm sub-agent, and visual × rhythm fusion; image review must analyze **the subject's body features**, **outfit colors and styles**,
  **the shooting scene**, **shooting method / camera movement / focal emphasis**, and facial expression; the five action elements must be detailed. Never invent fingers / facial features / precise body contours on blurry frames. This Skill uses the Agent's
  multimodal image viewing; rhythm and sharpness come from local scripts.
  Triggers: /dance-video-to-prompt, convert dance video to prompt, reverse-engineer video prompt, beat-sync prompt,
  video rhythm analysis, summarize moves into a generation prompt, short video to generation prompt, outfit-change video prompt, pose video prompt,
  dance video to prompt, video to prompt, turn this video into a generation prompt.
---

# Dance/Pose Short Video → Video Generation Prompt

## One-Line Summary

**Local video → frame extraction → sharpness check/rescue → rhythm script → (visual agent ∥ rhythm sub-agent) → fusion → 7-section Prompt.**  
The goal is to serve "regenerating a similar / beat-sync-enhanced video with AI", not motion capture or follow-along dance scoring.

## Use Cases

| Good fit | Not a fit |
|------|--------|
| Dance, light dance, beat-sync poses | Precise motion capture / joint coordinates |
| Outfit changes, outfit walks, multiple scenes | Shot-by-shot breakdown of an entire long video (can be split into segments) |
| Output for Kling/Runway/Jimeng | Automatically producing the finished video (this Skill only outputs the Prompt) |

**Duration guidance**: prefer ≤10s; 10-20s is workable; for anything longer, split into segments.

## Fixed Output Structure (headings may not be added or removed)

1. **Visual Style**  
2. **Scene Narrative** (body + **outfit colors and styles**)  
3. **Shooting Scene** (location, spatial relationships, background, set dressing)  
4. **Cinematography** (including **shooting method, camera movement, focal emphasis**)  
5. **Action List** (including expressions + **beat-sync alignment**)  
6. **Dialogue/Text**  
7. **Background Audio** (including **BPM** and its relationship to the beats)  

Contract: `references/output_contract.md`  
Template: `templates/output_template.md`  
Rhythm sub-agent: `agents/rhythm_agent.md`

## Multi-Role Division of Labor (mandatory)

```text
Main Agent (orchestration)
 ├─ Local scripts: frame extraction → sharpness check/neighbor-frame rescue → rhythm analysis
 ├─ Visual agent: read sharp frames first → analysis.json
 ├─ Rhythm sub-agent: read rhythm_* → rhythm_plan.json
 └─ Fusion: analysis + rhythm_plan → prompt.md → validation
```

| Role | Input | Output | Forbidden |
|------|------|------|------|
| **Frame extraction script** | Video | `frames/`, `frames_meta.json` | Calling models |
| **Sharpness script** | Frames + video | `frame_quality.json`, rescue overwrites blurry jpgs | Calling models |
| **Rhythm script** | Video | `rhythm_analysis.json`, `rhythm_brief.md`, `audio.wav` | Inventing visuals |
| **Visual agent** | **Prefer** `sharp_for_analysis` | `analysis.json` | Inventing hands/faces/precise body contours on blurry frames; inventing a precise BPM |
| **Rhythm sub-agent** | Rhythm script outputs | `rhythm_plan.json` | Inventing outfit or action details |
| **Fusion (main)** | analysis + rhythm_plan | `prompt.md` | Skipping rhythm/sharpness constraints |

**Suggested sub-agent invocation (Grok / environments that support Task):**

```text
spawn_subagent(
  subagent_type="general-purpose",
  description="Rhythm beat-sync planning",
  prompt="You are the rhythm sub-agent. Read only rhythm_analysis.json and rhythm_brief.md under OUT_DIR,
  and output rhythm_plan.json to OUT_DIR strictly following skills/.../agents/rhythm_agent.md.
  Do not read keyframes, and do not write prompt.md."
)
```

Without spawn: the main Agent **switches roles** to complete the rhythm sub-agent step, then performs fusion.

## Body / Outfit / Shooting Scene / Camera Movement / Facial Expression / Five Action Elements

### Body Features (mandatory, written mainly in "Scene Narrative")

Image review and `analysis.json` must fill in:

| Field | Content |
|------|------|
| `subject.body_type` | Overall build (height + slim/full or curve type) |
| `subject.body_proportions` | Head-to-body ratio, leg length, shoulders/hips, waistline and other proportions |
| `subject.body_details` | By region: shoulders/neck, chest, waist/abdomen, hips, legs, arms, etc. (only if visible) |
| `subject.posture_habit` | Posture habits such as upright, slight swayback, rounded shoulders |
| `segments[].body_focus` | The body or posture focus highlighted in this segment |

When fusing into `prompt.md`: **Scene Narrative** must contain a continuous, reproducible body description (overall build + ≥2 regional/proportion items + posture); empty phrases like "great figure / very thin" are forbidden.  
Body anchors go mainly in Scene Narrative; the Action List only touches on them lightly where posture is relevant, without repeating whole passages.

### Outfit Colors and Styles (mandatory, written mainly in "Scene Narrative")

Image review and `analysis.json` must fill in `subject.outfit`:

| Field | Content |
|------|------|
| `summary` | One-sentence overall outfit (must include colors and styles) |
| `style` | Style tag (OL / sweet girly / sporty / swimwear / JK, etc.) |
| `palette` | Main color + secondary color + accent |
| `items[]` | Visible items: `slot` + `name` + **`color`** + **`style` (style/cut)** |
| `change` | None / outfit-change moment and before/after |

When fusing: write colors and styles (cut/length/waistline) **item by item**; "fashionable outfit", or only writing "white shirt, black skirt" without the cut, is forbidden.  
See `references/output_contract.md` for details.

### Shooting Scene (mandatory, its own "Shooting Scene" section)

Record "what place is being filmed"; do not merge it into Scene Narrative, and do not mix it with camera movement. `scene` in `analysis.json` must fill in at least:

| Field | Content |
|------|------|
| `setting_type` / `location` / `space` | Indoor/outdoor, location type, spatial structure |
| `subject_placement` | Subject's position and facing direction |
| `background` / `ground` | Background and ground (including color or material) |
| `props` / `atmosphere` | Set dressing, spatial atmosphere |
| `time_weather` / `ambient_light` | Time of day and weather, position of light sources in the space |
| `changes` | Single continuous scene / timestamps of scene changes |

When fusing into `prompt.md`, it must include: **location + spatial relationships + background + ground + set dressing + time and ambient light + atmosphere + scene changes**.  
No "the scene looks nice"; do not invent landmarks that are not visible.

### Shooting Method / Camera Movement / Focal Emphasis (mandatory, written mainly in "Cinematography")

Infer the camera language by comparing across frames; `camera` in `analysis.json` must fill in at least:

| Field | Content |
|------|------|
| `camera.shot_method` | Overview of the shooting method (device stabilization + camera position + intent) |
| `camera.movement` | Main camera movement type and path/speed |
| `camera.movement_rhythm` | Relationship between camera movement and beats |
| `camera.focus_priority` | Focal emphasis of the camera across the whole video (primary + secondary) |
| `camera.height` / `angle` / `framing` | Camera height, angle, shot size and composition |
| `camera.device_feel` / `depth_of_field` | Device look and feel, depth of field and focus |
| `segments[].shot_size` / `camera_move` / `shot_focus` | Per-segment shot size, camera movement, focal point |

When fusing into `prompt.md`, **Cinematography** must include:

1. **Shooting method** — how it is shot, camera position and stabilization, what it aims to highlight  
2. **Camera movement** — executable direction/push-pull/follow (no "smooth camera movement")  
3. **Focal emphasis** — which of full-body proportions / legs and feet / waist and hips / hand gestures / face / outfit / environment the camera prioritizes  

When there is rhythm, try to write "camera pauses slightly on strong beats / follows and drifts on weak beats". Cuts must be marked; do not disguise them as a continuous long take.

### Facial Expression and the Five Action Elements

Brows, eyes, mouth + emotional changes; every action includes **left/right limbs, angle/amplitude, hand shape, gaze, facial expression**.  

See `references/output_contract.md` for details.

## Key Principles

1. **Do not call** external Vision HTTP APIs (unless the user explicitly asks for the API version).  
2. **You must use** `read_file` to view keyframes for visual analysis.  
3. **Rhythm numbers come from the script**; the sub-agent only interprets them and plans the beat-sync strategy, and must not fake the BPM.  
4. **Fusion is mandatory**: when there is an `ok=true` rhythm result, the Action List and "Background Audio" must fit the beats.  
5. Accuracy first: visual facts > beat-sync enhancement timing/intensity; do not invent clothing or props that do not exist.

## Path Resolution

| Location | Meaning |
|------|------|
| `<repo>/skills/dance-video-to-prompt/` | **Primary copy** |
| `<repo>/.grok/skills/...` | Project Grok |
| `~/.grok/skills/...` | User Grok |
| `~/.agents/skills/...` / `~/.claude/skills/...` | Other Agents |

`REPO_ROOT`: `DANCE_VIDEO_PROMPT_ROOT` → two/three levels above the skill → auto-resolved to the current repo root

## Workflow (must follow in order)

### Step 0: Confirm input

- **Absolute path** of the local video  
- Optional: `--interval` (default 0.33), `--max-frames` (default 36)

### Step 1: Frame extraction + sharpness + rhythm (no model API)

```bash
bash "<SKILL_DIR>/scripts/run_extract.sh" "<absolute video path>" --interval 0.33 --max-frames 36
```

`run_extract` / `main.py` **automatically** performs:

1. Frame extraction → `frames/`  
2. **Sharpness check** (Laplacian variance) + **neighbor-frame rescue** → `frame_quality.json`  
3. Rhythm analysis → `rhythm_analysis.json`  

Note down: `OUT_DIR`, `FRAME_COUNT`, `QUALITY_OK`, `SHARP`/`RESCUED`/`BLURRY`, `RHYTHM_OK`, `BPM`.

Re-run only the sharpness check (optional):

```bash
bash "<REPO_ROOT>/scripts/check_frame_quality.sh" "<video>" "<OUT_DIR>"
```

### Step 1.5: Sharpness handling rules (mandatory)

| Check result | Automatic handling | When the Agent views the image |
|----------|----------|--------------|
| **sharp** | Keep | Describe in fine detail as normal |
| **rescued** | **Overwrite the original jpg** with the sharpest neighbor frame within ±0.03-0.15s | Describe based on the rescued image; the timeline still uses the original extraction timestamp |
| **blurry** (rescue failed) | Keep the original frame and flag it | **Do not** invent fingers/facial features/precise body contours; only write the general pose and an impression of the build; may write "motion blur" |
| Blurry frames **>25%** | `QUALITY_OK=0` | Lower confidence on details; may suggest re-extracting with `--interval 0.25` |

**Threshold**: `max(35, median × 0.40)` (adaptive + absolute floor).

### Step 2: Read the work package

1. `OUT_DIR/AGENT_INSTRUCTIONS.md`  
2. `OUT_DIR/frame_quality.json`, `frame_quality_brief.md` (**before viewing images**)  
3. `OUT_DIR/frames_meta.json`  
4. `OUT_DIR/rhythm_analysis.json`, `rhythm_brief.md`  
5. The skill's templates + `references/output_contract.md` + `agents/rhythm_agent.md`

### Step 3A: Visual agent — fact observation

- **Prefer** `read_file` on `frame_quality.json` → the `sharp_for_analysis` list  
- Do not scrutinize hands, faces, or precise body contours on blurry paths  
- **Mandatory body observation**: overall build, proportions, regional contours, posture → write to `subject.body_*` / `posture_habit`  
- **Mandatory outfit observation**: style tag, color scheme, per-item color + style/cut → write to `subject.outfit`; for outfit changes fill in `change` and `segments[].outfit_note`  
- **Mandatory shooting scene observation**: indoor/outdoor, location type, spatial structure, subject position, background/ground (including color and material), set dressing, time and ambient light → write to `scene.*`; for scene changes fill in `changes` and `segments[].scene_note`  
- **Mandatory cinematography/camera movement observation** (must compare across frames):  
  - Device and sense of stabilization, camera height/angle, shot size and composition  
  - Camera movement type and path (push/pull, lateral track, follow, static, orbit, etc.)  
  - **Focal emphasis**: whether the camera is showing the full body, legs and feet, waist and hips, hand gestures, face, outfit, or environment  
  - Write to `camera.shot_method` / `movement` / `focus_priority`, etc.; per segment fill in `shot_size` / `camera_move` / `shot_focus`  
- Fill in `body_focus` for each segment (the body/posture highlighted in that segment's visuals)  
- Write to `OUT_DIR/analysis.json` (fields aligned with `templates/stage1_schema.json`)  
- Music fields can be rough; **BPM comes from the rhythm file**

### Step 3B: Rhythm sub-agent — beat-sync planning

- Follow `agents/rhythm_agent.md`  
- Write to `OUT_DIR/rhythm_plan.json`  
- Can run **in parallel** with 3A (when spawning)

### Step 4: Fusion — 7-section Prompt

Merge `analysis.json` + `rhythm_plan.json`:

- **Scene Narrative** merges `body_type` + `body_proportions` + `body_details` + `posture_habit` + hairstyle + `outfit` (per-item color and style) into the character identity anchor; **do not write environment details**  
- **Shooting Scene** merges `scene.setting_type` / `location` / `space` / `subject_placement` / `background` / `ground` / `props` / `time_weather` / `ambient_light` / `atmosphere` / `changes`  
- **Cinematography** merges `camera.shot_method` + `movement` + `focus_priority` + camera position/lens/lighting; if there is rhythm, layer on camera-movement beat-sync (slight pause on strong beats, etc.)  
- Align the action timeline to beats / accents  
- On strong beats, spell out the accented action; posture-related actions may echo `body_focus`; focus changes may lightly reference `shot_focus`  
- "Background Audio" includes the BPM, energy arc, and beat-sync timestamps in seconds  
- Strictly 7 `##` headings → `OUT_DIR/prompt.md`

### Step 5: Validation

- Body: Scene Narrative contains overall build + ≥2 regional/proportion items + posture; no empty phrases; nothing invented that was not seen  
- Outfit: per-item color + style; has a style tag; no "fashionable outfit" empty phrases  
- Shooting Scene: its own section; location + ≥2 background elements + subject position; not duplicated in Scene Narrative/Cinematography  
- Cinematography: includes shooting method + executable camera movement + focal emphasis; no "smooth camera movement" empty phrases; cuts not disguised as long takes  
- Visuals: nothing invented, left/right correct, all five elements present  
- Rhythm: when `ok=true`, check that the BPM and major beat-sync hits made it into the prompt  
- Overwrite and save back to `prompt.md`

### Step 6: Delivery

1. Print the full `prompt.md`  
2. Paths: `prompt.md`, `analysis.json`, `rhythm_analysis.json`, `rhythm_plan.json`, `frames/`  
3. Tip: frames can be reviewed manually; generate long videos in segments  

## Output Example (body + outfit + shooting scene + cinematography/camera movement + action beat-sync)

```markdown
## Scene Narrative
A tall, slender young woman with an elongated head-to-body ratio and long legs relative to her height, narrow shoulders with defined collarbones, a slim waist and flat stomach,
a clean hip line, long straight slender legs, slender arms, and an upright stance with a hint of dancer's poise; light brown curls falling to her shoulders;
dressed in OL office style: a white fitted short-sleeve collared shirt buttoned at the neck, a black high-waisted bodycon mini skirt, and black patent-leather pointed-toe stiletto heels.

## Shooting Scene
- Location: indoor stairwell corridor, long and narrow space
- Spatial relationship: subject stands against the gray-white wall on the right, about half a step from a half-open white door, facing the camera
- Background: gray-white wall with pencil graffiti, black baseboard, half-open white door on the right
- Ground: gray concrete floor
- Set dressing & props: half-open white door; holding a clear iced coffee cup in both hands
- Time & ambient light: daytime indoors, one overhead light overexposed
- Atmosphere: cool gray office corridor
- Scene changes: single continuous scene

## Cinematography
- Shooting method: vertical phone with a light gimbal feel, eye-level slightly low camera position, frontal leaning toward a 3/4 side angle, always framing the full body to emphasize leg length and posture lines
- Camera movement: slow follow with the subject centered; on strong beats the camera pauses slightly for half a beat, on weak beats it drifts sideways to follow the hip line
- Focal emphasis: primary focus on full-body proportions and stance; secondary focus on footwork hitting the beats and the skirt hem; briefly tightens to a medium shot during expression passages
- Camera: eye level slightly low, frontal slightly angled, gimbal-smooth stability
- Lens: full-body main shot size, background lightly blurred, subject centered with safe headroom
- Lighting: ...
- Mood: fresh, beat-synced, confident

## Action List
1. 0.05–0.67s (beats 1–2): left leg supporting; right foot lands on the strong beat...; face: ...; beat-sync: plant firmly.
2. 10.62–11.24s (big beat hit): ...; beat-sync: stop-step for half a beat.

## Background Audio
- Music: ...about 96.5 BPM...
- Mixing & beat-sync: one step per beat; big beat hits at 5.03/10.0/10.62s
```

## Versus the API Version

| Version | When to use |
|------|------|
| **This Skill (Agent)** | Default; includes the rhythm sub-agent + fusion |
| **API version** | `bash scripts/analyze_api.sh`; still recommended to run `analyze_rhythm.sh` first and merge the rhythm JSON into the context |

## Failure Handling

| Situation | Handling |
|------|------|
| Zero frames | Transcode to mp4 and retry |
| Heavy motion blur | Automatic neighbor-frame rescue; if still blurry, lower detail confidence; re-extract with `--interval 0.25` |
| Rhythm ok=false | Do not write a fake BPM; actions follow the visual timeline |
| Too many frames | Examine 12-16 evenly spaced frames from the **sharp** set in detail |
| Original moves are not on the beat | On the generation side, **enhance beat-sync** according to the rhythm, and explain in Background Audio |

## Install / Sync

```bash
bash skills/dance-video-to-prompt/scripts/install.sh
```
