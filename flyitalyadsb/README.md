# flyitalyadsb build of tar1090

This branch is wiedehopf/tar1090 `master` plus this folder and `.github/`. It is
the web UI of mappa.flyitalyadsb.com. Upstream is merged daily
(`sync-upstream.yaml`); the old `master` of this fork, a few 2023 experiments, is
kept as it was and not used.

Each build of this branch runs `check.py` and `smoke.mjs`, then pushes
`ghcr.io/flyitalyadsb/tar1090` tagged with the commit and `canary`:
- `check.py`: static checks. The strings the mappa vhost rewrites, the local
  scripts index.html loads, and the nginx.conf placeholders.
- `smoke.mjs`: headless Chromium against a fake readsb. It fails on any
  JavaScript error.

argocd-image-updater (nesso-infra) gives `canary` to cell B and `stable` to cell A.
`promote.yaml` moves `stable` once cell B has run the canary for 20 h, in line
with cell A (https://api.flyitalyadsb.com/api/cells.json). The design is in
nesso-infra `docs/FLYITALYADSB-TWO-CELLS.md`, "Automatic release of readsb and
tar1090".

Local test:
`python3 flyitalyadsb/check.py . && (cd flyitalyadsb && npm ci && npx playwright install chromium && node smoke.mjs ..)`
