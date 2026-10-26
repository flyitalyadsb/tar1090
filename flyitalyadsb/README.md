# flyitalyadsb build of tar1090

This branch is wiedehopf/tar1090 `master` plus this folder and `.github/`. It is
the web UI of mappa.flyitalyadsb.com. Upstream is merged daily
(`sync-upstream.yaml`); the old `master` of this fork, a few 2023 experiments, is
kept as it was and not used.

Each build of this branch adds tar1090-db, runs `check.py` and `smoke.mjs`,
then pushes `ghcr.io/flyitalyadsb/tar1090` tagged with the commit and `canary`:
- `cachebust.sh` (upstream's, as install.sh runs it): renames the scripts and
  stylesheet name_<md5>.ext and rewrites index.html. nginx.conf caches them 14
  days, so without it browsers and Cloudflare mixed releases (2026-10-26).
- `add-db.sh`: wiedehopf/tar1090-db at `tar1090-db.commit` into `html/db-<commit>`,
  as upstream's install.sh does: aircraft types (icon, wake category), airlines
  by callsign, military ranges, airport codes, registrations. `sync-upstream.yaml`
  moves `tar1090-db.commit` daily, because tar1090-db replaces its last commit.
- `check.py`: static checks. The strings the mappa vhost rewrites, the local
  scripts index.html loads, the database folder, and the nginx.conf placeholders.
- `smoke.mjs`: headless Chromium against a fake readsb. It fails on any
  JavaScript error, or if the aircraft types and airlines don't load.

argocd-image-updater (nesso-infra) gives `canary` to cell B and `stable` to cell A.
`promote.yaml` moves `stable` once cell B has run the canary for 20 h, in line
with cell A (https://api.flyitalyadsb.com/api/cells.json). The design is in
nesso-infra `docs/FLYITALYADSB-TWO-CELLS.md`, "Automatic release of readsb and
tar1090".

Local test, on a copy (add-db.sh changes html/index.html):
`git worktree add /tmp/t1090 HEAD && flyitalyadsb/add-db.sh /tmp/t1090 && (cd /tmp/t1090/html && bash ../cachebust.sh ../cachebust.list .) && python3 flyitalyadsb/check.py /tmp/t1090 && (cd flyitalyadsb && npm ci && npx playwright install chromium && node smoke.mjs /tmp/t1090)` (GNU sed and md5sum: on macOS put gsed first in PATH as sed).
