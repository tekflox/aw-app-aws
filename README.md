# aw-app-aws

Decoupled app for aw-workspace, mirroring
[`aw-app-git`](https://github.com/tekflox/aw-app-git)'s structure
(`aw-app.json` manifest schema v1). Installs the **AWS CLI v2** into the
workspace and provides a settings panel for AWS credentials (access key,
secret key, region, session token) applied via `aws configure`.

## Layout

- `aw-app.json` — the manifest (id `aws`, tier `inprocess`).
- `schemas/aw-app.schema.json` — local structural validator (same stand-in
  copied from `aw-app-git`, until the framework publishes its own).
- `scripts/install_aws.sh` — idempotent installer: downloads the official
  `awscli-exe-linux-<arch>` bundle (no apt package — Debian/Ubuntu don't ship
  AWS CLI v2) and runs its own `./aws/install`, pinned at
  `/usr/local/aws-cli` (`--bin-dir /usr/local/bin`). Detects `x86_64` /
  `aarch64`.
- `scripts/uninstall.sh` — removes `/usr/local/aws-cli` and the
  `/usr/local/bin/aws*` symlinks.
- `aws_app/plugin.py` — `AwsAppPlugin` entrypoint; `activate(ctx)` installs
  the CLI via `ctx.commands`, applies any already-stored credentials via
  `ctx.secrets` + `aws configure set`, and mounts the settings sub-app via
  `ctx.routes` (`POST /api/apps/aws/settings`, `GET /api/apps/aws/status`,
  `POST /api/apps/aws/logout`). Revert is driven by the framework's journal
  reverse-replay (runs `scripts/uninstall.sh`).
- `aws_app/aws_configure.py` — `configure_set()` / `apply_credentials()` /
  `status()`, the actual `aws configure` subprocess calls, framework-free and
  easy to unit-test with a mocked `subprocess.run` (mirrors `git_app/gh_auth.py`).
- `tests/validate_manifest.py` — validates `aw-app.json` against the schema +
  checks the `system_clis` installer path exists.
- `tests/test_aws_configure.py` — unit tests for `aws_configure.py`.
- `tests/test_plugin_routes.py` — `/settings`, `/status`, `/logout` through a
  real `FastAPI TestClient` with a fake `ctx` (secrets facade only) and
  `aws_configure.configure_set/status` monkeypatched.
- `tests/standalone_test.sh` — installs the AWS CLI for real and checks
  `aws --version` / `aws configure list` output; run inside the aw-workspace
  container.

## Credentials

`config_schema` in `aw-app.json` declares 4 fields:

- `aws_access_key_id` (plain)
- `aws_secret_access_key` (`x-secret` → zero-knowledge secret store)
- `aws_default_region` (plain, default `us-east-1`)
- `aws_session_token` (`x-secret`, optional — for temporary/STS credentials)

`POST /api/apps/aws/settings` accepts any subset of these, writes them to
`ctx.secrets`, and applies them via `aws configure set <key> <value>
--profile default` — the same one-shot-save pattern as `aw-app-git`'s
`set_token`/`save_settings` routes. `activate()` re-applies whatever is
already stored on every boot / reconcile pass, so credentials survive a
workspace recreation without a manual re-entry.

## NOT done here (explicitly out of scope)

- No nav/window entry — this is an install-a-CLI + settings app (like
  `aw-app-essentials` + credentials), not a UI surface with its own page.
- No install into the production workspace — the orchestrator installs (via
  the reconciler/catalog) and validates (`aws --version` +
  `aws configure list`) after this lands.
- No masking/redaction beyond the standard `x-secret` handling — visibility
  was explicitly not a concern for this card; the secret access key still
  goes through the secret store for security/consistency with `aw-app-git`.
