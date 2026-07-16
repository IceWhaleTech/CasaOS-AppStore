# CI/CD Overview

CI/CD explains how source files become validated, built, published store artifacts.

For most third-party stores, the practical goal is:

1. validate app compose files on pull requests
2. build v2 `dist/`
3. optionally build the legacy v1 `dist/store/main.zip`
4. publish `dist/` to static hosting

## Current official workflow split

This repository uses three main GitHub Actions workflows:

- [`validator.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/validator.yml): validates compose files and runs a full v2 build check.
- [`release.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release.yml): builds v2 and v1 artifacts for inspection or reuse.
- [`release-store.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release-store.yml): publishes tagged store output to `gh-pages` and GitHub Releases.

## Workflow responsibilities

| Workflow | Runs when | Main purpose | Main output |
|---|---|---|---|
| Validator | pull request or manual run | fail fast on invalid source files | validation and build reports |
| Release | push to `main` or manual run | produce reusable build artifacts | `dist/`, `main.zip`, reports |
| Release-store | release tag or manual run | publish the store | `gh-pages`, GitHub Release assets |

## Repo-local actions

These workflows are composed from small actions:

- `validate-compose`: validate source compose files.
- `build-store-v2`: repo-local wrapper around `IceWhaleTech/build-appstore-action`.
- `build-store-v1`: build legacy `main.zip`.
- `write-job-summary`: render report JSON into the GitHub Actions summary.
- `render-report`: convert report JSON into HTML when needed.

For external maintainers, the recommended public entrypoint is `IceWhaleTech/build-appstore-action`. See [Official Actions Reuse](official-actions-and-workflows.md).

## Build reports and job summary

The v2 build action writes a structured report JSON when `report-json` is set. This repository uploads that report as an artifact and renders it into the GitHub Actions job summary.

To read it:

1. Open the GitHub Actions run.
2. Open the relevant job, such as `validate`, `build`, or `release`.
3. Read the summary at the top of the job page.
4. Download the report artifact when you need the full JSON details.

Common artifact names:

- `validation-report`
- `build-v2-validation-report`
- `build-v2-report`
- `release-build-v2-report`

The summary includes build status, app counts, warning/error counts, top issues, generated artifacts, and repository context.

## Build error behavior

The action separates app-level issues from global failures.

App-level errors are collected so later apps can still be processed. If any app-level error exists, the report is written and the v2 build ultimately fails. Examples include invalid app metadata, missing required `x-casaos.id`, missing referenced assets, invalid YAML, and architecture mismatch.

Warnings are reported without failing the v2 build when the output can still be generated. Examples include missing `supported-languages.json`, skipped app directories without top-level `x-casaos`, registry rate limits, image digest pinning failures, image size estimation failures, and non-semver `x-casaos.version`.

Global failures stop the build for the whole repository. Examples include invalid `base-url`, missing `Apps/`, invalid store config JSON, invalid `store_id`, invalid `supported-languages.json`, or dependency setup failures.

## Compatibility behavior

The official workflows intentionally build both outputs:

- v2 static files for new clients
- v1 `dist/store/main.zip` for legacy clients

If your store is brand new and does not need v1 support, you can omit the v1 build step.

## Next pages

- [Official Actions Reuse](official-actions-and-workflows.md)
- [Validator Workflow](validator-workflow.md)
- [Release Workflow](release-workflow.md)
- [Release-store Workflow](release-store-workflow.md)
