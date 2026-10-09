#!/usr/bin/env python3
"""Extract the audio track from a local video and analyze BPM / beat grid / energy curve (no external API)."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("analyze_rhythm")

def extract_wav(video_path: Path, wav_path: Path) -> bool:
    """Prefer macOS afconvert, then fall back to system ffmpeg."""
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("afconvert"):
        cmd = [
            "afconvert",
            "-f",
            "WAVE",
            "-d",
            "LEI16@44100",
            "-c",
            "1",
            str(video_path),
            str(wav_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 1000:
            return True
        logger.warning("afconvert failed: %s", (r.stderr or r.stdout or "")[:300])

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        for cand in (
            Path("/Applications/VideoFusion-macOS.app/Contents/Resources/ffmpeg"),
            Path("/opt/homebrew/bin/ffmpeg"),
            Path("/usr/local/bin/ffmpeg"),
        ):
            if cand.is_file():
                ffmpeg = str(cand)
                break
    if ffmpeg:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "1",
            str(wav_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 1000:
            return True
        logger.warning("ffmpeg audio extraction failed code=%s", r.returncode)

    return False

def load_mono_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        n = w.getnframes()
        raw = w.readframes(n)
        width = w.getsampwidth()
    if width != 2:
        raise ValueError(f"Only 16-bit PCM is supported, got sample_width={width}")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    peak = float(np.max(np.abs(data))) + 1e-9
    data = data / peak
    return data, sr

def _onset_env(band: np.ndarray, smooth: int = 3) -> np.ndarray:
    d = np.maximum(0.0, np.diff(band, prepend=band[0]))
    if smooth > 1:
        k = np.ones(smooth) / smooth
        d = np.convolve(d, k, mode="same")
    return d / (float(d.max()) + 1e-9)

def analyze_audio(data: np.ndarray, sr: int) -> dict[str, Any]:
    dur = len(data) / sr
    nfft, hop = 2048, 512
    win = np.hanning(nfft)
    frames = [
        np.abs(np.fft.rfft(data[i : i + nfft] * win))
        for i in range(0, len(data) - nfft, hop)
    ]
    if not frames:
        return _empty_result(dur, "Audio too short to analyze")

    S = np.array(frames)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    hop_s = hop / sr
    t = np.arange(S.shape[0]) * hop_s

    kick = S[:, (freqs >= 40) & (freqs < 150)].sum(1)
    snare = S[:, (freqs >= 1500) & (freqs < 5000)].sum(1)
    full = S.sum(1)
    low_e = float(kick.sum())
    mid_e = float(S[:, (freqs >= 200) & (freqs < 2000)].sum())
    high_e = float(S[:, (freqs >= 2000) & (freqs < 8000)].sum())
    tot = low_e + mid_e + high_e + 1e-12

    o_kick = _onset_env(kick)
    o_snare = _onset_env(snare)
    o_full = _onset_env(full)
    o = 0.55 * o_kick + 0.25 * o_snare + 0.20 * o_full

    scores: list[tuple[float, float, int]] = []
    for bpm in np.arange(70, 160.5, 0.5):
        lag = int(round((60.0 / float(bpm)) / hop_s))
        if lag < 1 or lag >= len(o) // 2:
            continue
        c1 = float(np.dot(o[:-lag], o[lag:]))
        lag2 = lag * 2
        c2 = (
            float(np.dot(o[:-lag2], o[lag2:]))
            if lag2 < len(o) // 2
            else 0.0
        )
        w = 1.15 if 85 <= bpm <= 110 else (1.08 if 110 < bpm <= 130 else 1.0)
        scores.append(((c1 + 0.45 * c2) * w, float(bpm), lag))
    scores.sort(reverse=True)
    if not scores:
        return _empty_result(dur, "Could not estimate BPM")

    thr = float(np.mean(o) + 0.65 * np.std(o))
    min_gap = max(1, int(0.12 / hop_s))
    peaks: list[int] = []
    for i in range(1, len(o) - 1):
        if o[i] > thr and o[i] >= o[i - 1] and o[i] >= o[i + 1]:
            if not peaks or i - peaks[-1] > min_gap:
                peaks.append(i)
    peak_times = t[peaks] if peaks else np.array([])
    iv = np.diff(peak_times) if len(peak_times) >= 2 else np.array([])

    best_bpm = scores[0][1]
    best_err = 1e9
    for bpm in [s[1] for s in scores[:8]] + [scores[0][1] / 2, scores[0][1] * 2]:
        if bpm < 70 or bpm > 160 or len(iv) == 0:
            continue
        per = 60.0 / bpm
        near = np.minimum(np.abs(iv - per), np.abs(iv - per / 2))
        err = float(np.median(near))
        if err < best_err:
            best_err = err
            best_bpm = float(bpm)

    period = 60.0 / best_bpm
    best_off, best_sc = 0.0, -1e9
    for off in np.linspace(0, period, 48, endpoint=False):
        sc = 0.0
        nbeat = 0
        bt = float(off)
        while bt < dur:
            idx = int(round(bt / hop_s))
            if 0 <= idx < len(o):
                sc += float(o[idx]) + 0.5 * float(o_kick[idx])
                nbeat += 1
            bt += period
        sc = sc / max(nbeat, 1)
        if sc > best_sc:
            best_sc, best_off = sc, float(off)

    bt = best_off
    while bt - period >= -0.01:
        bt -= period
    if bt < 0:
        bt += period
    beats: list[float] = []
    while bt <= dur + 0.01:
        beats.append(round(float(bt), 3))
        bt += period

    bars = beats[::4]
    strong = beats[::2]

    energy_1s: list[dict[str, Any]] = []
    for sec in range(int(dur) + 1):
        a, b = int(sec * sr), int(min((sec + 1) * sr, len(data)))
        if b <= a:
            break
        rms = float(np.sqrt(np.mean(data[a:b] ** 2)))
        energy_1s.append({"t_start": sec, "t_end": sec + 1, "rms": round(rms, 3)})

    beat_hits: list[dict[str, Any]] = []
    accents: list[float] = []
    for i, b in enumerate(beats):
        idx = max(0, min(len(o_kick) - 1, int(round(b / hop_s))))
        lo, hi = max(0, idx - 2), min(len(o_kick), idx + 3)
        k, s, f = float(o_kick[lo:hi].max()), float(o_snare[lo:hi].max()), float(o_full[lo:hi].max())
        kind = "soft" if f < 0.15 else ("kick" if k >= s else "snare_hi")
        beat_hits.append({"i": i + 1, "t": b, "kind": kind, "kick": round(k, 2), "snare": round(s, 2), "full": round(f, 2)})
        if f >= 0.35 or k >= 0.55:
            accents.append(b)

    style_bits: list[str] = []
    if 90 <= best_bpm <= 105:
        style_bits.append("Typical range for mid-to-slow pop / ballad dance tracks")
    elif 105 < best_bpm <= 125:
        style_bits.append("Typical range for mid-to-fast pop / beat-sync dance tracks")
    elif best_bpm > 125:
        style_bits.append("Fast-leaning electronic / Dance range")
    if low_e / tot > 0.45:
        style_bits.append("Prominent low-end drums / bass")
    if high_e / tot < 0.1:
        style_bits.append("Highs are not harsh; not explosive EDM")
    if energy_1s:
        early = float(np.mean([e["rms"] for e in energy_1s[: max(1, len(energy_1s) // 3)]]))
        late = float(np.mean([e["rms"] for e in energy_1s[max(1, 2 * len(energy_1s) // 3) :]]))
        if late > early * 1.25:
            style_bits.append("Energy lifts in the second half; suits ending on a big beat-sync hit")
        elif early > late * 1.15:
            style_bits.append("First half is stronger; the ending can wind down")

    return {
        "ok": True,
        "duration_sec": round(dur, 3),
        "bpm": round(best_bpm, 1),
        "beat_period_sec": round(period, 3),
        "eighth_sec": round(period / 2, 3),
        "time_signature_guess": "4/4",
        "downbeat_offset_sec": round(best_off, 3),
        "beats": beats,
        "bars_4_4": bars,
        "strong_beats": strong,
        "accent_beats": accents[:12],
        "beat_hits": beat_hits,
        "onset_peak_times": [round(float(x), 3) for x in peak_times.tolist()],
        "energy_1s": energy_1s,
        "band_energy_ratio": {
            "low": round(low_e / tot, 3),
            "mid": round(mid_e / tot, 3),
            "high": round(high_e / tot, 3),
        },
        "top_bpm": [{"bpm": b, "score": round(s, 4)} for s, b, _ in scores[:6]],
        "style_hint": "; ".join(style_bits) if style_bits else "Mid-tempo, pop-leaning",
        "kadian_rules": {
            "default_step": "One step per beat (step rate ≈ BPM) or one key move per beat",
            "strong_beat": "On strong beats: plant the step / brief pause / limb snap / skirt flick",
            "accent_beat": "Hit the big beat-sync moments on accent_beats and energy peaks",
            "forbid": "Never use constant-speed, unaccented movement that completely ignores the beats",
        },
        "error": None,
    }

def _empty_result(dur: float, err: str) -> dict[str, Any]:
    return {
        "ok": False,
        "duration_sec": round(dur, 3),
        "bpm": None,
        "beats": [],
        "error": err,
        "style_hint": "No reliable rhythm; write Background Audio conservatively and time actions to the visual timeline",
        "kadian_rules": {
            "default_step": "Follow the visual timeline; do not force beat-sync",
            "forbid": "Do not invent a precise BPM",
        },
    }

def analyze_video_rhythm(
    video_path: Path,
    out_dir: Path,
    keep_wav: bool = True,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "audio.wav"
    result: dict[str, Any] = {
        "video": str(video_path),
        "ok": False,
    }

    if not extract_wav(video_path, wav_path):
        result.update(
            _empty_result(0.0, "Could not extract the audio track (afconvert/ffmpeg unavailable or no audio track)")
        )
        result["video"] = str(video_path)
        (out_dir / "rhythm_analysis.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    try:
        data, sr = load_mono_wav(wav_path)
        analysis = analyze_audio(data, sr)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Rhythm analysis failed")
        analysis = _empty_result(0.0, f"Analysis error: {exc}")

    analysis["video"] = str(video_path)
    analysis["audio_wav"] = str(wav_path) if keep_wav else None
    if not keep_wav and wav_path.exists():
        wav_path.unlink(missing_ok=True)

    (out_dir / "rhythm_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Human-readable brief (the rhythm sub-agent can read it directly)
    brief = _render_brief(analysis)
    (out_dir / "rhythm_brief.md").write_text(brief, encoding="utf-8")
    return analysis

def _render_brief(a: dict[str, Any]) -> str:
    if not a.get("ok"):
        return (
            f"# Rhythm Brief\n\n- Status: failed\n- Reason: {a.get('error')}\n"
            f"- Suggestion: {a.get('style_hint')}\n"
        )
    beats = a.get("beats") or []
    accents = a.get("accent_beats") or []
    bars = a.get("bars_4_4") or []
    lines = [
        "# Rhythm Brief (for the rhythm sub-agent / fusion stage)",
        "",
        f"- **BPM**: {a.get('bpm')} (beat interval ≈ {a.get('beat_period_sec')}s)",
        f"- **Time signature guess**: {a.get('time_signature_guess')}",
        f"- **Downbeat offset**: {a.get('downbeat_offset_sec')}s",
        f"- **Style hint**: {a.get('style_hint')}",
        f"- **Frequency bands**: low/mid/high = {a.get('band_energy_ratio')}",
        "",
        "## Beat-Sync Rules",
    ]
    rules = a.get("kadian_rules") or {}
    for k, v in rules.items():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "## Bar Downbeats (4/4 bar starts)",
        ", ".join(str(x) for x in bars),
        "",
        "## All Beats",
        ", ".join(str(x) for x in beats),
        "",
        "## Suggested Big Beat-Sync Hits (accent)",
        ", ".join(str(x) for x in accents) if accents else "(energy is fairly even; use strong_beats)",
        "",
        "## 1-Second Energy",
    ]
    for e in a.get("energy_1s") or []:
        lines.append(f"- {e['t_start']}-{e['t_end']}s rms={e['rms']}")
    lines.append("")
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    p = argparse.ArgumentParser(description="Rhythm analysis of a video's audio track → rhythm_analysis.json")
    p.add_argument("video", type=Path, help="Path to the video")
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory (same OUT_DIR as frame extraction)",
    )
    p.add_argument("--no-keep-wav", action="store_true", help="Delete the wav after analysis")
    args = p.parse_args(argv)

    video = args.video.expanduser().resolve()
    if not video.exists():
        logger.error("Video does not exist: %s", video)
        return 1

    result = analyze_video_rhythm(
        video_path=video,
        out_dir=args.output_dir.expanduser().resolve(),
        keep_wav=not args.no_keep_wav,
    )
    print(f"RHYTHM_OK={1 if result.get('ok') else 0}")
    print(f"BPM={result.get('bpm')}")
    print(f"RHYTHM_JSON={args.output_dir / 'rhythm_analysis.json'}")
    print(f"RHYTHM_BRIEF={args.output_dir / 'rhythm_brief.md'}")
    return 0 if result.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
