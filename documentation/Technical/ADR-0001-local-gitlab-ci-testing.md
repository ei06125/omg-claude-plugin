# ADR-0001: Testing GitLab CI locally

- **Status:** Accepted
- **Date:** 2026-09-19

## Context

`.gitlab-ci.yml` defines two jobs in one stage:

- `gitleaks` scans the full git history.
- `pre-commit` runs the remaining hooks through `uv`, with `SKIP=gitleaks`.

Both jobs use `image:` with hash-pinned images, so they can run on GitLab.com shared runners. Until a pipeline
runs on a real GitLab, several behaviours are unproven, so a way to run CI before pushing is wanted.

Two facts shaped the options below:

- The reference material used for comparison is the DevOps Foundations exercise files
  (`07_08_solution/docker-compose.yaml`). It runs a real GitLab EE server, a Docker-socket runner and Postgres
  locally, and its CI jobs call `docker compose run --rm <service>`.
- Docker on the development machine denied every `ghcr.io` pull, including public images with an empty Docker
  config, while `curl` to the same registry worked. The root cause is unknown, so CI images are pulled from
  Docker Hub. The uv image there serves the same digest as its `ghcr.io` counterpart.

## Decision drivers

- Fidelity: how much of real GitLab behaviour is exercised.
- Cost: setup effort, disk, memory and time to iterate.
- Security: supply-chain pinning, network exposure, blast radius of a runner with host Docker access.
- Portability: jobs must keep working on GitLab.com shared runners.
- Licensing: this repository is intended to be published, so third-party course files must not be copied into it.

## Options considered

### 1. `gitlab-ci-local` from a throwaway clone

Implemented as `tools/ci-local.sh`. It clones the repository, overlays the current files and runs
`gitlab-ci-local` against Docker.

Pros:
- Cheap: one `brew install`, seconds per run, no server to maintain.
- Verified in practice: both jobs pass on the clean repo and both fail on planted fake secrets.
- Runs the exact `image:` and script definitions used on GitLab.com.

Cons:
- It re-implements the runner and there is no GitLab server, so only JSON-schema validation of the CI file is
  done. `workflow:rules`, merge-request pipelines, cache keys and predefined-variable behaviour are not exercised.
- It exported no report for the failed job, so `artifacts: when: on_failure` is unverified.
- Running it directly from a git worktree gives a false green: `.git` is a pointer file that does not resolve in
  the job container, so gitleaks scans 0 commits and still exits 0. The wrapper avoids this.
- Local runs use the host CPU architecture (arm64 here), not the amd64 of GitLab.com runners.

### 2. Local GitLab EE + runner + Postgres via Docker Compose

A trimmed version of the reference stack.

Pros:
- Real GitLab behaviour, including `workflow:rules`, merge-request pipelines, artifacts, cache and GitLab's own
  CI Lint.
- A safe place for negative tests: fake secrets can be pushed without touching GitLab.com history.
- No shared-runner minutes and no dependence on the network once images are pulled.
- Reusable for other repositories.

Cons:
- Heavy: multi-GB images, several GB of RAM and a first boot of several minutes.
- Manual setup that the compose file does not contain: creating the `gitlab` network, a `gitlab.example.com` hosts
  entry (needs sudo), runner registration, retrieving the initial root password, and creating and pushing a
  project. Runner containers must also resolve `gitlab.example.com`.
- Differs from GitLab.com: older GitLab version, self-hosted runner with the Docker socket mounted, self-signed
  TLS, no licensed EE features.
- Mounting the Docker socket gives every CI job control of the host Docker engine.
- The reference stack uses an unofficial arm64 GitLab image pinned by tag, and GitLab 16.9 is out of support.
  Its ports bind to all interfaces by default.
- Ongoing upkeep: volumes, updates and drift from the hosted product.

### 3. Throwaway branch on GitLab.com

Push a branch to the private project and read the pipeline.

Pros:
- Highest fidelity: real runners, real GitLab version, real merge-request semantics.
- No infrastructure to build or maintain.

Cons:
- Consumes shared-runner minutes on a private project.
- Planted-secret tests would leave fake credentials in the GitLab.com repository, so they should stay local.
- Slower feedback loop and the network is required.

## Decision

Keep Option 1 as the default local loop. Validate real GitLab semantics once through Option 3 before relying on
the pipeline. Defer Option 2 until repeated CI experiments, or planted-secret tests inside a real pipeline, justify
the setup and upkeep.

The repository currently has one developer. Running and maintaining a local GitLab server is therefore not
justified for routine CI development. Use focused local tests for scripts and API responses, then use GitLab.com
for the final integration check. Reconsider Option 2 if the team grows or repeated GitLab-specific CI work makes
the additional fidelity worth its operational cost.

The merge-request approval gate follows this layered approach: test its shell and `jq` logic locally with mocked
Notes API responses, and verify `CI_JOB_TOKEN`, merge-request variables and pipeline blocking on GitLab.com. A
local GitLab server remains useful for occasional end-to-end experiments, but is not a required development
dependency.

Adopt the local Docker-based GitLab stack when at least one of these conditions becomes recurring rather than a
one-off investigation:

- CI changes depend on merge-request events, permissions, tokens, webhooks or other server-side GitLab behaviour.
- GitLab.com feedback time or shared-runner limits materially slow development.
- Destructive or security-focused pipeline tests must not touch the hosted repository.
- Multiple developers need a reproducible integration environment before pushing.
- Mock-based tests have missed a GitLab integration defect.

Before adoption, confirm that the expected use justifies the startup time, storage, patching and runner-security
cost. Prefer a disposable, loopback-only stack with synthetic credentials and no connection to production systems.

## Consequences

- `tools/ci-local.sh` remains the supported way to run CI locally, and the worktree caveat stays documented in the
  README.
- The gaps listed under Option 1 stay open until Option 2 or 3 is exercised.
- If Option 2 is adopted, follow the scope below.

## Scope if Option 2 is adopted

Keep only the services needed to run GitLab and a runner:

- `gitlab`, `gitlab-db`, `gitlab-runner`, `create-self-signed-certificate` and the `print-self-signed-certificate*`
  helpers, plus their volumes and the `gitlab` network.

Drop everything specific to the reference website project: `opentofu`, `website`, `selenium`, `unit-tests` and
`integration-tests`, and its Dockerfile, `spec/`, `infra/` and `website/` directories.

Requirements:
- Write a minimal compose file for this repository. Do not copy the course file into it.
- Bind published ports to `127.0.0.1`, pin images by digest, and prefer an official GitLab image if it supports
  the host architecture.
- Treat the stack as disposable: local-only, no real credentials, and never expose it on a network.

## Verification status

Verified locally:
- Both CI jobs pass on the clean repository and fail on planted fake secrets (a GitHub token, a `*_PAT`
  assignment and a private-key header).
- The uv image on Docker Hub matches the pinned digest.
- The host had ample resources for Option 2 (8 CPUs, about 33 GB RAM, free ports 80, 443 and 2222).

Not verified:
- Any pipeline on GitLab.com. The result of the pipeline triggered by the first push to `main` has not been
  reviewed.
- `artifacts: when: on_failure`, `workflow:rules` and merge-request pipelines.
- amd64 behaviour of the jobs.
- Whether an official GitLab image with arm64 support exists for the version that would be used.

## Follow-ups

- Review the first GitLab.com pipeline and record the result here.
- Investigate the `ghcr.io` denial so the CI image source is not dictated by a local Docker quirk.
