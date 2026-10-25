#!/bin/sh
# flyitalyadsb: add wiedehopf/tar1090-db to tar1090's web files, as install.sh does.
#
#   flyitalyadsb/add-db.sh SOURCE_DIR [COMMIT]   (default: flyitalyadsb/tar1090-db.commit)
#
# The map loads its lookup tables from html/<databaseFolder>/: aircraft types
# (icon shape, wake category), airlines by callsign, military address ranges,
# airport codes for "jump to", registrations for search. Until 2026-10-25 the
# folder was never installed on mappa.flyitalyadsb.com: every aircraft showed
# "Airline: n/a" and ~3% had the wrong icon.
#
# The folder is db-<short commit>, as install.sh names it: nginx.conf serves
# db-*.js with Content-Encoding gzip (the files are gzipped) and a 14-day cache,
# so each database needs its own folder name. tar1090-db replaces its last
# commit when the data changes; sync-upstream.yaml moves tar1090-db.commit along.
set -eu
src=$1
commit=${2:-$(cat "$(dirname "$0")/tar1090-db.commit")}
short=$(printf %.7s "$commit")
db="$src/html/db-$short"
index="$src/html/index.html"

n=$(grep -c 'let databaseFolder = .*;' "$index" || true)
if [ "$n" != 1 ]; then
  echo "index.html has $n databaseFolder assignments (expected 1)" >&2
  exit 1
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL "https://github.com/wiedehopf/tar1090-db/archive/$commit.tar.gz" | tar xz -C "$tmp" --strip-components=1
mkdir -p "$db"
cp -R "$tmp/db/." "$db/"
sed -i.orig "s/let databaseFolder = .*;/let databaseFolder = \"db-$short\";/" "$index"
rm "$index.orig"
echo "tar1090-db $short: $(ls "$db" | wc -l | tr -d ' ') files in $db"
