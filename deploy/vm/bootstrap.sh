#!/usr/bin/env bash
# SlateIQ VM bootstrap — runs as the GCE *startup-script* (root, every boot; idempotent).
# Debian 12. Installs Docker CE + compose plugin, adds a 2 GiB swapfile, and prepares
# /opt/slateiq for the compose bundle that create_vm.sh / deploy_stack.sh copies up.
# Deliberately does NOT install the Ops Agent: it costs ~120 MB RSS we cannot spare on a
# 1 GiB e2-micro (and Cloud Logging/Monitoring ingest is another billable surface).
set -euo pipefail
exec > >(tee -a /var/log/slateiq-bootstrap.log) 2>&1
echo "=== slateiq bootstrap $(date -Is) ==="

export DEBIAN_FRONTEND=noninteractive
STACK_DIR=/opt/slateiq

# ---------------------------------------------------------------- 1. swap (2 GiB)
if ! swapon --show=NAME --noheadings | grep -q '/swapfile'; then
  echo "--- creating 2G swapfile"
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
# Swap is a safety net, not a workload target: only spill under real pressure.
sysctl -w vm.swappiness=10 >/dev/null
sysctl -w vm.overcommit_memory=1 >/dev/null   # ClickHouse asks for this
grep -q '^vm.swappiness' /etc/sysctl.d/99-slateiq.conf 2>/dev/null || cat > /etc/sysctl.d/99-slateiq.conf <<'SYSCTL'
vm.swappiness=10
vm.overcommit_memory=1
SYSCTL

# ---------------------------------------------------------------- 2. docker + compose
if ! command -v docker >/dev/null 2>&1; then
  echo "--- installing docker ce"
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg jq
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker

# Cap the docker daemon's own log/metric footprint.
if [ ! -f /etc/docker/daemon.json ]; then
  mkdir -p /etc/docker
  cat > /etc/docker/daemon.json <<'DJSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "2" }, "live-restore": true }
DJSON
  systemctl restart docker
fi

# Let the login user drive compose without sudo.
for u in $(ls /home 2>/dev/null); do usermod -aG docker "$u" 2>/dev/null || true; done

# ---------------------------------------------------------------- 3. stack dir
mkdir -p "$STACK_DIR" "$STACK_DIR/seed"
chmod 0777 "$STACK_DIR/seed"          # so scp'd parquet from the login user lands here
chmod 0775 "$STACK_DIR"
chgrp docker "$STACK_DIR" 2>/dev/null || true

# ---------------------------------------------------------------- 4. bring the stack up if already provisioned
# (On a reboot the compose bundle is already on disk; `restart: unless-stopped` normally
#  handles this, but this makes a cold boot self-healing.)
if [ -f "$STACK_DIR/docker-compose.yml" ] && [ -f "$STACK_DIR/.env" ]; then
  echo "--- compose bundle present, starting stack"
  (cd "$STACK_DIR" && docker compose up -d --remove-orphans) || true
fi

# ---------------------------------------------------------------- 5. housekeeping
# Weekly prune so a 30 GB pd-standard never fills with dangling images.
cat > /etc/cron.weekly/slateiq-docker-prune <<'CRON'
#!/bin/sh
docker image prune -af --filter "until=168h" >/dev/null 2>&1
docker builder prune -af --filter "until=168h" >/dev/null 2>&1
CRON
chmod +x /etc/cron.weekly/slateiq-docker-prune

touch /var/run/slateiq-bootstrap-done
echo "=== slateiq bootstrap complete $(date -Is) ==="
free -m
