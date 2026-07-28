#!/usr/bin/env bash
# Standalone test — no framework runtime required. Run this INSIDE the
# aw-workspace container (as root) to prove the install script actually
# installs the AWS CLI v2 and that `aws --version` works after.
#
# Usage (from inside the container, with this repo copied in):
#   bash tests/standalone_test.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== install_aws.sh =="
bash scripts/install_aws.sh

echo "== version =="
aws --version

echo "== aws configure list (expected: not configured yet) =="
aws configure list 2>&1 || true

echo "OK: aws cli installed and functional"
