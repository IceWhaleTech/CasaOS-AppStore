# Release Workflow

This page documents [`.github/workflows/release.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release.yml), the artifact build workflow.

## Purpose

It turns repository source definitions into reusable build deliverables.

## Triggers

- push to `main`
- manual `workflow_dispatch`

## Main stages

1. Check out repository source.
2. Restore build caches.
3. Build protocol v2 `dist/`.
4. Build legacy v1 zip output.
5. Upload build reports and deliverable artifacts.
6. Save build caches.
7. Write a job summary.

## Build outputs

The workflow currently produces at least:

- static `dist/` output for the v2 protocol
- legacy `dist/store/main.zip`
- JSON reports for v1 and v2 build results

## Why it matters

This workflow explains the build contract of the repository:

- source files are not the published protocol directly
- `dist/` is the publication artifact
- uploaded reports are debugging artifacts, not protocol files

## Related publish workflow

Actual tag-based publishing now lives in [Release-store Workflow](release-store-workflow.md).

If you are designing a third-party store repository, see [Official Actions Reuse](official-actions-and-workflows.md) for the recommended reuse path.

For external store maintainers, this page is useful even if you do not copy the official workflow exactly, because it shows which steps are protocol-critical and which are implementation detail.
