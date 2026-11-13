# Agent Instructions

## Learning from mistakes

- Whenever you make a mistake and learn from it (pointed out by the user or noticed yourself),
  record the lesson in `AGENTS.md` **automatically**, without being asked, so it isn't repeated.
- If a mistake recurs although a rule for it already exists, make that rule stricter and more
  concrete (e.g. a mandatory check before acting) instead of just restating it.
- When writing or updating `AGENTS.md`, only add information that isn't already obvious from the
  repository itself (e.g. Git LFS tracking is visible in `.gitattributes` and marked on GitHub).

## Commit messages

- Attribution line: `Co-Authored-By: Claude <model name> <noreply@anthropic.com>` — always include the model name,
  e.g. `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
  (see https://web.archive.org/web/20261016172400/https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors)
- Do **not** include a `Claude-Session:` line — the session URL is private.
- Explain **why**, not what — don't restate in prose what's already obvious from `git diff` of
  the commit (e.g. "add a notice to the README", "update section X").
- When content is copied or adapted from another repository, reference the sources with full
  permanent URLs (commit hash + path), e.g. `https://github.com/<owner>/<repo>/blob/<sha>/<path>`.
- Don't hard-wrap long lines in commit message bodies — write each paragraph / list item on a single line; git log viewers wrap them automatically.

## CHANGELOG

- Only document **user-facing** changes (features, bug fixes, removed support).
- CI / build tooling changes (e.g. GitHub Actions workflows, `dependabot.yml`) are not
  user-facing → no entry needed.
- Test tooling changes (e.g. `Pipfile`, `Pipfile.lock`) are not user-facing → no entry needed.
- CI checks all links in `CHANGELOG.md` with `blinkcheck` — only add URLs that are reachable.
- Wording for Python version support: `declare compatibility with \`python3.X\`` (under
  `### Added`), `compatibility with \`python3.X\`` (under `### Removed`)

## Pull requests

