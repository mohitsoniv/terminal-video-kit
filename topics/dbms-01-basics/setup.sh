#!/usr/bin/env bash
set -eo pipefail
U="${USER:-$(id -un)}"
if ! psql -d postgres -c "SELECT 1" >/dev/null 2>&1; then
  echo "Postgres se connect nahi ho pa raha ($U ke naam se)."
  echo "Ek baar yeh chalao, phir dobara build karo:"
  echo "  sudo -u postgres psql -c \"CREATE ROLE $U LOGIN CREATEDB\""
  exit 1
fi
echo "Postgres connection theek hai"
