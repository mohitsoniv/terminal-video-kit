#!/usr/bin/env bash
set -eo pipefail
if ! sudo -n -u postgres psql -tAc "select 1" >/dev/null 2>&1; then
  echo "sudo -u postgres psql bina password nahi chal raha."
  echo "Recording rule lagao:"
  echo "  echo '$(id -un) ALL=(postgres) NOPASSWD: /usr/bin/psql' | sudo tee /etc/sudoers.d/vhs-recording"
  echo "  sudo chmod 0440 /etc/sudoers.d/vhs-recording"
  exit 1
fi
echo "postgres connection theek hai"
