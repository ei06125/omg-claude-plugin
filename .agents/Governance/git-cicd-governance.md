# Git, Repository, and CI/CD Governance Guide

Last reviewed: 2026-09-19

This guide provides a practical baseline for Git repositories, GitHub or GitLab, CI/CD pipelines, branching, environments, commit conventions, hooks, releases, and software-supply-chain security. Adapt it to the company’s size, release model, risk, and regulatory obligations.

## 1. Governance objectives

A repository and delivery process should provide:

- **Traceability:** connect requirements, code, reviews, test results, artifacts, approvals, deployments, and incidents.
- **Integrity:** prevent unauthorised or unreviewed changes to code, pipeline definitions, dependencies, artifacts, and production.
- **Repeatability:** build and deploy the same source through automated, versioned procedures.
- **Separation of duties:** prevent one person or compromised account from silently changing and deploying critical code.
- **Recoverability:** identify deployed versions and safely roll back or roll forward.
- **Least privilege:** limit repository, runner, secret, package, and environment access.
- **Developer usability:** keep the safe path fast and clear enough that people consistently follow it.

Assign owners for repository administration, source areas, CI/CD infrastructure, security controls, release decisions, and each deployment environment. Review administrator and bypass permissions regularly.

## 2. Repository structure and ownership

Choose a repository model intentionally:

- **Monorepo:** easier atomic cross-component changes and shared tooling; requires scalable CI selection, ownership rules, and dependency boundaries.
- **Multiple repositories:** clearer access and release boundaries; increases coordination, dependency, template, and policy-management work.

For every repository, define:

- Business and technical owner.
- Visibility: public, internal, or private.
- Data classification and prohibited content.
- Default branch and merge strategy.
- Required status checks and reviewers.
- Release and support policy.
- Archival criteria and retention.
- Dependency, secret, vulnerability, and license controls.
- Deployment environments and authorised deployers.

Use organisation-level policy and reusable templates for common controls. Do not rely on every repository owner to independently recreate security settings.

## 3. Git fundamentals and safe use

- Keep commits small, cohesive, and reviewable. A commit should represent one logical change.
- Never commit passwords, tokens, private keys, production data, customer data, or `.env` files containing secrets.
- Use `.gitignore` for generated, local, credential, and environment-specific files. A file already tracked remains tracked after adding it to `.gitignore`.
- Treat a secret committed at any point as compromised. Remove it from use and rotate it before considering history cleanup.
- Avoid generated binaries and large media in ordinary Git history. Use a package registry, artifact store, release asset, or Git LFS when justified.
- Configure line endings and attributes with `.gitattributes` when the team uses multiple operating systems.
- Prefer `git switch` and `git restore` for explicit branch and working-tree operations.
- Use `git fetch` plus an explicit merge or rebase policy rather than leaving `git pull` behaviour ambiguous.
- Do not rewrite shared branch history. If force-pushing a private topic branch is permitted, use `--force-with-lease`, never an unconditional force push.
- Use `git revert` for auditable reversal of changes already shared or deployed.
- Preserve authorship and review attribution. Do not share Git hosting accounts or signing keys.

## 4. Branching strategy

### Recommended default: trunk-based development

For most product teams, use one protected, always-releasable default branch—normally `main`—with short-lived topic branches and pull or merge requests.

Recommended flow:

1. Create a short-lived branch from current `main`.
2. Make a focused change with tests and documentation as needed.
3. Open a draft pull/merge request early.
4. Run automated checks and obtain required review.
5. Update from `main`, resolve conflicts, and rerun affected checks.
6. Merge using the repository’s selected strategy.
7. Delete the merged topic branch.
8. Deploy the immutable artifact built from the accepted revision.

Keep unfinished functionality behind feature flags rather than long-lived branches. Remove flags after rollout to avoid permanent configuration complexity.

Benefits include small integration steps, early conflict detection, simpler CI/CD, and a clear source of truth. This model requires reliable tests, branch protection, rapid review, and the ability to disable incomplete features.

### GitHub Flow

GitHub Flow is effectively a lightweight trunk-based workflow: branch from the default branch, collaborate through a pull request, merge after checks and review, then deploy. It suits continuously deployed services and many application teams.

### GitLab Flow