- Rebase on `master` before opening a PR.
- One commit per PR; amend rather than adding new commits.
- Force-push with `--force-with-lease` on feature branches.
- **Never force-push to `master`.**
- **Always open a pull request — never push directly to `master`** (the only exception is
  fast-forwarding `master` to a pull request's head commit, see "Merging pull requests").
- **Never amend or force-push a branch whose PR is already merged or closed** — that rewrites
  history that's already landed (or been reviewed) and leaves a dangling branch that no longer
  reflects what merged. For a follow-up change, create a **new** branch (from current `master`)
  and a **new** PR instead.
  - This has happened despite this rule, so before **every** amend / push to an existing branch,
    first fetch its PR's current state from GitHub — pull requests may have been merged since you
    last looked.
- After a branch has been **fully** merged into `master`, delete it (on GitHub and locally). If
  only a subset of its commits was merged, keep it and rebase the remaining commits onto `master`
  instead (`git rebase --onto origin/master <last merged commit>`).

## Merging pull requests

- Keep existing commit signatures: never rewrite commits when merging — no GitHub squash or rebase
  merge, no cherry-picking or re-creating commits locally. Rewriting replaces signed commits (e.g.
  Dependabot's) with new, unsigned or differently signed ones.
- Pull requests / branches with a **single commit**, or whose changes should be squashed into a
  single commit: **fast-forward** `master` to the branch's head commit, so that exact commit lands
  on `master`.
  - Squashing belongs on the branch, done by its author — squashing someone else's signed commits
    yourself would drop their signatures.
  - The head commit's parent must be the current `master` tip. If it isn't, have the branch
    rebased by its author (for Dependabot: the rebase command, see "GitHub comments that
    @-mention a bot").
  - All checks must have passed on **that exact head commit** — a push to `master` doesn't wait
    for them the way GitHub's merge button does.
  - Then push the head commit: `git push origin <head-sha>:master` (no force) — GitHub marks the
    pull request as merged.
- Pull requests / branches with **multiple commits that should stay separate**: create a merge
  commit (GitHub merge method `merge`).
- Never call GitHub's merge API without an explicit merge method, and never use `squash` or `rebase`.
- When working on pull requests across the owner's repositories (e.g. merging Dependabot pull
  requests), first check whether each repository is **archived** and skip archived ones entirely —
  they're read-only, so their pull requests are to be ignored (no merging, no access requests).

## CI failures

- Fix CI failures automatically, iterating until all checks are green — no need to ask first.
- After a fix for a failing build is merged into `master`, **automatically** comment the
  Dependabot rebase command on each of Dependabot's open pull requests (without being asked), so
  their checks re-run on top of the fix instead of staying red. Follow the mandatory steps in
  "GitHub comments that @-mention a bot" below.

## Supported Python versions

- Keep the `tests` matrix in `.github/workflows/python.yml`, the `Programming Language :: Python :: 3.X`
  classifiers and `python_requires` in `setup.py` consistent when adding or dropping a Python version.
- The lowest supported Python version is the lowest one in that matrix.

## Files synced with other repositories

- Files starting with a `sync with <url>` comment are shared with other repositories. Keep them
  structurally in sync and mention in the PR description when a change should be ported to the
  referenced file as well.

## GitHub comments that @-mention a bot

- Commands like `@dependabot rebase` must reach GitHub as plain text — tool-call composition can
  silently insert stray characters (e.g. interpunct `·`) into `@mentions`, which stops the bot from
  recognizing the command. This has happened **repeatedly**, even with this rule in place, so the
  following steps are **mandatory**:
  - Before posting, check that the comment body is plain ASCII and contains no `·` (U+00B7).
  - Post such comments **one at a time**, never several in parallel.
  - Immediately after posting, read the comment back from GitHub and compare it character by
    character with the intended text. Only then post the next one.
  - Creating the comment has corrupted the body **every time** so far (stray `·` inside the
    command, plus an appended "Generated by Claude Code" footer), so never consider a bot command
    posted after the create call alone.
  - If the body is wrong, edit the comment **once** to the exact intended text (Dependabot does act
    on edited comments) and read it back again. Editing used to fix the body, but has also come
    back corrupted (twice in a row on fphammerle/docker-postfix#158).
  - If the edited body is still wrong, don't keep re-editing the same way. First re-check whether
    another **automatic** approach is available to fix the comment or re-post it (e.g. another
    tool or API that reaches GitHub without the corruption), and apply it, again with read-back.
  - Only if that fails too, ask the user to post the command, naming the **exact link** to post it
    at (the pull request URL, e.g. `https://github.com/<owner>/<repo>/pull/<number>`) and the exact
    command text; mention the broken comment's link so it can be deleted. Continue once the bot has
    acted on it.
- The same corruption also hits `@mentions` in PR descriptions and other GitHub text. Don't quote
  bot commands literally there (describe them instead, e.g. "the Dependabot rebase command"), and
  read every PR description back after creating or updating it.

## Pull request descriptions

- Don't include the Claude session URL — it's private. A footer containing it may be appended
  automatically when a PR is created; read the description back and remove it with an update.

## Pipfile / dependency management

- Generate `Pipfile.lock` on the **lowest** supported Python version.
- When a package is a conditional transitive dependency (e.g. `dill`, `typing_extensions`)
  whose pip markers depend on the lock-generation Python version, add it **explicitly** as a
  direct dependency in `Pipfile` (without a version marker) so it installs on all supported
  Python versions.
- Dependabot may regenerate `Pipfile.lock` on a newer Python version, picking dependency versions
  that dropped support for the lowest supported Python version (e.g. `platformdirs` requiring
  `python_version >= '3.11'`). Fix by re-running `pipenv lock` on the lowest supported version.
- When constrained packages (e.g. `setuptools`, `urllib3`) need to override transitive
  resolution, put them in `[packages]`, not `[dev-packages]`.
- `spidev` is pinned to `==3.4` in `[packages]` to match the version shipped by Raspbian's
  `python3-spidev` package (see comment in `Pipfile`). Don't bump it; `install_requires` stays
  unconstrained (`spidev`).

## Examples

- Keep the scripts in `examples/` working when changing the public API of `cc1101`.

## `AGENTS.md` across repositories

- The `AGENTS.md` files of the owner's repositories share most of their rules. Find them all with
  a GitHub code search for `user:fphammerle filename:AGENTS.md`.
- Creating an `AGENTS.md` for a repository: base it on **all** of them, not just one. Start from
  the closest sibling, keep only the rules that fit the particular repository (e.g. no Python /
  `Pipfile` rules for a `Dockerfile`-only repository, no rules on `Dockerfile` version pins for a
  repository without a `Dockerfile`), and adapt repository-specific examples
  (e.g. package names, commit subject conventions from `git log`). In the commit message, reference
  the individual source each part was based on with full permanent URLs (commit hash + path).
