#!/usr/bin/env bash
set -euo pipefail

if [[ "${HC_APPLY_HOST_HARDENING:-}" != "YES" ]]; then
  echo "Refusing to change the host. Set HC_APPLY_HOST_HARDENING=YES after review." >&2
  exit 2
fi
if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root on the deployment host." >&2
  exit 2
fi

runtime_user="${HC_RUNTIME_USER:-hc-runtime}"
ssh_port="${HC_SSH_PORT:-2222}"
repo_root="${HC_REPO_ROOT:-/opt/healthcore}"
log_dir="${HC_LOG_DIR:-/var/log/healthcore}"
env_file="${HC_ENV_FILE:-${repo_root}/.env}"

if ! id "${runtime_user}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "${runtime_user}"
fi
install -d -o "${runtime_user}" -g "${runtime_user}" -m 0750 "${log_dir}"
install -d -o root -g "${runtime_user}" -m 0750 "${repo_root}"
if [[ -f "${env_file}" ]]; then
  chown root:"${runtime_user}" "${env_file}"
  chmod 0640 "${env_file}"
fi
find "${repo_root}" -type d -exec chmod 0750 {} +
find "${repo_root}" -type f -exec chmod 0640 {} +
setfacl -m "u:${runtime_user}:rX" "${repo_root}"
setfacl -m "u:${runtime_user}:rwx" "${log_dir}"

install -d -m 0755 /etc/ssh/sshd_config.d
install -o root -g root -m 0644 \
  "$(dirname "$0")/sshd_config.d/healthcore.conf" \
  /etc/ssh/sshd_config.d/healthcore.conf
sshd -t
systemctl reload sshd 2>/dev/null || systemctl reload ssh

ufw default deny incoming
ufw default allow outgoing
ufw allow "${ssh_port}/tcp"
ufw allow 443/tcp
ufw --force enable

echo "HealthCore host hardening applied for ${runtime_user}; verify with verify-host-hardening.sh."
