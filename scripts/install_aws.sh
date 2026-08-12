#!/usr/bin/env bash
# Installs the AWS CLI v2 into the workspace via the official awscli-exe-linux
# bundle (no apt package — Debian/Ubuntu ship v1 or nothing). Idempotent — safe
# to re-run (on install, and on every reconcile pass after workspace recreation).
#
# Everything privileged goes through sudo: the workspace container's default
# user is unprivileged `ubuntu` (uid 1001) with NOPASSWD sudo baked into the
# image. This script used to call apt-get and write to /usr/local directly, so
# it failed on EVERY boot with "Could not open lock file /var/lib/apt/lists/lock
# - open (13: Permission denied)" and the CLI was never actually installed.
set -euo pipefail

if command -v aws >/dev/null 2>&1; then
  echo "aws already installed: $(aws --version)"
  exit 0
fi

# Extraction without depending on `unzip`, which the workspace image does not
# ship. python3 is always present (it is a Python image) and zipfile is stdlib,
# so nothing has to be installed just to open the bundle. Falling back to apt
# for it is the last resort, not the first move.
extract_zip() {
  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$1" -d "$2"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$1" "$2"
  elif command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    sudo -n apt-get update -qq
    sudo -n apt-get install -y --no-install-recommends unzip
    unzip -q "$1" -d "$2"
  else
    echo "install_aws.sh: need unzip or python3 to extract the installer bundle" >&2
    return 1
  fi
}

command -v curl >/dev/null 2>&1 || {
  echo "install_aws.sh: curl not found on this system — unsupported base image" >&2
  exit 1
}

case "$(uname -m)" in
  x86_64) ARCH="x86_64" ;;
  aarch64|arm64) ARCH="aarch64" ;;
  *)
    echo "install_aws.sh: unsupported architecture $(uname -m)" >&2
    exit 1
    ;;
esac

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" -o "$WORKDIR/awscliv2.zip"
extract_zip "$WORKDIR/awscliv2.zip" "$WORKDIR"
# python3 -m zipfile drops the archive's mode bits, so the installer comes out
# non-executable when that is the path taken.
chmod +x "$WORKDIR/aws/install" "$WORKDIR/aws/dist/aws" 2>/dev/null || true
sudo -n "$WORKDIR/aws/install" --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update

aws --version
