#!/usr/bin/env python3
"""Batch process videos into 9:16 vertical 1080p outputs with max 15s duration."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv", ".webm", ".m4v"}
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
MAX_DURATION_SECONDS = 15.0


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def ffprobe_metadata(video_path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = run_command(cmd)
    return json.loads(result.stdout)


def get_duration_seconds(metadata: dict, file_path: Path) -> float:
    duration_str = metadata.get("format", {}).get("duration")
    if duration_str is None:
        raise ValueError(f"无法读取时长: {file_path}")
    return float(duration_str)


def has_audio_stream(metadata: dict) -> bool:
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "audio":
            return True
    return False


def build_atempo_filter(speed_factor: float) -> str:
    factors: list[float] = []
    remaining = speed_factor

    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0

    factors.append(remaining)
    return ",".join(f"atempo={factor:.8f}" for factor in factors)


def process_video(input_path: Path, output_path: Path) -> None:
    metadata = ffprobe_metadata(input_path)
    duration = get_duration_seconds(metadata, input_path)
    audio_exists = has_audio_stream(metadata)

    speed_factor = 1.0
    if duration > MAX_DURATION_SECONDS:
        speed_factor = duration / MAX_DURATION_SECONDS

    vf_chain = [
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT}",
    ]
    if speed_factor > 1.0:
        vf_chain.append(f"setpts=PTS/{speed_factor:.8f}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        ",".join(vf_chain),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "medium",
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
    ]

    if speed_factor > 1.0 and audio_exists:
        cmd.extend(["-af", build_atempo_filter(speed_factor)])

    cmd.append(str(output_path))

    print(f"处理: {input_path.name}")
    if speed_factor > 1.0:
        print(f"  - 原始时长 {duration:.2f}s，已加速 {speed_factor:.4f}x 到 <= {MAX_DURATION_SECONDS:.0f}s")
    else:
        print(f"  - 原始时长 {duration:.2f}s，无需加速")

    run_command(cmd)
    print(f"  - 输出: {output_path}\n")


def collect_videos(input_dir: Path, recursive: bool) -> list[Path]:
    iterator = input_dir.rglob("*") if recursive else input_dir.glob("*")
    files = [p for p in iterator if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
    return sorted(files)


def ensure_ffmpeg_tools() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise EnvironmentError(f"未找到 {tool}，请先安装 FFmpeg 工具链")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="依次处理目录中的视频：转 9:16 竖屏 1080p，时长超过 15 秒则均匀加速到 15 秒内。"
    )
    parser.add_argument("input_dir", nargs="?", default=".", help="输入目录，默认当前目录")
    parser.add_argument("-o", "--output-dir", default="output", help="输出目录，默认 ./output")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"输入目录不存在或不是目录: {input_dir}", file=sys.stderr)
        return 1

    try:
        ensure_ffmpeg_tools()
    except EnvironmentError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    videos = collect_videos(input_dir, args.recursive)
    if not videos:
        print("未找到可处理的视频文件。")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    for video in videos:
        output_name = f"{video.stem}_9x16_1080p{video.suffix.lower()}"
        output_path = output_dir / output_name

        try:
            process_video(video, output_path)
        except subprocess.CalledProcessError as exc:
            print(f"处理失败: {video}", file=sys.stderr)
            if exc.stderr:
                print(exc.stderr, file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"处理失败: {video} - {exc}", file=sys.stderr)

    print(f"全部任务完成，输出目录: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
