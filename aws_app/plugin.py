"""
Entrypoint referenced by aw-app.json's runtime.entrypoint
("aws_app.plugin:AwsAppPlugin").

Plugs into the real F4 framework runtime and uses the gated ``ctx`` facades
rather than raw shell:

* ``ctx.commands`` (``commands:install``) — install the `aws` CLI THROUGH the
  facade (journaled; reverted on uninstall via scripts/uninstall.sh).
* ``ctx.secrets`` (``secrets:own``) — access key / secret key / region /
  session token live in the workspace-side secure store; the app applies
  them via `aws configure set` on activate, and the settings route writes +
  re-applies them. Mirrors aw-app-git's ``github_token`` handling.
* ``ctx.routes`` (``routes:register``) — a small settings sub-app to save
  credentials + read configured status.
"""

from __future__ import annotations

import json
import logging
import os

from . import aws_configure

log = logging.getLogger("aw_apps.aws")

_CONFIG_FIELDS = (
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_default_region",
    "aws_session_token",
)


def _stored_credentials(ctx) -> dict:
    return {field: ctx.secrets.read(field) for field in _CONFIG_FIELDS if ctx.secrets.read(field)}


class AwsAppPlugin:
    async def activate(self, ctx) -> None:
        self.ctx = ctx
        with open(os.path.join(ctx.package_dir, "aw-app.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        for cli in manifest.get("contributes", {}).get("system_clis", []):
            # `verify` decides what "installed" MEANS: a command that has to
            # succeed, not just the name being on PATH. Defaults to
            # `<name> --version` when the manifest doesn't say otherwise.
            ctx.commands.install_system_cli(
                cli["name"], cli["installer"], uninstall="scripts/uninstall.sh",
                verify=cli.get("verify"),
            )
        log.info("aw-app-aws activated: aws cli installed")

        # If credentials are already stored, apply them now — this also runs
        # on every reconcile pass after workspace recreation.
        stored = _stored_credentials(ctx)
        if stored:
            try:
                applied = aws_configure.apply_credentials(stored)
                log.info("aws configure: applied %s from stored credentials", applied)
            except aws_configure.AwsConfigureError as e:
                log.warning("aws configure: failed to apply stored credentials: %s", e)

        ctx.routes.register(self._build_routes(ctx))

    async def deactivate(self) -> None:
        # aws cli removal is driven by the framework's journal reverse-replay
        # (scripts/uninstall.sh); the secret namespace is purged by the runtime.
        log.info("aw-app-aws deactivated")

    def _build_routes(self, ctx):
        from fastapi import Body, FastAPI

        api = FastAPI()

        @api.post("/settings")
        async def save_settings(data: dict = Body(...)):
            """Generic config-window submit (the framework's Apps view posts
            here). Routes the `x-secret` fields (aws_secret_access_key,
            aws_session_token) and the plain ones (aws_access_key_id,
            aws_default_region) to the secret store, then applies whichever
            fields were given via `aws configure set`. Fields are all
            optional so a partial save (e.g. only the region) works."""
            values = {field: data[field] for field in _CONFIG_FIELDS if data.get(field)}
            if not values:
                return {"ok": True, "applied": []}
            for field, value in values.items():
                ctx.secrets.write(field, value)
            try:
                applied = aws_configure.apply_credentials(values)
                return {"ok": True, "applied": applied}
            except aws_configure.AwsConfigureError as e:
                return {"ok": True, "applied": [], "error": str(e)}

        @api.get("/status")
        async def status():
            has_credentials = "aws_access_key_id" in ctx.secrets.keys()
            aws_status = aws_configure.status()
            return {
                "has_credentials": has_credentials,
                "region": ctx.secrets.read("aws_default_region"),
                **aws_status,
            }

        @api.post("/logout")
        async def logout():
            """Drops the stored credentials — the settings window's
            Logout/Clear button once credentials are configured. Does not
            unset the local `aws configure` profile (a fresh apply on the
            next activate/reconcile would just re-write it if left in place;
            clearing it is out of scope for this route)."""
            for field in _CONFIG_FIELDS:
                ctx.secrets.delete(field)
            return {"ok": True}

        return api
