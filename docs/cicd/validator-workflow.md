# Validator Workflow

The validator workflow is defined in [`.github/workflows/validator.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/validator.yml).

## Purpose

It validates source inputs before merge and catches regressions early.

## Triggers

- pull requests on `opened` and `synchronize`
- manual `workflow_dispatch`

## Main checks

1. Run the repo-local `validate-compose` action against app source files.
2. Upload a structured validation report artifact.
3. Restore shared build caches.
4. Run the repo-local `build-store-v2` action as a full build validation.
5. Upload the build validation report and write a job summary.
6. Fail the workflow if either compose validation or the v2 build check fails.

## Repo-local actions involved

- `validate-compose`: checks top-level `name`, `x-casaos.id`, and `docker compose config -q`
- `build-store-v2`: wraps the public `IceWhaleTech/build-appstore-action`
- `write-job-summary`: renders JSON reports into the GitHub Actions summary

## Why it matters

This workflow protects the source repository contract:

- compose syntax must be valid
- naming must match repo expectations
- the repository must still build into valid `dist/`

## When to read this page

Use this page when:

- a PR fails validation
- you want to understand what source rules are enforced automatically
- you are designing third-party store CI modeled after this repo
