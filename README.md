# dance-video-to-prompt

> English translation of [CattleZ/dance-video-to-prompt](https://github.com/CattleZ/dance-video-to-prompt).

Reverse-engineer a **local short video** (dance / posing / outfit-change transitions / travel check-ins / outfit walks, etc., ideally ≤10s) into a structured prompt that can be used directly for AI video generation.

Repository: https://github.com/CattleZ/dance-video-to-prompt

Capabilities: dense frame sampling, **keyframe sharpness check and neighbor-frame rescue**, **audio-track rhythm/BPM analysis**, visual fact observation, rhythm / beat-sync fusion, and a 7-section generation prompt.  
Frame analysis must cover the **subject's body features**, **outfit colors and styles**, **shooting scene**, **shooting method / camera movement / focal emphasis**, and facial expression.  
The Action List must include: **left/right limbs, angle/amplitude, hand shape, gaze, facial expression (including changes)**.

## Quick Start

```bash
# 1. Environment
bash scripts/setup.sh

# 2. Frame extraction + sharpness check + rhythm (Agent-mode work package)
bash skills/dance-video-to-prompt/scripts/run_extract.sh /path/to/video.mp4

# 3. Install the Skill into the local Grok / Claude directories (optional)
bash skills/dance-video-to-prompt/scripts/install.sh
```

Output goes to `output/<video_name>_<timestamp>/` by default (this directory is not committed to the repo).

## Output Template (fixed 7 sections)

| Module | Purpose |
|------|------|
| Visual Style | Image quality, composition, lighting, color tone |
| Scene Narrative | Subject (including body shape features), outfit (colors and styles), demeanor |
| Shooting Scene | Location, spatial relationships, background, ground, furnishings, time/weather and ambient light |
| Cinematography | Shooting method, camera movement, focal emphasis, camera position, focal length, lighting, mood |
| Action List | Timestamped; **must** include left/right limbs, angle/amplitude, hand shape, gaze |
| Dialogue/Text | Dialogue and subtitles |
| Background Audio | BGM style, BPM and beat-sync relationship |

---

## Two Versions

| | **A. Skill / Agent version (recommended default)** | **B. CLI / API version** |
|--|-------------------------------------|---------------------|
| Who "understands the frames" | **The current CLI Agent's multimodal vision** | External vision model HTTP API |
| Calls a Vision API? | **No** | Yes |
| Best for | Interactive, accurate and controllable, no API config needed | Batch, unattended, CI |
| Entry point | Skill `dance-video-to-prompt` or `extract_frames.sh` | `analyze_api.sh` |
| Model dependency | Grok/Claude etc. in the session (must be able to read images) | `VISION_MODEL` + gateway token |

Both versions **share**:

- Frame extraction logic (dense frame sampling)
- Three-stage flow (facts → templated prompt → verification)
- The same 7-section output contract

```text
Local video
   │
   ▼
 scripts/extract_frames.sh     ← shared, no API
   │
   ├──────────── Agent/Skill version ────────┐
   │  Agent read_file views frames           │
   │  → analysis.json → prompt.md            │
   │                                         │
   └──────────── API version ────────────────┤
      analyze_api.sh → Vision API 3 stages ──┘
```

---

## A. Skill / Agent version (no API calls)

### Option 1: Use the Skill in Grok/CLI

Example triggers:

- `/dance-video-to-prompt`
- "Reverse-engineer this dance video into a generation prompt: /path/to/a.mp4"

The Agent will:

1. Run the frame extraction script
2. View the keyframe images itself
3. Write `analysis.json` + `prompt.md`

**Skill master copy (reused along with the repo):**

```text
skills/dance-video-to-prompt/
```

Sync to each local Agent (re-run after modifying the skill):

```bash
bash skills/dance-video-to-prompt/scripts/install.sh
```

Installs to:

- `.grok/skills/dance-video-to-prompt/` (project-level Grok discovery)
- `~/.grok/skills/dance-video-to-prompt/`
- `~/.agents/skills/dance-video-to-prompt/`
- `~/.claude/skills/dance-video-to-prompt/` (if it exists)

### Option 2: Extract frames manually, then let the Agent continue

```bash
bash scripts/setup.sh   # first time only
bash scripts/extract_frames.sh /path/to/dance.mp4
# or
bash scripts/analyze.sh /path/to/dance.mp4 --mode agent
```

The output directory will contain:

- `frames/` — keyframes
- `frames_meta.json`
- `AGENT_INSTRUCTIONS.md` — complete step-by-step instructions for the Agent

Then, in the conversation, ask the Agent to "complete the analysis following AGENT_INSTRUCTIONS".

---

## B. CLI / API version (calls a vision API)

```bash
# 1. Configure
cp config/settings.example.env config/settings.env
# Fill in ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / VISION_MODEL
# VISION_MODEL must support image input

# 2. One-command analysis
bash scripts/analyze_api.sh /path/to/dance.mp4

# Higher-precision frame extraction
bash scripts/analyze_api.sh /path/to/dance.mp4 --interval 0.25

# Skip the verification pass (faster)
bash scripts/analyze_api.sh /path/to/dance.mp4 --no-verify
```

---

## Output Directory

```text
output/<video_name>_<timestamp>/
  frames/
  frames_meta.json
  AGENT_INSTRUCTIONS.md   # agent mode only
  analysis.json             # after analysis completes
  prompt.md                 # final copy-ready prompt
  run_meta.json             # api mode only
```

`output/` holds run artifacts and is not committed to Git by default.

---

## Pipeline (Accuracy)

1. **High-density frame extraction** (default 0.33s, optionally 0.25s)
2. **Sharpness check + neighbor-frame rescue**
3. **Rhythm analysis** (BPM / beats)
4. **Stage 1**: fact observation → JSON (including body, outfit, shooting scene, camera movement, expression)
5. **Stage 2**: rewrite into the 7-section generation prompt
6. **Stage 3**: verify against the facts

No joint-coordinate-level motion reconstruction; actions are described as generation-ready timeline text.

---

## Dependencies

- Python 3.10+
- `opencv` + `Pillow` (frame extraction, required in both modes)
- `httpx` (API mode only)

```bash
bash scripts/setup.sh
```

---

## Script Overview

| Script | Purpose |
|------|------|
| `scripts/setup.sh` | Install dependencies |
| `scripts/extract_frames.sh` | Frame extraction only + Agent work package |
| `scripts/check_frame_quality.sh` | Keyframe sharpness check and neighbor-frame rescue |
| `scripts/analyze_rhythm.sh` | Audio-track rhythm / BPM analysis |
| `scripts/analyze.sh` | General entry point (`--mode agent\|api`) |
| `scripts/analyze_api.sh` | Fully automated via API |
| `skills/dance-video-to-prompt/scripts/run_extract.sh` | Skill entry point: frame extraction + sharpness check + rhythm |
| `skills/dance-video-to-prompt/scripts/install.sh` | Sync the Skill to the local Agent directories |
