"""
`aws configure set` wiring — applies stored credentials to the workspace's
``~/.aws/credentials`` / ``~/.aws/config``. Kept as pure functions (no
framework coupling) so they're easy to unit-test with a mocked subprocess.run,
mirroring aw-app-git's git_app/gh_auth.py.
"""

from __future__ import annotations

import subprocess

_FIELD_TO_AWS_KEY = {
    "aws_access_key_id": "aws_access_key_id",
    "aws_secret_access_key": "aws_secret_access_key",
    "aws_default_region": "region",
    "aws_session_token": "aws_session_token",
}


class AwsConfigureError(RuntimeError):
    pass


def configure_set(key: str, value: str, profile: str = "default") -> None:
    """Runs `aws configure set <key> <value> --profile <profile>`."""
    result = subprocess.run(
        ["aws", "configure", "set", key, value, "--profile", profile],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AwsConfigureError(f"aws configure set {key} failed: {result.stderr.strip()}")


def apply_credentials(values: dict, profile: str = "default") -> list[str]:
    """Applies whichever of the known credential fields are present in
    ``values`` (a dict keyed by the config_schema property names) via
    `aws configure set`. Returns the list of aws config keys that were set."""
    applied = []
    for field, aws_key in _FIELD_TO_AWS_KEY.items():
        value = values.get(field)
        if value:
            configure_set(aws_key, str(value), profile=profile)
            applied.append(aws_key)
    return applied


def status(profile: str = "default") -> dict:
    """Returns whether a profile has an access key configured, via
    `aws configure list`. Never calls AWS itself (no network dependency —
    this only inspects local config)."""
    result = subprocess.run(
        ["aws", "configure", "list", "--profile", profile],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = f"{result.stdout}\n{result.stderr}".strip()
    access_key_line = next(
        (line for line in result.stdout.splitlines() if line.strip().startswith("access_key")),
        "",
    )
    configured = result.returncode == 0 and "<not set>" not in access_key_line and bool(access_key_line)
    return {"configured": configured, "raw": combined}
