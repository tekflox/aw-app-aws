#!/usr/bin/env bash
# Reverses install_aws.sh. Called on app uninstall (journal replay per the
# ADR's Decision 7 — this script IS the revert action for the commands:install
# journal entry).
set -euo pipefail

rm -rf /usr/local/aws-cli
rm -f /usr/local/bin/aws /usr/local/bin/aws_completer
