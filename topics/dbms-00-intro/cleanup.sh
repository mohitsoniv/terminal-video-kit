#!/usr/bin/env bash
sudo -n -u postgres psql -q -c "DROP DATABASE IF EXISTS shopdb;" >/dev/null 2>&1 || true
