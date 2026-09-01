#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
demo_dir="$repo_root/examples/bookmark-buddy"
assets_dir="$demo_dir/assets"
frames_dir="/Users/fitawrari/.openclaw/workspace-mehandisu/.tmp_video"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT

mkdir -p "$assets_dir"

durations=(10 12 22 14 24 10 12 10 6)
frames=(
  s1_hook.png
  s2_intent.png
  s3_requirements.png
  s4_design.png
  s5_runsh.png
  s6_pass.png
  s7_agents.png
  s8_manifest.png
  s1_hook.png
)
narration=(
  "This is Bookmark Buddy, a tiny local-first C L I for saving and searching bookmarks. It starts from one plain-English intent."
  "Save, organize, and search bookmarks, all on your own machine. No accounts, cloud services, or hidden dependencies."
  "A human turns that intent into this requirements document, the source of truth. Specadia does not derive it; it is a reviewed, hand-authored input."
  "A short hand-authored design adds the architecture and file structure, making implementation choices visible before coding begins."
  "Now Specadia takes over. Generate runs twice with the same inputs, without credentials or a live model, then compares both outputs."
  "The runs are byte-for-byte identical, and no local absolute paths leak into the generated artifacts."
  "The coding-agent contract maps every requirement and acceptance criterion back to its reviewed source."
  "The manifest hashes each input and output, creating a compact, verifiable chain from source documents to contract."
  "Install Specadia from Pie P I, and give your coding agent a real contract."
)
captions=(
  "This is Bookmark Buddy, a tiny local-first CLI for saving and searching bookmarks. It starts from one plain-English intent."
  "Save, organize, and search bookmarks, all on your own machine. No accounts, cloud services, or hidden dependencies."
  "A human turns that intent into this requirements document, the source of truth. Specadia does not derive it; it is a reviewed, hand-authored input."
  "A short hand-authored design adds the architecture and file structure, making implementation choices visible before coding begins."
  "Now Specadia takes over. Generate runs twice with the same inputs, without credentials or a live model, then compares both outputs."
  "The runs are byte-for-byte identical, and no local absolute paths leak into the generated artifacts."
  "The coding-agent contract maps every requirement and acceptance criterion back to its reviewed source."
  "The manifest hashes each input and output, creating a compact, verifiable chain from source documents to contract."
  "Install Specadia from PyPI, and give your coding agent a real contract."
)

: > "$work_dir/concat.txt"

for i in "${!durations[@]}"; do
  index=$((i + 1))
  duration=${durations[$i]}
  frame="$frames_dir/${frames[$i]}"
  captioned_frame="$work_dir/frame-${index}.png"
  raw_audio="$work_dir/audio-${index}.mp3"
  padded_audio="$work_dir/audio-${index}.m4a"
  silent_video="$work_dir/video-${index}.mp4"
  scene="$work_dir/scene-${index}.mp4"

  test -f "$frame"
  image_url=$(python3 -c 'import pathlib, sys, urllib.parse; print(urllib.parse.quote(pathlib.Path(sys.argv[1]).as_uri(), safe=""))' "$frame")
  caption_url=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "${captions[$i]}")
  "$chrome" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --window-size=1920,1080 --force-device-scale-factor=1 \
    --screenshot="$captioned_frame" \
    "file://${repo_root}/scripts/caption_frame.html?image=${image_url}&caption=${caption_url}" >/dev/null 2>&1
  generated=false
  for attempt in 1 2 3; do
    if uvx --from edge-tts edge-tts \
      --voice en-US-AndrewMultilingualNeural \
      --rate=-4% \
      --text "${narration[$i]}" \
      --write-media "$raw_audio"; then
      generated=true
      break
    fi
    sleep 2
  done
  if [[ "$generated" != true ]]; then
    echo "Narration generation failed for scene ${index}" >&2
    exit 1
  fi

  audio_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$raw_audio")
  python3 - "$index" "$audio_duration" "$duration" <<'PY'
import sys

scene, audio_duration, scene_duration = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
if audio_duration > scene_duration - 0.25:
    raise SystemExit(
        f"Narration for scene {scene} is {audio_duration:.2f}s, "
        f"which does not fit safely within its {scene_duration:.2f}s scene"
    )
PY

  ffmpeg -hide_banner -loglevel error -y \
    -i "$raw_audio" \
    -af "loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=${duration},atrim=0:${duration}" \
    -c:a aac -b:a 160k "$padded_audio"

  fade_out=$((duration - 1))
  ffmpeg -hide_banner -loglevel error -y \
    -loop 1 -i "$captioned_frame" -t "$duration" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.25,fade=t=out:st=${fade_out}:d=0.25,format=yuv420p" \
    -r 30 -c:v libx264 -preset veryfast -crf 24 -an "$silent_video"

  ffmpeg -hide_banner -loglevel error -y \
    -i "$silent_video" -i "$padded_audio" \
    -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -shortest "$scene"

  printf "file '%s'\n" "$scene" >> "$work_dir/concat.txt"
done

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$work_dir/concat.txt" -c copy "$work_dir/base.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work_dir/base.mp4" \
  -c:v libx264 -preset medium -crf 25 -maxrate 3M -bufsize 6M \
  -c:a aac -b:a 160k -movflags +faststart \
  "$assets_dir/specadia-bookmark-buddy-demo.mp4"

cp "$frames_dir/s1_hook.png" "$assets_dir/specadia-bookmark-buddy-demo-poster.png"

ffprobe -v error -show_entries stream=index,codec_name,codec_type,width,height -show_entries format=duration,size -of json \
  "$assets_dir/specadia-bookmark-buddy-demo.mp4"
