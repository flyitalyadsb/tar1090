# flyitalyadsb: tar1090's web files as an image, for the nginx pods of
# map.flyitalyadsb.com (nesso-infra k8s/flyitalyadsb/base/nginx.yaml). An init
# container copies /tar1090 into the pod at start. Until 2026-10-23 the files
# were downloaded once from wiedehopf/tar1090 master into a shared volume and
# never updated (the 2026-06-16 copy, upstream d892b99).
#
# The nginx.conf rewrite is the one that init container did, byte for byte:
# built from d892b99 this image reproduces the files served on 2026-10-23
# (329 html files and nginx.conf identical).
#
# html/ must already hold tar1090-db (flyitalyadsb/add-db.sh, run by
# docker.yaml before the checks): that init container never installed it, so
# until 2026-10-25 the map had no aircraft types, airlines or airport codes.
#
# Build context: the repository root. Build args: REVISION (the commit built).
FROM alpine:3.21 AS build
ARG REVISION=unknown
COPY html /src/html
COPY nginx.conf /src/nginx.conf
RUN mkdir -p /tar1090 \
 && cp -r /src/html /tar1090/ \
 && sed -e 's|/INSTANCE/|/|g' \
        -e 's|SOURCE_DIR|/run/tar1090|g' \
        -e 's|HTMLPATH|/usr/local/share/tar1090/html|g' \
        -e 's|/run/SERVICE/|/run/tar1090/|g' \
        /src/nginx.conf \
    | sed 's|/INSTANCE|/|g' > /tar1090/nginx.conf \
 && printf '{"commit":"%s"}\n' "$REVISION" > /tar1090/html/flyitalyadsb-version.json

FROM alpine:3.21
COPY --from=build /tar1090 /tar1090
# The init container: copy into the pod's volume. The touch marks when this
# pod installed it, which stats-api reports as tar1090_started (/api/cell.json).
ENTRYPOINT ["sh", "-c", "cp -a /tar1090/. /target/ && touch /target/html/flyitalyadsb-version.json"]
