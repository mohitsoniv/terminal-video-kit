#!/usr/bin/env bash
# Usage: ./new-topic.sh <naam>
set -euo pipefail
cd "$(dirname "$0")"
[ $# -eq 1 ] || { echo "Usage: ./new-topic.sh <naam>"; exit 1; }
T="topics/$1"
[ -e "$T" ] && { echo "$T pehle se hai"; exit 1; }
mkdir -p "$T/steps" "$T/narration"
cat > "$T/steps/01.cmd" <<'X'
# Is file mein sirf EK command likho (ek line).
# Output aane mein 3 second se zyada lage to upar likho:  # wait 6
echo "yahan apni command likho"
X
cat > "$T/setup.sh" <<'X'
#!/usr/bin/env bash
# (optional) video se pehle ki taiyari: server chalana, demo files banana.
# Yahan background process chalao to uska PID build/ mein save karo, cleanup.sh use band karega.
X
cat > "$T/cleanup.sh" <<'X'
#!/usr/bin/env bash
# (optional) video ke baad safai
X
echo "Bana diya: $T"
echo "Ab steps/01.cmd, 02.cmd ... mein commands likho, phir output Claude ko bhejo."