GitLab Flow commonly combines merge-request development with issue tracking and, where needed, environment or release branches. Use the smallest variation that satisfies release and operational needs.

### Git Flow

Classic Git Flow uses long-lived `develop` and `main` branches plus feature, release, and hotfix branches. It may fit products with multiple supported versions, scheduled release trains, or lengthy formal validation. It adds merge paths, branch drift, duplicate fixes, and operational overhead. Do not adopt it by default merely because it is familiar.

### Release branches

Create release branches only when a released line needs stabilisation or maintenance independent of current development. Define:

- Who may create, update, and close them.
- Supported lifetime and versions.
- Whether fixes originate on `main` and are backported, or originate on the oldest supported line and move forward.
- Required checks and review.
- Version and tag relationship.

Avoid permanent branches named after environments. Code should progress between environments as immutable artifacts, not through `dev`, `staging`, and `production` branches that drift.

### Hotfixes

Use the normal review and CI path whenever possible, with expedited reviewers and deployment. A production emergency should reduce waiting time, not remove traceability. Apply the fix to the authoritative development line and backport it to supported releases. Document and review any emergency bypass after the incident.

## 5. Branch naming

Use lower-case, short, descriptive names. Recommended pattern:

`<type>/<work-item>-<description>`

Examples:

- `feat/1234-add-saml-login`
- `fix/2891-token-refresh-race`
- `chore/update-runner-image`
- `hotfix/742-payment-timeout`

Suggested types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `release`, and `hotfix`.

Rules:

- Use hyphens between words.
- Avoid personal names, dates without meaning, vague names such as `changes`, and sensitive information.
- Include a work-item identifier when the team uses issue tracking.
- Keep branches short-lived and delete them after merge.
- Reserve prefixes such as `release/` and `hotfix/` if they trigger privileged automation.

Treat branch names, tag names, issue titles, commit text, and pull-request fields as untrusted input in CI scripts.

## 6. Commit messages

Use an imperative, concise subject that explains the outcome. Include context and rationale in the body when the reason is not obvious from the change.

Conventional Commits is a useful machine-readable standard:

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

Examples:

```text
feat(auth): add SAML identity-provider metadata validation
fix(api): reject tokens issued for another audience
docs(governance): document production deployment approval
feat(billing)!: replace legacy invoice endpoint
```

Recommended types:

- `feat`: user- or API-visible capability.
- `fix`: defect correction.
- `docs`: documentation only.
- `refactor`: code change without intended behaviour change.
- `test`: test-only change.
- `perf`: performance improvement.
- `build`: build system or dependency change.
- `ci`: CI/CD configuration or scripts.
- `chore`: repository maintenance not covered elsewhere.
- `revert`: reversal of an earlier commit.

Use `!` or a `BREAKING CHANGE:` footer for an incompatible change. Keep scopes stable and meaningful; do not make every directory a scope. Reference work items in footers when useful.

Commit messages are not a substitute for a changelog or release notes. Automated versioning should follow the product’s compatibility policy, not blindly infer customer impact from a prefix.

