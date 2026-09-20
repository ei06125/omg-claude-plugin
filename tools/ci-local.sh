#!/usr/bin/env bash
set -euo pipefail

# Runs GitLab CI jobs locally (all jobs, or the names given) from a throwaway clone.
# Do not run gitlab-ci-local straight from a git worktree: its .git is a pointer file that
# does not resolve inside the job container, so gitleaks scans 0 commits and still passes.

command -v gitlab-ci-local >/dev/null || {
  echo "gitlab-ci-local not found: brew install gitlab-ci-local" >&2
  exit 1
}

repo_root=$(git rev-parse --show-toplevel)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

git clone --quiet "$repo_root" "$work"
rsync -a --delete --exclude=.git --filter=':- .gitignore' "$repo_root"/ "$work"/
# gitlab-ci-local only copies tracked files into the job, so stage new ones in this throwaway clone.
git -C "$work" add -A

cd "$work"
gitlab-ci-local "$@"
