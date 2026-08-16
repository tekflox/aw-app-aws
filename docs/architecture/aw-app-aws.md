---
repo: architecture
path: docs/architecture/aw-app-aws.md
source: generated
edited: false
checksum: sha256:19e19f3720a3cd4d7ab33c88a9327b9fda19a460e55b8b359bcb09dc336e009d
---
# AWS CLI

- **repo**: aw-app-aws
- **layer**: app
- **technologies**: python
- **health** (derived): planned

Installs the AWS CLI v2 into the workspace and provides a settings panel for AWS credentials (access key, secret key, region, session token — applied via `aws configure`).

## Connections
- `http` → **aw-workspace** — routes mounted at /api/apps/aws

## MCP tools
_none exposed_

## Requirements
_none documented_