Source: [Conventional Commits 1.0.0](https://www.conventionalcommits.org/)

## 7. Commitlint and local hooks

A `.commitlintrc`, `commitlint.config.js`, or equivalent configuration can enforce the chosen commit structure. Keep rules limited to conventions that deliver value, such as allowed types, non-empty subject, and reasonable header length.

Common client-side hooks:

- **`pre-commit`:** fast formatting, linting, generated-file checks, secret detection, and validation of staged content.
- **`commit-msg`:** commit message validation with commitlint or an equivalent tool.
- **`prepare-commit-msg`:** optionally inserts a work-item reference or template; avoid silently inventing metadata.
- **`pre-push`:** targeted tests or checks that are useful before consuming shared CI capacity.
- **`post-checkout` / `post-merge`:** non-blocking dependency or setup notices.

Server-side hooks such as `pre-receive` and `update` can enforce policy on self-hosted Git servers. GitHub Enterprise Server supports pre-receive hooks; hosted platforms primarily provide branch protection, rulesets, push rules, and CI checks.

Important limitations:

- Local hooks are not cloned automatically by Git and can often be bypassed with `--no-verify`.
- Hooks must be installed through a documented tool or `core.hooksPath` setup and should be versioned in the repository.
- Hooks should be deterministic, quick, portable, and produce actionable failures.
- CI and hosting-platform protections are the authoritative enforcement layer. Local hooks provide fast feedback, not the sole control.
- Never skip hooks to force a change through. Fix the issue or use an explicitly approved, documented exception.

Source: [Git — githooks](https://git-scm.com/docs/githooks)

## 8. Pull and merge requests

Every protected-branch change should use a pull request (GitHub) or merge request (GitLab), except an audited emergency procedure.

The request should include:

- Purpose and linked work item.
- Important design decisions and risks.
- Test evidence.
- User, operational, security, data, and compatibility impact.
- Migration, deployment, feature-flag, and rollback plan where relevant.
- Screenshots or recordings for meaningful UI changes.

Review requirements:

- At least one independent approval for ordinary changes; increase for critical repositories or sensitive areas.
- CODEOWNERS or equivalent approval for security, authentication, infrastructure, deployment, billing, privacy, and policy code.
- Dismiss or invalidate approvals when material new commits are pushed.
- Require approval of the latest reviewable change by someone other than its author.
- Resolve review conversations before merge.
- Require passing, current status checks against the revision being merged.
- Prevent authors from satisfying their own required approval.

Review the code, tests, threat and failure modes, observability, compatibility, rollout, and rollback—not only formatting. Keep changes small enough for meaningful review.

## 9. Protected branches, tags, and repository rules

Protect `main`, supported release branches, and release tags.

Recommended controls:

- Require pull/merge requests.
- Require independent and code-owner review.
- Require CI checks and current branch state before merge.
- Block force pushes and deletion.
- Restrict direct pushes and bypass permissions.
- Require linear history if the selected merge strategy depends on it.
- Require verified commit or tag signatures when the operational cost is justified.
- Require successful security and policy checks for sensitive repositories.
- Restrict tag creation and modification to release automation or authorised maintainers.

On GitHub, rulesets can govern branches and tags, require reviews and status checks, block force pushes, and constrain bypass. Layered rulesets use the most restrictive applicable rules. On GitLab, use protected branches and tags, merge request approvals, CODEOWNERS, and protected environments.

Source: [GitHub — Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

## 10. Merge strategy and history

Select one primary strategy per repository and document it.

### Squash merge

Produces one default-branch commit per pull request. It keeps history concise and works well when topic-branch commits are iterative. Preserve meaningful authorship and the pull-request link. The squashed message should satisfy the commit convention.

### Rebase and merge

Preserves individual commits in a linear history. Use it when each commit is intentionally curated, buildable, and valuable. Rebasing rewrites topic-branch commit IDs and should not rewrite shared protected history.

### Merge commit

Preserves the branch topology and exact commits. It can provide strong contextual grouping but makes history noisier. It may suit coordinated multi-commit changes and repositories where branch structure matters.

Do not require developers to curate every intermediate commit if the repository always squash-merges. Align local effort with the final history model.

## 11. CI pipeline design

Continuous Integration should validate every proposed change before merge. A typical pipeline includes:

1. Configuration and policy validation.
2. Formatting and linting.
3. Unit tests.
4. Build and package creation.
5. Static analysis and type checking.
6. Secret, dependency, license, and vulnerability scanning.
7. Integration and contract tests.
8. Database migration checks.
9. End-to-end or system tests where proportionate.
10. Artifact signing, provenance, and publication for accepted revisions.

Design principles:

- Fail fast with cheap deterministic checks before expensive jobs.
- Run independent jobs in parallel.
- Cache only validated dependencies and treat caches as untrusted performance aids, not artifacts of record.
- Pin toolchain and dependency versions; use lock files.
- Make builds reproducible and independent of mutable developer machines.
- Set timeouts and concurrency limits.
- Cancel superseded topic-branch runs when safe.
- Preserve useful logs, test reports, coverage, and artifacts under a defined retention policy.
- Use reusable workflows/templates for common controls, version them, and review changes centrally.
- Keep the required path reliable; quarantine or fix flaky tests rather than teaching developers to rerun until green.

Do not let a workflow modify its own required checks, approve its own change, or publish from unreviewed code.

## 12. GitHub Actions security

- Set the default `GITHUB_TOKEN` to read-only and grant only required permissions at workflow or job level.
- Pin third-party actions and reusable workflows to full-length commit SHAs. A movable tag is not an immutable dependency.
- Review third-party action source and ownership; allowlist actions at organisation level where practical.
- Use Dependabot or equivalent automation to propose reviewed action updates.
- Prefer OpenID Connect federation to cloud providers instead of long-lived cloud credentials.
- Scope secrets to the narrowest repository, environment, and job. Environment secrets should only become available after protection rules pass.
- Do not interpolate untrusted event data directly into shell scripts. Pass it through environment variables and quote it safely.
- Avoid `pull_request_target` for executing pull-request code. It runs in a privileged context and can expose write tokens, secrets, or trusted caches.
- Treat artifacts and caches from untrusted workflows as attacker-controlled.
- Use isolated, ephemeral runners. Do not run public or untrusted contributions on persistent self-hosted runners with internal-network access.
- Restrict who can change workflow files and require code-owner review for `.github/workflows/` and custom actions.
- Use concurrency controls to avoid overlapping deployments.
- Generate and verify artifact attestations or equivalent provenance for important releases.

Source: [GitHub — Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)

## 13. GitLab CI/CD security

- Protect important branches, tags, environments, variables, and runners.
- Use protected runners only for trusted protected refs, and tag jobs so privileged work cannot fall back to an ordinary runner.
- Prefer an external secrets manager. If CI/CD variables must contain secrets, mask, hide, protect, and environment-scope them.
- Use pipeline inputs rather than freely overridable pipeline variables for controlled parameters where supported.
- Require review of `.gitlab-ci.yml`, included templates, runner configuration, and deployment scripts by designated owners.
- Pin included CI components, container images, and dependencies to immutable versions or digests.
- Review merge-request pipeline behaviour before granting access to protected variables or runners.
- Use protected environments and deployment approvals for production.
- Consider a separate deployment project when development maintainers must not access production secrets or alter delivery controls.
- Prevent concurrent or outdated deployments to the same environment.

Sources: [GitLab — Pipeline security](https://docs.gitlab.com/ci/pipeline_security/), [GitLab — Deployment safety](https://docs.gitlab.com/ci/environments/deployment_safety/)

## 14. Secrets and credentials

- Never store plaintext secrets in source, workflow files, images, build artifacts, logs, comments, or repository variables intended for non-sensitive configuration.
- Prefer workload identity and short-lived credentials over stored cloud keys.
- Use a central secrets manager with audit logs, rotation, and fine-grained access.
- Scope credentials by environment, repository, job, audience, operation, and lifetime.
- Do not expose production secrets to pull-request pipelines or untrusted code.
- Masking is a defensive convenience, not a guarantee that transformed or encoded values will be redacted.
- Scan developer changes, full history where appropriate, and CI output for secrets.
- On exposure: revoke or rotate first, investigate use, then clean history if required. History rewriting alone does not neutralise a credential.

## 15. Artifacts and software-supply-chain integrity

Build once from the reviewed source revision and promote the same immutable artifact through environments. Do not rebuild separately for staging and production.

Record:

- Source repository and commit.
- Workflow and trusted builder identity.
- Dependencies and lock files.
- Build parameters and environment.
- Artifact digest and signature.
- Test and scan results.
- Approvals and deployment history.

Use immutable package versions and container digests. Generate a Software Bill of Materials where customer, regulatory, or risk requirements justify it. Sign releases and artifacts, produce build provenance, verify before deployment, and protect signing keys outside ordinary job filesystems where possible.

Treat package registries and container registries as production systems. Restrict publish, overwrite, delete, and retention privileges.

## 16. Environments: DEV, STG, and PROD

Separate environments when the product’s risk or operational model requires isolation. A small static site may only need preview and production. A service handling customer data usually benefits from development, staging, and production separation.

### Development

Purpose: rapid integration and developer testing.

- May deploy automatically from `main` or create ephemeral review environments per request.
- Uses synthetic or approved sanitised data.
- Has no production credentials or network paths unless strictly controlled.
- Can tolerate faster change and shorter retention.

### Staging

Purpose: production-like validation of the release candidate.

- Uses the same deployment mechanism and artifact intended for production.
- Mirrors critical topology, configuration classes, migrations, and integrations closely enough to expose release risks.
- Uses synthetic, anonymised, or specifically authorised data—not an uncontrolled production copy.
- Runs smoke, integration, migration, performance, security, and operational checks according to risk.
- Is not a permanent substitute for tests or a place to accumulate unreleased changes.

### Production

Purpose: customer-facing or business-critical operation.

- Accepts only immutable, traceable, approved artifacts.
- Uses protected environments, narrowly scoped credentials, and independent approval where risk warrants it.
- Restricts deployment sources to protected branches or release tags.
- Prevents self-approval for sensitive deployments.
- Records the artifact, initiator, approver, time, result, and rollback relationship.
- Has observability, incident response, backup, recovery, and rollback/roll-forward procedures.

Environment boundaries should separate credentials, cloud accounts or projects, data, encryption keys, network access, and permissions. Naming environments differently without isolating trust does not create a meaningful boundary.

GitHub environments can enforce required reviewers, branch/tag restrictions, custom protection rules, and secret gating. GitLab protected environments restrict deployers and can require deployment approvals.

Sources: [GitHub — Deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments), [GitLab — Protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)

## 17. Continuous delivery and deployment

- **Continuous delivery:** every accepted change is deployable; production deployment remains an explicit decision.
- **Continuous deployment:** every accepted change that passes controls automatically reaches production.

Choose based on test confidence, blast radius, rollback speed, compliance, and business tolerance—not terminology. Manual approval does not compensate for weak testing, and automated deployment does not require unsafe rollout.

Recommended promotion model:

1. Merge reviewed code to the protected default branch.
2. Build, test, scan, sign, and publish one immutable artifact.
3. Deploy that artifact to a lower environment.
4. Run environment-specific verification.
5. Promote the same digest to production after automated and, where required, human gates.
6. Monitor health and business signals.
7. Roll forward, roll back, or disable via feature flag when thresholds fail.

Use canary, rolling, blue-green, or feature-flagged rollout for changes whose blast radius warrants progressive exposure. Define automatic abort criteria before deployment.

## 18. Database and infrastructure changes

- Version infrastructure as code and review it through the same protected process.
- Plan database changes for backward and forward compatibility during rolling deployments.
- Prefer expand/migrate/contract changes over destructive one-step migrations.
- Back up and test restoration before irreversible migrations.
- Detect infrastructure drift and reconcile it through code; restrict manual production changes.
- Record emergency manual changes and promptly encode or reverse them through the repository.
- Use plan output in review, but regenerate or validate it at apply time so stale plans cannot silently deploy.

## 19. Releases, versions, and tags

Use Semantic Versioning when the software exposes a meaningful public compatibility contract. Internal services may use date, build, or independently versioned components if that communicates releases better.

- Create release tags from protected, reviewed commits.
- Use annotated and cryptographically signed tags where provenance requirements justify it.
- Never move or reuse a published release tag or package version.
- Generate release notes from reviewed metadata, then edit for user impact and migration guidance.
- Include breaking changes, security implications, upgrade steps, known issues, and rollback constraints.
- Define supported versions and end-of-support policy.

## 20. Dependencies and automated update tools

- Commit lock files for deployable applications and verify integrity metadata.
- Use trusted registries and namespace controls to reduce dependency-confusion risk.
- Automate update proposals, but require the same tests and review as other code.
- Group low-risk updates carefully; keep high-impact framework, runtime, authentication, and major-version changes separately reviewable.
- Enable dependency and container vulnerability alerts with owners and remediation targets.
- Use automated merge only for narrowly defined low-risk updates after all required checks pass.
- Review licenses and provenance, not only known vulnerabilities.

## 21. Backup, continuity, and platform exit

The hosting platform is not the only required backup. Determine recovery requirements for repositories, issues, pull/merge requests, releases, packages, CI definitions, environment configuration, and audit evidence.

- Mirror or back up critical source and configuration according to recovery objectives.
- Protect backup credentials and test restoration.
- Document how to rebuild runners, integrations, branch protections, secrets references, and deployment controls.
- Maintain multiple organisation owners under controlled emergency access.
- Plan for vendor outage, account suspension, regional failure, and migration to another Git service.

## 22. Common failure modes

- Direct pushes or broad bypass rights on `main`.
- Long-lived feature and environment branches that drift.
- Required checks that can be replaced or renamed by the change under review.
- Production deployments that rebuild source instead of promoting an existing artifact.
- Persistent self-hosted runners executing untrusted code.
- Long-lived cloud secrets in CI instead of workload federation.
- Unpinned third-party actions, CI templates, packages, or container tags.
- Production secrets exposed to fork or merge-request pipelines.
- Manual production changes not represented in version control.
- Flaky tests normalised through repeated reruns.
- One person authoring, approving, and deploying a critical change.
- Local hooks treated as the only policy enforcement.
- Rewriting published history or moving release tags.
- Production data copied into lower environments without authorisation and protection.
- Rollback plans that have never been tested or cannot reverse a data migration.

## 23. Minimum policy set

- Source-code and repository-management policy.
- Branching, commit, pull/merge request, and code-review standard.
- CI/CD pipeline and runner security standard.
- Secrets and signing-key management standard.
- Environment and deployment policy.
- Release, versioning, and artifact-retention policy.
- Dependency and software-supply-chain policy.
- Emergency change and bypass procedure.
- Repository archival, backup, and recovery procedure.
- Open-source contribution and license policy where applicable.

Every exception should have a reason, risk owner, compensating controls, approval, and expiry.

## 24. Suggested implementation order

### First 30 days

- Inventory repositories, owners, administrators, visibility, secrets, runners, and production deployment paths.
- Protect default branches and release tags; block direct pushes and force pushes.
- Require pull/merge requests, independent review, and baseline CI.
- Enable MFA and SSO for the Git organisation where supported.
- Rotate exposed or ownerless credentials and remove secrets from pipeline files.
- Document the branching, commit, and emergency-change conventions.

### Days 31–90

- Add CODEOWNERS, required checks, commit-message validation, and fast local hooks.
- Standardise reusable CI templates and least-privilege workflow tokens.
- Separate DEV/STG/PROD trust boundaries and protect production deployments.
- Replace cloud keys with OIDC/workload identity where supported.
- Add dependency, secret, static-analysis, and artifact scanning.
- Establish immutable artifact promotion, deployment records, and tested rollback.

### Months 4–12

- Use ephemeral isolated runners for sensitive or untrusted workloads.
- Add artifact signing, SBOM, and provenance where risk warrants it.
- Reduce standing deployment access and bypass permissions.
- Exercise platform recovery, signing-key rollover, runner compromise, and supply-chain incident response.
- Measure pipeline reliability, review effectiveness, deployment health, and exception age.

## 25. Evidence and metrics

Keep evidence of:

- Repository ownership, access reviews, and administrator changes.
- Rulesets, protected branches/tags, required checks, and bypass events.
- Pull/merge requests, approvals, review dismissal, and CI results.
- Workflow/template revisions and third-party dependency pins.
- Artifact digests, signatures, provenance, scan results, and release tags.
- Environment approvals, deployments, verification, and rollback events.
- Secret rotation, runner maintenance, exceptions, and incident actions.
- Backup restoration and continuity exercises.

Useful metrics:

- Lead time from first commit to production.
- Deployment frequency and success rate.
- Change failure rate and time to restore service.
- Pull/merge request age, size, and review time.
- Default-branch build health and flaky-test rate.
- Repositories lacking owners, protection, required CI, or recent access review.
- Standing administrators, bypass users, and manual production deployers.
- Age of dependencies, actions, runner images, and unresolved critical findings.
- Percentage of deployments promoting a previously built immutable artifact.
- Emergency changes and expired exceptions outstanding.

Metrics should drive investigation and improvement, not individual performance scoring or incentives to manipulate commits and pull requests.

## References

- [Git — githooks](https://git-scm.com/docs/githooks)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/)
- [GitHub — Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub — Secure use reference for Actions](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub — Deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [GitLab — CI/CD pipelines](https://docs.gitlab.com/ci/pipelines/)
- [GitLab — Pipeline security](https://docs.gitlab.com/ci/pipeline_security/)
- [GitLab — Protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)
- [GitLab — Deployment safety](https://docs.gitlab.com/ci/environments/deployment_safety/)
- [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/info/rfc9700/)
