#!/usr/bin/env bash
# Usage: ./build.sh topics/<naam>
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
FPS="${FPS:-15}"
PROMPT_USER="${PROMPT_USER:-$(id -un)}"
PROMPT_HOST="${PROMPT_HOST:-$(hostname -s)}"
PROMPT_DIR="${PROMPT_DIR:-~}"
export PROMPT_TEXT="${PROMPT_USER}@${PROMPT_HOST}:${PROMPT_DIR}$ "
[ $# -eq 1 ] && [ -d "$1/steps" ] || { echo "Usage: ./build.sh topics/<naam>"; exit 1; }
TOPIC="$(cd "$1" && pwd)"
NAME="$(basename "$TOPIC")"

for c in vhs ffmpeg ffprobe edge-tts python3 script; do
  command -v "$c" >/dev/null || { echo "Missing tool: $c"; exit 1; }
done

# ---- safety check: commands har build pe dobara chalti hain ----
DANGER='(^|[;&| (])(su|rm|rmdir|dd|mkfs|shutdown|reboot|poweroff|apt|apt-get|dnf|yum|snap|pip|npm|systemctl|kill|pkill|killall|chmod|chown|mv|passwd|useradd|userdel|crontab|iptables|ufw)( |$)|kubectl +(delete|apply|scale|edit|drain)|docker +(rm|rmi|stop|kill|prune|system)|(^|[^0-9&])>{1,2} *([^&/ 0-9]|/[^d])|\b(top|htop|vim|vi|nano|less|more|watch|ssh)\b|tail +-f|`'
bad=0
for f in $(ls "$TOPIC"/steps/*.cmd "$TOPIC"/steps/*.session 2>/dev/null); do
  cmd=$(grep -v '^[[:space:]]*#' "$f" | grep -v '^[[:space:]]*$' || true)
  if echo "$cmd" | grep -Eq "$DANGER"; then
    echo "KHATRA: $(basename "$f"): $cmd"; bad=1
  fi
done
if [ $bad -eq 1 ] && [ "${ALLOW_DANGEROUS:-0}" != "1" ]; then
  echo "Yeh commands har build pe dobara chalengi (system badal sakti hain ya kabhi khatam nahi hongi)."
  echo "Pakka safe ho to: ALLOW_DANGEROUS=1 ./build.sh $1"
  exit 1
fi

frames_to_mp4() {   # $1 = frames dir, $2 = output mp4
  ffmpeg -y -loglevel error \
    -thread_queue_size 512 -framerate $FPS -i "$1/frame-text-%05d.png" \
    -thread_queue_size 512 -framerate $FPS -i "$1/frame-cursor-%05d.png" \
    -filter_complex "[0][1]overlay,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x282a36,format=yuv420p" \
    -c:v libx264 -preset ultrafast -crf 20 "$2"
}

tape_header() {   # $1 = frames dir, $2 = working dir
  cat <<T
Output $1/
Set Framerate $FPS
Set Shell "bash"
Set FontSize 20
Set Width 1280
Set Height 720
Set Padding 30
Set TypingSpeed 30ms
Set Theme "Dracula"

Hide
Type \`cd '$2' && export PS1='\[\e[01;32m\]${PROMPT_USER}@${PROMPT_HOST}\[\e[00m\]:\[\e[01;34m\]${PROMPT_DIR}\[\e[00m\]$ ' PAGER=cat PSQL_PAGER=cat && alias ls='ls --color=auto' && alias grep='grep --color=auto'\`
Enter
Type "clear"
Enter
T
}

# ---- calibration (sirf ek baar, kit level pe) ----
if [ ! -f "$KIT/calib/calib.json" ]; then
  echo ">> Calibration (sirf pehli baar)"
  rm -rf "$KIT/calib/frames"
  { tape_header "frames" "$KIT/calib"
    printf 'Type "python3 calib_print.py"\nEnter\nSleep 1500ms\nShow\nSleep 1s\n'; } > "$KIT/calib/calib.tape"
  (cd "$KIT/calib" && vhs calib.tape >/dev/null)
  frames_to_mp4 "$KIT/calib/frames" "$KIT/calib/calib-term.mp4"
  python3 "$KIT/highlight.py" calibrate
fi

mkdir -p "$TOPIC/build"
cd "$TOPIC"
if [ -f cleanup.sh ]; then trap 'bash "$TOPIC/cleanup.sh" || true' EXIT; fi
if [ -f setup.sh ]; then echo ">> setup.sh"; bash setup.sh; fi

echo ">> Patterns check"
python3 "$KIT/highlight.py" check "$TOPIC" || { echo "Pehle patterns theek karo (upar MISS dekho)."; exit 1; }

: > build/list.txt
for f in $(ls steps/*.cmd steps/*.session 2>/dev/null | sort); do
  st=$(basename "$f"); st="${st%.*}"
  wait=$(grep -oP '^#\s*wait\s+\K[\d.]+' "$f" || echo 3)
  if [ "${FORCE:-0}" != "1" ] && [ -f "build/$st.mp4" ] \
     && [ "build/$st.mp4" -nt "steps/$st.cmd" ] && [ "build/$st.mp4" -nt "narration/$st.txt" ]; then
    echo ">> Step $st: pehle se bana hai, skip (dobara banana ho to FORCE=1)"
    echo "file '$st.mp4'" >> build/list.txt
    continue
  fi
  echo ">> Step $st: terminal"
  [ -f "steps/$st.pre" ] && bash "steps/$st.pre" >/dev/null 2>&1
  rm -rf "build/$st-frames"
  { tape_header "build/$st-frames" "$TOPIC"
    printf 'Show\n\nSleep 500ms\n'
    first=1
    grep -v '^[[:space:]]*#' "$f" | grep -v '^[[:space:]]*$' | while IFS= read -r line; do
      if [ $first -eq 1 ]; then first=0; else printf 'Sleep 700ms\n'; fi
      printf 'Type `%s`\nSleep 300ms\nEnter\n' "$line"
    done
    printf 'Sleep %ss\n' "$wait"; } > "build/$st.tape"
  vhs "build/$st.tape" >/dev/null
  frames_to_mp4 "build/$st-frames" "build/$st-term.mp4"
  echo ">> Step $st: awaaz + highlight"
  python3 "$KIT/highlight.py" step "$TOPIC" "$st"
  echo "file '$st.mp4'" >> build/list.txt
done

ffmpeg -y -loglevel error -f concat -safe 0 -i build/list.txt -c copy "$TOPIC/$NAME.mp4"
echo "Ban gayi: $TOPIC/$NAME.mp4"
