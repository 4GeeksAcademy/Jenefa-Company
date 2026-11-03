# HealthCore host-hardening evidence

These deployment-owned controls close the host-hardening gates in the OWASP
audit without pretending that the repository can prove the state of a remote
production host.

## Apply

Review the target host, then run as root with an explicit opt-in:

```bash
HC_APPLY_HOST_HARDENING=YES \
HC_REPO_ROOT=/opt/healthcore \
HC_SSH_PORT=2222 \
./SecureAI/host-hardening/apply-host-hardening.sh
```

The script creates or reuses the unprivileged `hc-runtime` user, disables SSH
root/password login, applies a default-deny UFW policy with HTTPS and the
configured SSH port, and separates read-only application code, restricted
environment files, and writable logs.

## Verify and retain evidence

```bash
HC_REPO_ROOT=/opt/healthcore \
./SecureAI/host-hardening/verify-host-hardening.sh | tee host-hardening-evidence.txt
```

The output is deployment evidence and must be retained with the release record.
The verifier fails closed when `sshd`, UFW, permissions, or the runtime user do
not meet the baseline.
