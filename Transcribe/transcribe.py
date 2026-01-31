import json
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel
from tqdm import tqdm


def run(cmd):
    subprocess.run(cmd, check=True)


def format_srt_time(seconds: float) -> str:
    # SRT timestamp: HH:MM:SS,mmm
    ms = int(round(seconds * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_wav_16k_mono(input_audio: Path) -> Path:
    """
    Convert any audio (m4a/mp3/wav/etc) into 16kHz mono PCM wav.
    This makes transcription reliable across formats.
    """
    out_wav = input_audio.with_suffix(".16k_mono.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_wav)
    ]
    run(cmd)
    return out_wav


def main():
    import argparse

    p = argparse.ArgumentParser(
        description="Free offline transcription (m4a/mp3/wav/etc) -> txt/srt/json with a progress bar"
    )
    p.add_argument("audio", help="Path to audio file (m4a/mp3/wav/etc)")
    p.add_argument("--model", default="small", help="tiny/base/small/medium/large-v3")
    p.add_argument("--language", default=None, help="Force language code, e.g. en, zh (optional)")
    p.add_argument("--keep_wav", action="store_true", help="Keep intermediate .16k_mono.wav (default: kept anyway)")
    args = p.parse_args()

    input_audio = Path(args.audio).expanduser().resolve()
    if not input_audio.exists():
        raise FileNotFoundError(f"File not found: {input_audio}")

    # 1) Convert to wav
    wav = to_wav_16k_mono(input_audio)

    # 2) Load model
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    # 3) Transcribe with progress bar (based on audio seconds covered)
    segments, info = model.transcribe(
        str(wav),
        beam_size=5,
        vad_filter=True,
        language=args.language
    )

    segs = []
    total_duration = float(info.duration) if info.duration else 0.0
    last_t = 0.0

    # If duration is known, show a proper progress bar; otherwise just collect segments.
    if total_duration > 0:
        with tqdm(total=total_duration, unit="sec", desc="Transcribing") as pbar:
            for seg in segments:
                segs.append(seg)
                # advance by new audio time covered
                new_t = max(last_t, float(seg.end))
                pbar.update(max(0.0, new_t - last_t))
                last_t = new_t
    else:
        for seg in segments:
            segs.append(seg)

    out_base = input_audio  # outputs named based on original input file

    # 4) Write TXT
    text = "\n".join(seg.text.strip() for seg in segs if seg.text and seg.text.strip())
    out_txt = out_base.with_suffix(".txt")
    out_txt.write_text(text, encoding="utf-8")

    # 5) Write SRT
    srt_lines = []
    for i, seg in enumerate(segs, start=1):
        srt_lines.append(str(i))
        srt_lines.append(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}")
        srt_lines.append(seg.text.strip())
        srt_lines.append("")
    out_srt = out_base.with_suffix(".srt")
    out_srt.write_text("\n".join(srt_lines), encoding="utf-8")

    # 6) Write JSON
    out_json = out_base.with_suffix(".json")
    data = {
        "detected_language": info.language,
        "duration": info.duration,
        "model": args.model,
        "segments": [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs],
    }
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDone.")
    print("Input:", input_audio.name)
    print("Detected language:", info.language)
    print("Outputs:", out_txt.name, out_srt.name, out_json.name)
    print("Intermediate wav:", wav.name)


if __name__ == "__main__":
    main()

