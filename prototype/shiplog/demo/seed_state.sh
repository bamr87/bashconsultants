#!/usr/bin/env bash
# Put the demo repository into the state the screen recording opens on:
# a few posts already published (so the track record has something in it) and
# drafts waiting for a human (so the approval gate can be demonstrated).
#
# Every draft here is composed by shiplog from the demo repo's own git history
# and files. Nothing is hand-written for the camera.
#
# Usage:  ./seed_state.sh [demo-dir]        (default: /tmp/shiplog-demo)
set -euo pipefail

TARGET="${1:-/tmp/shiplog-demo}"
SHIPLOG="$(cd "$(dirname "$0")/.." && pwd)"
run() { python3 "$SHIPLOG" --root "$TARGET" "$@"; }

rm -rf "$TARGET/.shiplog"

# --- history: published posts, backdated, so `portfolio` has real numbers ----
seed_published() {
  run draft "$1" --audience "$2" >/dev/null
  run record "$3" --at "$4" --urn "urn:li:share:demo-$3" >/dev/null
  rm -f "$TARGET/.shiplog/queue/$3.md"
}

seed_published "changelog:0-5-0"      peer-devs      "changelog-0-5-0"     "2026-05-21T15:00:00Z"
seed_published "post:at-least-once"   peer-devs      "post-at-least-once"  "2026-06-09T13:20:00Z"
seed_published "commits:recent"       backend-hiring "commits-recent"      "2026-06-27T09:45:00Z"
seed_published "changelog:0-6-0"      backend-hiring "changelog-0-6-0"     "2026-07-11T11:10:00Z"

# --- one already approved, waiting on `publish` -----------------------------
run draft "post:why-not-a-broker" --audience peer-devs >/dev/null
run approve "post-why-not-a-broker" >/dev/null

# --- the one a person approves on camera ------------------------------------
run draft "tag:v0.6.0" --audience backend-hiring >/dev/null

echo "seeded:"
run queue
echo
run portfolio
