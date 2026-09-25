#!/bin/sh
# One-time setup so headless Chromium can load pages in a Claude Code cloud
# container: the Playwright Python package, plus the agent proxy's CA in
# Chromium's NSS trust store (curl and Python read it from env; Chromium doesn't).
set -e
python3 -c "import playwright" 2>/dev/null || pip install -q playwright==1.56.0
command -v certutil >/dev/null || { apt-get update -qq && apt-get install -y -qq libnss3-tools; } >/dev/null
DB="sql:$HOME/.pki/nssdb"
mkdir -p "$HOME/.pki/nssdb"
[ -f "$HOME/.pki/nssdb/cert9.db" ] || certutil -N -d "$DB" --empty-password
for ca in /root/.ccr/agent-proxy-ca.crt /root/.ccr/system-trust.ca.pem; do
  [ -f "$ca" ] || continue
  dir=$(mktemp -d)
  csplit -s -z -f "$dir/c-" "$ca" '/-----BEGIN CERTIFICATE-----/' '{*}'
  for c in "$dir"/c-*; do certutil -A -d "$DB" -n "$(basename "$ca")-$(basename "$c")" -t "C,," -i "$c"; done
  rm -rf "$dir"
done
