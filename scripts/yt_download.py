import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class TimeRange:
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


def parse_timestamp_to_seconds(text: str) -> float:
    """
    Accepts timestamps in mm:ss or hh:mm:ss (optionally with fractional seconds like mm:ss.sss).
    Returns seconds as float.
    """
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Timestamp cannot be empty")

    # Support hh:mm:ss(.ms) and mm:ss(.ms)
    parts = cleaned.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("Timestamp must be mm:ss or hh:mm:ss")

    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            total = minutes * 60 + seconds
        else:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            total = hours * 3600 + minutes * 60 + seconds
    except ValueError as exc:
        raise ValueError("Invalid timestamp numbers") from exc

    if total < 0:
        raise ValueError("Timestamp must be non-negative")

    return float(total)


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print("No input provided.", file=sys.stderr)
        sys.exit(1)


def ensure_directories(base_downloads: Path) -> Tuple[Path, Path, Path]:
    downloads_dir = base_downloads
    trimmed_dir = downloads_dir / "trimmed"
    compressed_dir = downloads_dir / "compressed"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    trimmed_dir.mkdir(parents=True, exist_ok=True)
    compressed_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir, trimmed_dir, compressed_dir


def check_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        print(
            "ffmpeg is required but not found in PATH. Please install it (e.g., brew install ffmpeg)",
            file=sys.stderr,
        )
        sys.exit(2)


def sanitize_filename(name: str) -> str:
    # Basic sanitation to avoid problematic filesystem characters
    return re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()


def download_video(url: str, downloads_dir: Path) -> Path:
    """Download the YouTube video using yt-dlp, return the final local file path."""
    try:
        import yt_dlp  # type: ignore
    except Exception as e:
        print("yt-dlp is required. Run via 'uv run' to auto-install dependencies. Error:", e, file=sys.stderr)
        raise

    output_tmpl = str((downloads_dir / "%(title).200B [%(id)s].%(ext)s").resolve())

    ydl_opts = {
        "outtmpl": output_tmpl,
        "merge_output_format": "mp4",
        "format": "bv*+ba/b",  # best video+audio, fallback to best
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
        ],
        # Less noise
        "quiet": False,
        "noprogress": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Compute the prepared filename; if remuxed to mp4, adjust extension
        base_filepath = Path(ydl.prepare_filename(info))
        if base_filepath.suffix.lower() != ".mp4":
            final_path = base_filepath.with_suffix(".mp4")
        else:
            final_path = base_filepath

    if not final_path.exists():
        # Sometimes the final path might include a different sanitized title; ensure we pick an mp4 in downloads matching id
        vid_id = info.get("id") if isinstance(info, dict) else None
        candidates = list(downloads_dir.glob(f"*[{vid_id}].mp4")) if vid_id else []
        if candidates:
            return candidates[0]
        raise FileNotFoundError("Downloaded video file not found after yt-dlp run.")

    return final_path


def build_output_name(input_path: Path, time_range: TimeRange) -> str:
    stem = input_path.stem
    start_tag = int(time_range.start_seconds)
    end_tag = int(time_range.end_seconds)
    return f"{stem}__{start_tag}-{end_tag}_480p.mp4"


def build_trimmed_name(input_path: Path, time_range: TimeRange) -> str:
    stem = input_path.stem
    start_tag = int(time_range.start_seconds)
    end_tag = int(time_range.end_seconds)
    return f"{stem}__{start_tag}-{end_tag}_trim.mp4"


def trim_to_original_quality(
    input_file: Path,
    output_dir: Path,
    time_range: TimeRange,
) -> Path:
    """
    Fast trim using stream copy. This may cut on keyframes (approximate).
    """
    output_name = build_trimmed_name(input_file, time_range)
    output_path = output_dir / output_name

    duration = time_range.duration_seconds
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{time_range.start_seconds:.3f}",
        "-i",
        str(input_file),
        "-t",
        f"{duration:.3f}",
        "-c",
        "copy",
        str(output_path),
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("ffmpeg failed to create trimmed clip:", e, file=sys.stderr)
        raise

    return output_path


def trim_and_compress_to_480p(
    input_file: Path,
    output_dir: Path,
    time_range: TimeRange,
) -> Path:
    output_name = build_output_name(input_file, time_range)
    output_path = output_dir / output_name

    # Use accurate seeking by placing -ss and -to after the input
    # Scale to 480p height, keep aspect ratio, even width
    # Aim for small size: CRF 28 and slow preset (tune=film helps perceptual quality slightly)
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-ss",
        f"{time_range.start_seconds:.3f}",
        "-to",
        f"{time_range.end_seconds:.3f}",
        "-vf",
        "scale=-2:480",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "28",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        str(output_path),
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("ffmpeg failed to trim/compress the video:", e, file=sys.stderr)
        raise

    return output_path


def validate_and_build_range(start_text: str, stop_text: str) -> TimeRange:
    start = parse_timestamp_to_seconds(start_text)
    end = parse_timestamp_to_seconds(stop_text)
    if end <= start:
        raise ValueError("Stop timestamp must be greater than start timestamp")
    return TimeRange(start, end)


def main() -> None:
    print("Please Insert Youtube Video Link: ", end="")
    url = ask("")
    print("Please Insert start timestamp (mm:ss): ", end="")
    start_ts = ask("")
    print("Please Insert stop timestamp (mm:ss): ", end="")
    stop_ts = ask("")

    # Resolve directories
    project_root = Path(__file__).resolve().parent
    downloads_dir, trimmed_dir, compressed_dir = ensure_directories(project_root / "downloads")

    # Validate range
    try:
        time_range = validate_and_build_range(start_ts, stop_ts)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure ffmpeg exists before doing the download work (fail fast)
    check_ffmpeg_available()

    # Download into a temporary directory so full video is not retained
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = Path(tmpdir)
        print("\nDownloading video with yt-dlp...\n")
        try:
            input_file = download_video(url, tmp_dir_path)
        except Exception as e:
            print(f"Failed to download video: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Downloaded to temporary file: {input_file}")

        # Create trimmed original-quality clip
        print("\nCreating trimmed clip (original quality, fast)...\n")
        try:
            trimmed_path = trim_to_original_quality(input_file, trimmed_dir, time_range)
        except Exception as e:
            print(f"Failed to create trimmed clip: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Trimmed clip saved to: {trimmed_path}")

        # Create compressed 480p clip directly from the original input for best quality
        print("\nTrimming and compressing to 480p (this may take a while)...\n")
        try:
            compressed_path = trim_and_compress_to_480p(input_file, compressed_dir, time_range)
        except Exception as e:
            print(f"Failed to trim/compress: {e}", file=sys.stderr)
            sys.exit(1)

    # Temporary directory cleaned up automatically here; full video not retained
    print(f"\nDone!\n - Trimmed: {trimmed_path}\n - Compressed: {compressed_path}")


if __name__ == "__main__":
    main()