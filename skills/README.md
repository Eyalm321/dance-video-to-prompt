# Project Skills

This directory holds reusable Agent Skills so they can be copied/synced along with the repo.

## dance-video-to-prompt

**Local short video → 7-section AI video-generation prompt** (the Agent views the images; no external Vision API is called).

Covers many kinds of vertical reference clips: dance / pose showcase / outfit change / travel check-in / outfit walk, etc.  
The Action List must include: **left/right limbs, angle/amplitude, hand shape, gaze, facial expression (including changes over the timeline)**.  
When viewing the images, analyze brows/eyes/mouth and emotion, **outfit colors and styles**, and the **shooting scene**, write them into `analysis.json`, and carry them into the Prompt.

### Primary copy

```text
skills/dance-video-to-prompt/
```

See `SKILL.md` in that directory for full documentation.

### Install to each local Agent

```bash
bash skills/dance-video-to-prompt/scripts/install.sh
```

Syncs to:

- `.grok/skills/dance-video-to-prompt/`
- `~/.grok/skills/dance-video-to-prompt/`
- `~/.agents/skills/dance-video-to-prompt/`
- `~/.claude/skills/dance-video-to-prompt/` (if it exists)

### Usage

```text
/dance-video-to-prompt /path/to/video.mp4
```

Or:

```text
Reverse-engineer this dance video into a generation prompt: /path/to/video.mp4
```

Frame extraction only:

```bash
bash skills/dance-video-to-prompt/scripts/run_extract.sh /path/to/video.mp4
```

### Maintenance

**`skills/dance-video-to-prompt/` is the primary copy**; after making changes, run `install.sh` again.
