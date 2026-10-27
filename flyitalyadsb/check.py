#!/usr/bin/env python3
"""flyitalyadsb: static checks on tar1090's web files before an image is built.

python3 flyitalyadsb/check.py [SOURCE_DIR]   (default: the repository root)

- Every string that nesso-infra's mappa vhost rewrites with sub_filter is still
  in html/index.html exactly once. If upstream changes one, sub_filter skips it
  silently and the map loses its FlyItalyADSB title, description, icon,
  page name or analytics. Keep EXPECTED in step with
  nesso-infra k8s/flyitalyadsb/base/nginx-conf/mappa.flyitalyadsb.conf.
- Every local script and stylesheet index.html loads exists.
- index.html's databaseFolder is a db-* folder (add-db.sh) holding the lookup
  tables, gzipped: nginx.conf sends db-*.js with Content-Encoding gzip.
- nginx.conf still uses the placeholders the Dockerfile rewrites.
- The files in cachebust.list were renamed name_<md5>.ext and index.html loads
  those names (docker.yaml runs cachebust.sh after add-db.sh): nginx.conf caches
  every html/*.js for 14 days, so a fixed name mixes releases in browsers and
  at Cloudflare (2026-10-26: the 16 June planeObject.js still served from the
  edge with a new defaults.js, ReferenceError headingLineMinutes).
"""
import pathlib
import re
import sys

EXPECTED = (
    "</head>",
    "<title>tar1090</title>",
    '<meta name="description" content="tar1090 - ADS-B plane tracking interface">',
    '<script src="config.js"></script>',
    'href="images/tar1090-favicon.png"',
)
DB_FILES = ("icao_aircraft_types2.js", "operators.js", "ranges.js", "airport-coords.js", "regIcao.js")
PLACEHOLDERS = ("/INSTANCE/", "SOURCE_DIR", "HTMLPATH", "/run/SERVICE/")


def check(root):
    errors = []
    html = root / "html"
    index = (html / "index.html").read_text()
    for s in EXPECTED:
        n = index.count(s)
        if n != 1:
            errors.append(f"index.html has {n} of {s!r} (the mappa vhost's sub_filter expects exactly 1)")
    for ref in re.findall(r'<(?:script[^>]*\bsrc|link[^>]*\bhref)="([^"]+)"', index):
        if re.match(r"^(?:[a-z]+:)?//", ref) or ref.startswith(("data:", "#")):
            continue
        path = ref.split("?")[0]
        if not (html / path).is_file():
            errors.append(f"index.html loads {ref}, which is not in html/")
    folders = re.findall(r'let databaseFolder = "([^"]*)";', index)
    if len(folders) != 1:
        errors.append(f"index.html has {len(folders)} databaseFolder assignments (expected 1)")
    elif not folders[0].startswith("db-"):
        errors.append(f'databaseFolder is "{folders[0]}", not a db-* folder: run flyitalyadsb/add-db.sh first')
    else:
        for name in DB_FILES:
            p = html / folders[0] / name
            if not p.is_file():
                errors.append(f"{folders[0]}/{name} is missing")
            elif p.read_bytes()[:2] != b"\x1f\x8b":
                errors.append(f"{folders[0]}/{name} is not gzipped (nginx.conf sends it with Content-Encoding gzip)")
    for line in (root / "cachebust.list").read_text().split():
        stem, _, ext = line.rpartition(".")
        hashed = [p for p in html.glob(f"{stem}_*.{ext}") if re.fullmatch(rf"{re.escape(pathlib.Path(stem).name)}_[0-9a-f]{{32}}\.{ext}", p.name)]
        if (html / line).exists() or len(hashed) != 1:
            errors.append(f"{line} is not cache-busted (expected one {stem}_<md5>.{ext}): run cachebust.sh as docker.yaml does")
        elif hashed[0].relative_to(html).as_posix() not in index:
            errors.append(f"index.html doesn't load {hashed[0].relative_to(html).as_posix()}")
    conf = (root / "nginx.conf").read_text()
    for p in PLACEHOLDERS:
        if p not in conf:
            errors.append(f"nginx.conf no longer has the placeholder {p}: the Dockerfile's rewrite is out of date")
    return errors


if __name__ == "__main__":
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = check(root)
    for e in errors:
        print("ERROR:", e)
    print("ok" if not errors else f"{len(errors)} problem(s)")
    sys.exit(1 if errors else 0)
