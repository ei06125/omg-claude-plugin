# ADR-0002: Version bumps come from accepted feature specs

- **Status:** Proposed (open questions answered by the owner, awaiting acceptance)
- **Date:** 2026-09-19
- **Updated:** 2026-09-20
- **Related:** `documentation/Product/Features/omg-release.md`,
  `.agents/Governance/git-cicd-governance.md` (sections 6, 9 and 19)

## Context

The plugin version lives in `.claude-plugin/plugin.json` and is `0.1.0`. Nothing is tagged, and the version is
edited by hand. The release feature (`omg-release`) needs a rule that decides the next version automatically.

Facts that shape the rule:

- Every feature has a spec in `documentation/Product/Features/`, and only the owner accepts a feature. The
  post-acceptance commit and merge come after that acceptance.
- Merge styles have varied: the earlier GitLab project squash-merged, and the first GitHub pull request landed as
  a merge commit. Commit messages are therefore not a reliable release signal.
- The repository's governance says automated versioning "should follow the product's compatibility policy, not
  blindly infer customer impact from a prefix" (section 6). It also says to use Semantic Versioning where there is
  a meaningful public compatibility contract, to create release tags from protected reviewed commits, and to
  restrict tag creation to release automation or authorised maintainers (sections 9 and 19).
- For a Claude Code plugin, the public compatibility contract is not a binary ABI. It is the names and documented
  behaviour users depend on: skill and command names (for example `/omg:hello`), agent names, MCP tool names and
  schemas once they exist, configuration keys, and documented replies.

## Decision drivers

- The rule must be deterministic and testable without a network.
- It should follow the compatibility policy, per the governance.
- It should not depend on every author writing a correct commit prefix.
- It should tie a release to the owner's acceptance.
- It should be cheap to maintain.

## Options considered

### 1. Conventional Commits with `python-semantic-release`

The prefix of each commit (`feat`, `fix`, `!`) decides the bump.

Pros:

- Mature tooling for computing the version, and a familiar convention.

Cons:

- It infers impact from a prefix, which the governance warns against.
- It depends on every author, and on the merge style, to produce the right prefix: one wrong prefix mis-versions a release.
- It needs a title or commit-message check to work at all.
- A new feature and a small fix can carry the same prefix if the author judges it that way.

### 2. Accepted feature specs decide the bump (proposed)

The rules below use the spec headers and the paths that changed.

Pros:

- Follows the compatibility policy: a new accepted capability is a backward-compatible addition.
- Deterministic: it compares file contents between the last tag and the release commit, with no message parsing.
- The release signal is the owner's acceptance, which the workflow already requires.
- Removes the need for a commit-title check and for `python-semantic-release`.

Cons:

- Custom logic to write and test.
- Depends on spec discipline: a feature merged without a spec is only a patch.
- Breaking changes need an explicit human marker, because a spec diff cannot show them.

### 3. Manual versioning

The owner edits `plugin.json` and tags by hand.

Pros:

- Nothing to build.

Cons:

- Easy to forget, and it does not scale past a few releases.
- It gives up the review trail the release pull request provides.

### 4. No `version` field

`claude plugin list` shows commit-SHA identifiers for plugins that declare no version. Every commit would count as
a new version.

Pros:

- No bumping at all, and updates are always distinguishable.

Cons:

- Users and the owner get no meaningful version to reason about, and there is no compatibility signal.
- Not verified here: whether an explicit version that never changes actually blocks updates.

## Decision (proposed)

Adopt Option 2. The next version is computed from what changed between the previous release tag and the release
commit.

| Change in that range | Bump |
|---|---|
| A feature spec's `Status` is `Accepted` at the release commit and was not at the previous tag, or a new spec is added as `Accepted` | MINOR |
| A spec in the range carries a `Breaking: yes` marker in its header | MAJOR |
| Any other change to shipped content: `.claude/`, `.claude-plugin/`, `sources/`, `configs/` | PATCH |
| Only docs, tests, CI, tooling, or governance changed | No release |

Rules:

- When several rows apply, the highest wins. A release bumps once per release, not once per feature, so two
  features accepted before the same release still give a single MINOR bump.
- `Status` has three values: `Draft`, `In development` and `Accepted`. The owner sets `Accepted`, as part of the
  post-acceptance commit on the feature's own pull request.
- A `Breaking: yes` marker is needed when a change removes or renames a skill, command or agent, changes a
  documented reply, or removes or changes an MCP tool or configuration key incompatibly.
- The previous tag is the baseline. The owner tags the current `main` as `v0.1.0`, and `omg-hello` counts as
  already included.
- **Below 1.0.0:** a MAJOR-class change (a `Breaking: yes` spec) bumps MINOR instead, for example `0.1.0` to
  `0.2.0`. The owner cuts `1.0.0` deliberately, as a manual release.
- **Cadence:** the release pull request is opened after every merge to `main` that contains a releasable change.
  If one is already open, it is updated to the newly computed version instead of opening a second. The owner
  decides when to merge it, so releasing one feature at a time or several together are both possible.
- **Tags:** the release creates an annotated, unsigned tag `vX.Y.Z` with a release message. Signed tags are
  revisited if the plugin is published for others.
- **Break detection:** the `Breaking: yes` marker is the only safeguard for now. An automatic check of the public
  surface (skill, command and agent names) is deferred.
- The release itself follows the release pull request flow in the `omg-release` spec: the automation opens
  `release/vX.Y.Z`, the owner merges it, and the tag is created on the merge commit. `main` and `v*` tags stay
  protected.

## Consequences

- The `omg-release` spec implements this ADR: the next version comes from a small script instead of
  `python-semantic-release`, and there is no commit-message or title check.
- The existing specs use free-text `Status` values. They must be normalised to the three values above before the
  rule can read them.
- A feature's `Accepted` status has to arrive in the feature's own pull request. If it is flipped later, the
  release is delayed until that change lands.
- Breaking changes rely on the owner remembering the marker, until an automatic check exists.
- Because a release pull request follows every qualifying merge, the automation must handle a release pull
  request that is already open. When the computed version changes (for example a second feature arrives), the open
  one is replaced: it is closed with a comment and its branch is deleted, as the `omg-release` spec describes.

## Questions answered by the owner (2026-09-20)

1. **Below 1.0.0:** a MAJOR-class change bumps MINOR while the major version is 0.
2. **Detecting breakage automatically:** decide later. A snapshot test of the public surface (skill, command and
   agent names) would fail when a name disappears without a `Breaking: yes` marker. Revisit once there are more
   skills, agents or MCP tools to protect.
3. **Release cadence:** a release pull request after every qualifying merge to `main`.
4. **Tag type:** annotated, unsigned.

## Still open

- Whether to add the public-surface check (question 2 above), and when.

## Verification status

Implemented in the `omg-release` feature and tested against real git repositories, with a local HTTP stand-in for
the GitHub API. Not yet verified on the real repository: the assumptions listed in the spec. The sections cited
above exist in `.agents/Governance/git-cicd-governance.md`.

## Follow-ups

- The owner accepts this ADR and the `omg-release` spec.
- Add the public-surface check when there are more skills, agents or MCP tools to protect.
