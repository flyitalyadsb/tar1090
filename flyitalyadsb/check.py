#!/usr/bin/env python3
"""flyitalyadsb: static checks on tar1090's web files before an image is built.

python3 flyitalyadsb/check.py [SOURCE_DIR]   (default: the repository root)

- Every string that nesso-infra's mappa vhost rewrites with sub_filter is still
  in html/index.html exactly once. If upstream changes one, sub_filter skips it
  silently and the map loses its FlyItalyADSB title, description, icon,
  page name or analytics. Keep EXPECTED in step with
  nesso-infra k8s/flyitalyadsb/base/nginx-conf/mappa.flyitalyadsb.conf.
- Every local script and stylesheet index.html loads exists.
- nginx.conf still uses the placeholders the Dockerfile rewrites.
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
