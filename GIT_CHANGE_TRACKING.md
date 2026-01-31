# Git Change Tracking & Rollback Guide

**Project:** TMS Dashboard  
**Baseline Commit:** `28efac5` (INITIAL: TMS Dashboard baseline before enhancements)  
**Date:** January 10, 2026

---

## Quick Reference

### Current Status
```bash
# Show current branch and commit
git status
git log --oneline -5

# Show all available branches
git branch -a

# Show baseline commit details
git show 28efac5 --stat
```

### Emergency Rollback (Full Reset to Baseline)
```bash
cd /home/pdanekula/tms_dashboard_python
git reset --hard 28efac5
git clean -fd
```

---

## Branching Structure

All enhancements are implemented in isolated feature branches that can be independently reverted.

```
BASELINE (28efac5)
│
├─ master (production - safe to merge after testing)
│
└─ feature branches (work in progress)
   ├─ feature/auth (Authentication & Session Management)
   ├─ feature/audit (Audit Trail & Logging)
   ├─ feature/ui-enhancements (Clickable Customer IDs & Action History)
   └─ feature/load-testing (Performance Testing)
```

---

## Implementation Workflow

### Starting a Feature Branch

```bash
# Create and switch to feature branch (from master)
git checkout -b feature/<feature-name>

# Make changes and commit regularly
git add .
git commit -m "FEATURE: <description>"

# Push to remote (if using remote repo)
git push origin feature/<feature-name>
```

### Viewing Changes in a Branch

```bash
# See commits in current branch not in master
git log master..HEAD

# See files changed
git diff --name-only master..HEAD

# See detailed changes
git diff master..HEAD

# See changes in specific file
git diff master..HEAD -- path/to/file.py
```

### Merging a Feature to Master

```bash
# Switch to master
git checkout master

# Merge feature branch
git merge feature/<feature-name> --no-ff

# Create annotated tag for release
git tag -a v1.1-<feature-name> -m "Release with <feature-name>"
```

---

## Reversion Strategies

### Strategy 1: Revert a Specific Commit

Keeps the revert in history. Safe for shared repositories.

```bash
# Revert a single commit (creates new commit that undoes it)
git revert <commit-hash>

# Revert multiple commits one by one
git revert <commit-hash-1>
git revert <commit-hash-2>
git revert <commit-hash-3>

# Revert a range (creates separate revert for each)
git revert <commit-hash-start>..<commit-hash-end>
```

**Use Case:** You've merged a feature and need to remove it safely without losing history.

**Example:**
```bash
# If feature/auth was merged with commit abc1234
git revert abc1234

# Creates a new commit with the reversion
git log --oneline | head -5
# Shows: xyz9999 Revert "Merge feature/auth"
```

### Strategy 2: Revert a Merge Commit

Use `-m` flag to specify which parent to revert against.

```bash
# Revert a merge commit (keep parent 1 - the master branch)
git revert -m 1 <merge-commit-hash>

# This undoes all changes from the feature branch
```

**Use Case:** You merged a feature branch into master and want to remove the entire feature.

### Strategy 3: Hard Reset (Destructive - Use with Caution)

Loses all commits since target. Only use if you haven't pushed or shared.

```bash
# Reset to baseline commit
git reset --hard 28efac5

# Clean up untracked files
git clean -fd

# This is destructive - all commits after 28efac5 are lost locally
```

**Use Case:** Local-only development went wrong; need to start over.

### Strategy 4: Selective File Reversion

Revert specific files while keeping other changes.

```bash
# Revert a single file to baseline
git checkout 28efac5 -- path/to/file.py

# Revert a specific file from another commit
git checkout <commit-hash> -- path/to/file.py

# Then commit the reversion
git add path/to/file.py
git commit -m "REVERT: Rollback file.py to baseline"
```

**Use Case:** Only part of a feature is problematic; revert just those files.

### Strategy 5: Revert a Specific Branch (Before Merge)

If you haven't merged a feature yet, just delete the branch.

```bash
# View all branches
git branch -a

# Delete local branch
git branch -d feature/<feature-name>

# Delete remote branch
git push origin --delete feature/<feature-name>

# The feature never gets to master; clean revert
```

**Use Case:** Realized a feature is not needed before merging to master.

---

## Common Scenarios & How to Handle Them

### Scenario 1: "I want to undo my last commit (not yet pushed)"

```bash
# Option A: Revert commit (keeps history)
git revert HEAD

# Option B: Amend the last commit
git reset --soft HEAD~1
git add .
git commit --amend -m "Updated message"

# Option C: Delete the commit entirely (destructive)
git reset --hard HEAD~1
```

### Scenario 2: "I merged a feature but it broke production"

```bash
# Find the merge commit
git log --oneline --graph | head -20

# Revert the merge (keeps history, safe)
git revert -m 1 <merge-commit-hash>

# OR reset to before the merge (destructive, if not shared)
git reset --hard <commit-before-merge>
```

### Scenario 3: "Multiple commits from a feature need to be removed"

```bash
# Revert them in reverse order (newest first)
git revert <newest-commit-hash>
git revert <middle-commit-hash>
git revert <oldest-commit-hash>

# OR reset to before the feature (destructive)
git reset --hard <commit-before-feature>
```

### Scenario 4: "I want to see what changed in a feature before reverting"

```bash
# Compare feature to master
git diff master..feature/auth

# See commits in feature
git log master..feature/auth --oneline

# See files changed
git diff --name-status master..feature/auth
```

### Scenario 5: "I want to keep one commit from a feature but discard the rest"

