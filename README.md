# AWS CLI

AWS CLI adds Amazon Web Services command-line access to an AW Workspace. It installs the AWS CLI and provides a settings screen for credentials and default region values.

## What It Does

- Installs the `aws` command in the workspace.
- Saves AWS access settings through the workspace settings experience.
- Supports access keys, secret keys, default regions, and temporary session tokens.
- Applies saved settings so terminal sessions can use AWS commands immediately.

## Why Use It

Use this app when a workspace needs to inspect or manage AWS resources. It is useful for deployments, infrastructure checks, S3 operations, logs, identity checks, and any workflow that depends on the official AWS CLI.

## How To Use It

Install the app, open its settings, add your AWS credentials, and choose a default region. After that, open a workspace terminal and run AWS CLI commands such as account checks, S3 listings, or deployment commands.

## What It Delivers

The app gives the workspace a ready AWS command-line environment with credentials kept in workspace-managed settings. Agents and users can run AWS operations without rebuilding the workspace image or manually reinstalling the CLI.
