#!/usr/bin/env bash
set -eo pipefail
U="${USER:-$(id -un)}"
if ! psql -d postgres -c "SELECT 1" >/dev/null 2>&1; then
  echo "Postgres se connect nahi ho pa raha ($U ke naam se)."
  echo "  sudo -u postgres psql -c \"CREATE ROLE $U LOGIN CREATEDB\""
  exit 1
fi
psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='shopdb'" | grep -q 1 || createdb shopdb
bash "$(dirname "$0")/reset.sh"
echo "shopdb ready"