```bash
# Create a new branch from master
git checkout -b feature/cherry-pick master

# Cherry-pick the desired commit
git cherry-pick <desired-commit-hash>

# Discard the feature branch (contains unwanted commits)
git branch -D feature/auth
```

---

## Monitoring Your Changes

### See What's Changed Since Baseline

```bash
# Show all commits since baseline
git log 28efac5..HEAD --oneline

# Show files changed since baseline
git diff --name-only 28efac5..HEAD

# Show line count changes since baseline
git diff --stat 28efac5..HEAD

# Example output:
# app.py | 450 ++++++++++++++++++
# src/auth.py | 200 +++++++
# src/audit.py | 300 +++++++
# templates/login.html | 100 +++++
# total: 1050 insertions(+)
```

### Track Individual Feature Changes

```bash
# See commits in feature/auth
git log master..feature/auth --oneline

# See exactly what feature/auth changed
git diff master..feature/auth --stat

# See commits in feature/audit
git log feature/auth..feature/audit --oneline
```

### Generate Change Summary

```bash
# Create a summary of all changes
git log 28efac5..HEAD --oneline > CHANGES_SUMMARY.txt
git diff --stat 28efac5..HEAD > CHANGES_STATISTICS.txt

# Full diff for review
git diff 28efac5..HEAD > FULL_CHANGES.patch
```

---

## Backup & Recovery

### Create a Backup Before Major Changes

```bash
# Create a backup tag
git tag backup/before-feature-merge

# Create a backup branch
git branch backup/master-before-major-change

# List all backup tags
git tag -l | grep backup
```

### Recover from Backup

```bash
# List all commits
git reflog

# Recover to a specific commit via reflog
git reset --hard <reflog-entry>

# Or go back to a backup tag
git reset --hard backup/before-feature-merge
```

---

## Best Practices

### ✅ Do

- **Commit frequently** with clear messages
- **Use feature branches** for each feature
- **Keep branches small** and focused on one feature
- **Test before merging** to master
- **Use tags** for release points
- **Write commit messages** that explain the "why"
- **Review changes** before committing: `git diff --staged`

### ❌ Don't

- **Don't force push** to master or shared branches
- **Don't commit sensitive data** (passwords, API keys)
- **Don't use `reset --hard`** on shared branches
- **Don't merge without testing** in the branch first
- **Don't make massive commits** - break into logical chunks
- **Don't forget to commit** before switching branches

---

## Commit Message Format

Use consistent format for easy searching and understanding:

```bash
# Format: TYPE: Brief description (50 chars max)
#
# Longer explanation if needed (wrap at 72 chars)

# Examples:
git commit -m "FEATURE: Add user authentication with login page"
git commit -m "AUDIT: Create audit logging for customer actions"
git commit -m "UI: Make customer IDs clickable with action history"
git commit -m "FIX: Correct session timeout calculation"
git commit -m "TEST: Add load testing suite for 50K customers"
git commit -m "REFACTOR: Simplify audit database queries"
git commit -m "DOCS: Update README with deployment instructions"

# Supported types: FEATURE, FIX, TEST, REFACTOR, DOCS, AUDIT, UI, PERF
```

---

## Post-Implementation Checklist

### Before Production Release

- [ ] All features merged to master
- [ ] All tests passing
- [ ] Performance validated (baseline ±10%)
- [ ] Security reviewed
- [ ] Rollback procedures documented and tested
- [ ] Release tag created: `git tag -a v1.1-release -m "Production release"`
- [ ] Changelog generated
- [ ] Team notified of changes

### Maintaining Audit Trail

```bash
# Generate audit of all changes
git log 28efac5..HEAD --pretty=format:"%h|%an|%ad|%s" --date=short > AUDIT_TRAIL.csv

# Keep this file in version control for compliance
git add AUDIT_TRAIL.csv
git commit -m "DOCS: Audit trail of all changes since baseline"
```

---

## Verification Commands

### Verify Baseline Integrity

```bash
# Check baseline commit still exists
git show 28efac5

# Verify no accidental changes to baseline
git diff 28efac5..28efac5  # Should show nothing

# Count commits since baseline
git rev-list --count 28efac5..HEAD
```

### Verify Feature Branches

```bash
# List all branches
git branch -a

# Show merge status
git branch --merged
git branch --no-merged

# Show which commits are in which branches
git log --graph --oneline --all
```

---

## Emergency Contact & Escalation

If you're unsure about a reversion:

1. **Pause** - Don't execute destructive commands without understanding
2. **Check** - Run `git log` and `git diff` to see what will change
3. **Backup** - Create a tag or branch: `git tag backup/before-<action>`
4. **Test** - Do the reversion in a test branch first: `git checkout -b test/revert-<feature>`
5. **Review** - Have someone review before applying to master

---

## Summary Table

| Action | Command | Preserves History | Can Undo |
|--------|---------|-------------------|----------|
| Revert commit | `git revert <hash>` | ✅ Yes | ✅ Yes |
| Revert merge | `git revert -m 1 <hash>` | ✅ Yes | ✅ Yes |
| Undo last commit | `git reset --soft HEAD~1` | ✅ Yes | ✅ Yes |
| Delete commit | `git reset --hard HEAD~1` | ❌ No | ⚠️ Via reflog |
| Delete branch | `git branch -d <branch>` | ❌ No | ⚠️ Via reflog |
| Revert file | `git checkout <hash> -- file` | ✅ Yes | ✅ Yes |

---

**Last Updated:** January 10, 2026  
**Status:** Ready for implementation  
**Baseline:** `28efac5` - Safe point for all reversions
