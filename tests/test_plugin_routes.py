"""End-to-end test of the /settings + /status + /logout routes through a real
FastAPI TestClient, with aws_configure.configure_set/status monkeypatched (no
real `aws` binary needed) and a minimal fake ``ctx`` (secrets facade only —
the piece the routes actually touch).

Run: .venv/aw/bin/python -m pytest tests/test_plugin_routes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aws_app import aws_configure, plugin  # noqa: E402


class FakeSecrets:
    def __init__(self):
        self.store: dict[str, str] = {}

    def read(self, key):
        return self.store.get(key)

    def write(self, key, value):
        self.store[key] = value
        return {"key": key, "written": True}

    def delete(self, key):
        removed = key in self.store
        self.store.pop(key, None)
        return {"key": key, "deleted": removed}

    def keys(self):
        return list(self.store)


class FakeCtx:
    def __init__(self):
        self.secrets = FakeSecrets()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(aws_configure, "configure_set", lambda key, value, profile="default": None)
    ctx = FakeCtx()
    app = plugin.AwsAppPlugin()
    api = app._build_routes(ctx)
    return TestClient(api), ctx


def test_save_settings_writes_secrets_and_applies(client, monkeypatch):
    tc, ctx = client
    applied = []
    monkeypatch.setattr(
        aws_configure,
        "configure_set",
        lambda key, value, profile="default": applied.append((key, value)),
    )
    resp = tc.post(
        "/settings",
        json={
            "aws_access_key_id": "AKIAEXAMPLE",
            "aws_secret_access_key": "shh",
            "aws_default_region": "sa-east-1",
        },
    )
    body = resp.json()
    assert body["ok"] is True
    assert sorted(body["applied"]) == ["aws_access_key_id", "aws_secret_access_key", "region"]
    assert ctx.secrets.read("aws_access_key_id") == "AKIAEXAMPLE"
    assert ctx.secrets.read("aws_secret_access_key") == "shh"
    assert ctx.secrets.read("aws_default_region") == "sa-east-1"
    assert ("aws_access_key_id", "AKIAEXAMPLE") in applied


def test_save_settings_partial_field_only(client, monkeypatch):
    tc, ctx = client
    applied = []
    monkeypatch.setattr(
        aws_configure,
        "configure_set",
        lambda key, value, profile="default": applied.append((key, value)),
    )
    resp = tc.post("/settings", json={"aws_default_region": "us-west-2"})
    body = resp.json()
    assert body["ok"] is True
    assert body["applied"] == ["region"]
    assert ctx.secrets.read("aws_default_region") == "us-west-2"


def test_save_settings_no_fields_is_noop(client):
    tc, _ = client
    resp = tc.post("/settings", json={})
    assert resp.json() == {"ok": True, "applied": []}


def test_save_settings_configure_error_surfaces(client, monkeypatch):
    tc, _ = client

    def raise_error(key, value, profile="default"):
        raise aws_configure.AwsConfigureError("aws configure set failed: boom")

    monkeypatch.setattr(aws_configure, "configure_set", raise_error)
    resp = tc.post("/settings", json={"aws_default_region": "us-west-2"})
    body = resp.json()
    assert body["ok"] is True
    assert body["applied"] == []
    assert "boom" in body["error"]


def test_status_reports_configured_state(client, monkeypatch):
    tc, ctx = client
    ctx.secrets.write("aws_access_key_id", "AKIAEXAMPLE")
    ctx.secrets.write("aws_default_region", "sa-east-1")
    monkeypatch.setattr(
        aws_configure, "status", lambda profile="default": {"configured": True, "raw": "ok"}
    )
    resp = tc.get("/status")
    body = resp.json()
    assert body["has_credentials"] is True
    assert body["region"] == "sa-east-1"
    assert body["configured"] is True


def test_status_reports_unconfigured_when_no_secrets(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(
        aws_configure, "status", lambda profile="default": {"configured": False, "raw": "<not set>"}
    )
    resp = tc.get("/status")
    body = resp.json()
    assert body["has_credentials"] is False
    assert body["configured"] is False


def test_logout_clears_stored_credentials(client):
    tc, ctx = client
    ctx.secrets.write("aws_access_key_id", "AKIAEXAMPLE")
    ctx.secrets.write("aws_secret_access_key", "shh")
    resp = tc.post("/logout")
    assert resp.json() == {"ok": True}
    assert "aws_access_key_id" not in ctx.secrets.keys()
    assert "aws_secret_access_key" not in ctx.secrets.keys()
