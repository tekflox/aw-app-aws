"""Unit tests for aws_app/aws_configure.py.

Run: .venv/aw/bin/python -m pytest tests/test_aws_configure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aws_app import aws_configure  # noqa: E402


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_apply_credentials_maps_field_names(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return FakeResult()

    monkeypatch.setattr(aws_configure.subprocess, "run", fake_run)
    applied = aws_configure.apply_credentials(
        {
            "aws_access_key_id": "AKIAEXAMPLE",
            "aws_secret_access_key": "shh",
            "aws_default_region": "sa-east-1",
            "aws_session_token": "",
        }
    )
    assert applied == ["aws_access_key_id", "aws_secret_access_key", "region"]
    assert ["aws", "configure", "set", "region", "sa-east-1", "--profile", "default"] in calls


def test_apply_credentials_skips_empty_values(monkeypatch):
    monkeypatch.setattr(aws_configure.subprocess, "run", lambda cmd, **kw: FakeResult())
    assert aws_configure.apply_credentials({}) == []


def test_configure_set_raises_on_failure(monkeypatch):
    monkeypatch.setattr(
        aws_configure.subprocess,
        "run",
        lambda cmd, **kw: FakeResult(returncode=1, stderr="boom"),
    )
    try:
        aws_configure.configure_set("region", "us-east-1")
        assert False, "expected AwsConfigureError"
    except aws_configure.AwsConfigureError as e:
        assert "boom" in str(e)


def test_status_configured(monkeypatch):
    monkeypatch.setattr(
        aws_configure.subprocess,
        "run",
        lambda cmd, **kw: FakeResult(stdout="access_key     ****ABCD              config-file    ~/.aws/credentials\n"),
    )
    result = aws_configure.status()
    assert result["configured"] is True


def test_status_not_configured(monkeypatch):
    monkeypatch.setattr(
        aws_configure.subprocess,
        "run",
        lambda cmd, **kw: FakeResult(stdout="access_key     <not set>             None    None\n"),
    )
    result = aws_configure.status()
    assert result["configured"] is False
