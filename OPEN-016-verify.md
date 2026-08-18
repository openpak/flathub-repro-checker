# OPEN-016 Verification 2026-08-18T06:05Z

## GHCR Visibility (a)
- `ghcr.io/openpak/flatpak-builder-lint:unprivileged` still private
  - `curl https://ghcr.io/token?service=ghcr.io&scope=repository:openpak/flatpak-builder-lint:pull` → `{"errors":[{"code":"UNAUTHORIZED"}]}`
  - `docker manifest inspect ghcr.io/openpak/flatpak-builder-lint:unprivileged` → `unauthorized`
  - `gh api /orgs/openpak/packages/container/flatpak-builder-lint` → `403 read:packages scope missing`
  - Positive control: `ghcr.io/flathub-infra/flatpak-builder-lint:unprivileged` manifest succeeds, token returns `{"token":"..."}`
  - Republish `32066984044` queued but versions remain private until visibility flipped
  - Decision: keep-upstream until public, filed OPEN-017 for `https://github.com/orgs/openpak/packages/container/flatpak-builder-lint/settings` Danger Zone → Public
- `ghcr.io/openpak/flatpak-builder-lint:latest` same private

## Seccomp (b)
- `tests/test_integration.py:46` follow-fork to `https://raw.githubusercontent.com/openpak/vorarbeiter/refs/heads/main/flatpak.seccomp.json`
- Hashes identical: `sha256 7a4928bb6479829ee0093d6407d6fdf12bb0397ad25161648f44364c1096e91f` for openpak, flathub-infra, and local `vorarbeiter/flatpak.seccomp.json`

## Docs (c)
- `README.md:10` keep-upstream until image public (same root cause)

## Ledger
- `rebrand-p1-c6-ledger.tsv` rows for ci.yml:21, test_integration.py:52, test_integration.py:46, README.md:10 all present with decision and rationale

## Verification
- `python3 verify-open016.py --offline` PASS
- `python3 verify-open016.py --online` PASS (expects UNAUTHORIZED for keep-upstream)
- Break-test: temp repoint ci.yml to openpak → FAIL image-env, restored → PASS
- `flathub-repro-checker` unit tests: 46 passed, `ruff check` PASS, `mypy` PASS, no GHCR_TOKEN
keep-upstream verified
final verification Tue 18 Aug 2026 07:13:45 IST
