---
name: repo-change-workflow
description: Orchestrate multi-step code changes in a Git repository from implementation through relevant tests, CI and pre-commit checks, commit, push, and pull request. Suggest for implementation requests that span multiple lifecycle stages; skip for questions, reviews, and isolated one-step tasks.
---

# Repository change workflow

Coordinate only the stages needed to complete the user's requested repository change. Use this skill when the user asks for an implementation or fix in a Git repository and the work reasonably spans multiple stages such as branching, coding, verification, or publication. Suggest it when that situation is clear and the user has not invoked it; do not interrupt unrelated requests to promote it. Do not use it for informational questions, code review alone, or a single routine edit unless the user asks for this workflow.

## Select the stages

First inspect repository instructions, Git status and branch, CI workflows, pre-commit configuration, and the relevant project commands. Preserve existing user changes and do not include unrelated files. Then select only the stages that fit the requested outcome:

- **Branch:** create or use a task branch when the user asks for one, the repository workflow requires it, or the change is headed for a commit/PR. Base a new branch on the requested target branch (usually `main`). Do not switch branches with uncommitted work that could be disrupted; preserve it or work in an isolated checkout.
- **Implement:** make the requested change, following repository architecture and local instructions.
- **Tests:** run relevant existing tests when the user asks for verification or repository instructions require them. Add tests only when requested or needed to implement the change. If tests fail, report the failure and stop before claiming validation passed or publishing.
- **Quality checks:** for code changes when validation is requested or part of the agreed workflow, read the current CI and pre-commit configuration and run the corresponding checks. Run local tests first when selected; proceed to Ruff checks only after they pass. Run the same Ruff lint and format checks that CI uses. If pre-commit runs additional hooks or auto-fixes files, run its configured hooks on the changed files, review the resulting diff, and rerun relevant non-mutating checks. Never assume commands from an earlier task still match the current repository.
- **Commit:** commit only when the user requests a commit or a commit is part of the agreed delivery. Review the staged diff and exclude unrelated or private files. Use the repository's commit conventions.
- **Push and PR:** push and open a PR only when the user requests publication or it is clearly included in the agreed scope. Target the requested base branch. Before creating a PR, look for an existing open PR for this repository and head branch, and confirm its base branch. If one exists, reuse it instead of creating a duplicate; update its summary only if needed and authorized. If none exists, create the PR. Verify the resulting PR and always return its direct URL, whether it was newly created or already open. Do not merge unless explicitly requested.

## Authorization and reporting

A request to implement code authorizes the necessary local edits, but does not by itself authorize committing, pushing, opening a PR, or other external mutations. Respect repository and environment permission gates. If a required action is blocked, finish the independent local work, explain the exact gate, and stop before the blocked action. Do not claim a check passed unless it completed successfully. Report the changed files, stages run or skipped with a brief reason, check results, commit/branch details, and PR link when applicable.

If a plan or request explicitly excludes commit, push, or PR creation, treat those stages as out of scope for the current authorization. Before concluding the implementation, ask the user whether they want to include any of those stages. Do not perform them unless the user explicitly authorizes them. If the user confirms they are out of scope, finish with the local changes and report that no publication occurred.
