#!/usr/bin/env bash
set -u

runtime_user="${HC_RUNTIME_USER:-hc-runtime}"
repo_root="${HC_REPO_ROOT:-/opt/healthcore}"
log_dir="${HC_LOG_DIR:-/var/log/healthcore}"
env_file="${HC_ENV_FILE:-${repo_root}/.env}"
failures=0

check() {
  local description="$1"
  shift
  if "$@"; then
    printf 'PASS: %s\n' "${description}"
  else
    printf 'FAIL: %s\n' "${description}"
    failures=$((failures + 1))
  fi
}

check_runtime_user() {
  [[ "$(id -u "${runtime_user}" 2>/dev/null || echo 0)" -ne 0 ]]
}

check_ssh() {
  command -v sshd >/dev/null &&
    sshd -T 2>/dev/null | grep -Eq '^permitrootlogin no$' &&
    sshd -T 2>/dev/null | grep -Eq '^passwordauthentication no$' &&
    sshd -T 2>/dev/null | grep -Eq '^pubkeyauthentication yes$'
}

check_firewall() {
  command -v ufw >/dev/null &&
    ufw status verbose 2>/dev/null | grep -Eq 'Default: deny \(incoming\)' &&
    ufw status 2>/dev/null | grep -Eq '443/tcp.*ALLOW'
}

check_code_permissions() {
  [[ -d "${repo_root}" ]] &&
    ! find "${repo_root}" -xdev -type f -perm /022 -print -quit | grep -q .
}

check_log_permissions() {
  [[ -d "${log_dir}" ]] &&
    [[ "$(stat -c '%a' "${log_dir}" 2>/dev/null)" =~ ^7[05]0$ ]]
}

check_env_permissions() {
  [[ ! -e "${env_file}" ]] ||
    [[ "$(stat -c '%a' "${env_file}" 2>/dev/null)" =~ ^6[04]0$ ]]
}

check "application does not run as root" check_runtime_user
check "SSH disables root and password login" check_ssh
check "firewall defaults to deny and allows HTTPS" check_firewall
check "application code is not group/world writable" check_code_permissions
check "log directory is the dedicated writable target" check_log_permissions
check "environment secrets are not world-readable" check_env_permissions

if [[ "${failures}" -ne 0 ]]; then
  printf '%s host-hardening checks failed.\n' "${failures}" >&2
  exit 1
fi
echo "All host-hardening checks passed."
