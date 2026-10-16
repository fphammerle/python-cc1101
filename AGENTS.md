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
- Do **not** include a `Claude-Session:` line — the session URL is private.
- Explain **why**, not what — don't restate in prose what's already obvious from `git diff` of
  the commit (e.g. "add a notice to the README", "update section X").
- When content is copied or adapted from another repository, reference the sources with full
  permanent URLs (commit hash + path), e.g. `https://github.com/<owner>/<repo>/blob/<sha>/<path>`.
- Don't hard-wrap long lines in commit message bodies — write each paragraph / list item on a single line; git log viewers wrap them automatically.

## CHANGELOG

- Only document **user-facing** changes (features, bug fixes, removed support).
- Test tooling changes (e.g. `Pipfile`, `Pipfile.lock`) are not user-facing → no entry needed.
- CI checks all links in `CHANGELOG.md` with `blinkcheck` — only add URLs that are reachable.
- Wording for Python version support: `declare compatibility with \`python3.X\`` (under
  `### Added`), `compatibility with \`python3.X\`` (under `### Removed`)

## Pull requests

- Rebase on `master` before opening a PR.
- One commit per PR; amend rather than adding new commits.
- Force-push with `--force-with-lease` on feature branches.
- **Never force-push to `master`.**
- **Always open a pull request — never push directly to `master`.**
- **Never amend or force-push a branch whose PR is already merged or closed** — that rewrites
  history that's already landed (or been reviewed) and leaves a dangling branch that no longer
  reflects what merged. For a follow-up change, create a **new** branch (from current `master`)
  and a **new** PR instead.

## CI failures

- Fix CI failures automatically, iterating until all checks are green — no need to ask first.

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
  - If the body is wrong, edit the comment to the exact intended text (Dependabot does act on
    edited comments) and read it back again — don't leave a broken command posted.
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
