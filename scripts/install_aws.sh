#!/usr/bin/env bash
# Installs the AWS CLI v2 into the workspace via the official awscli-exe-linux
# bundle (no apt package — Debian/Ubuntu ship v1 or nothing). Idempotent — safe
# to re-run (on install, and on every reconcile pass after workspace recreation).
set -euo pipefail

if command -v aws >/dev/null 2>&1; then
  echo "aws already installed: $(aws --version)"
  exit 0
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "install_aws.sh: no apt-get on this system — unsupported base image" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
if ! command -v curl >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y --no-install-recommends curl unzip
fi

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
unzip -q "$WORKDIR/awscliv2.zip" -d "$WORKDIR"
"$WORKDIR/aws/install" --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update

aws --version
