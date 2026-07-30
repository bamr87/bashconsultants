#!/usr/bin/env bash
# Build the demo repository the walkthrough and the screen recording run against.
#
# It stands in for a normal developer's project: a real git history with
# conventional commits, an annotated release tag, a CHANGELOG, and a doc the
# author wrote. shiplog reads exactly these — nothing is staged or faked for
# the camera beyond the repository itself.
#
# Usage:  ./setup_demo.sh [target-dir]      (default: /tmp/shiplog-demo)
set -euo pipefail

TARGET="${1:-/tmp/shiplog-demo}"
rm -rf "$TARGET"
mkdir -p "$TARGET/docs"
cd "$TARGET"

cat > README.md <<'EOF'
# queuectl

A small job queue for people who do not want a broker. SQLite for storage,
one binary, at-least-once delivery.
EOF

cat > CHANGELOG.md <<'EOF'
# Change Log

## [0.6.0]

- **Backpressure** — a worker that falls behind now slows its own fetch instead of letting the queue grow without bound.
- **Visibility timeout is per-job** — long jobs no longer need a global timeout tuned for the worst case.
- **`queuectl drain`** — stop accepting work and finish what is in flight, for deploys.

## [0.5.0]

- **At-least-once delivery** — acknowledged jobs are removed in the same transaction that records the result.
- **SQLite WAL mode** — readers no longer block the writer.
EOF

cat > docs/why-not-a-broker.md <<'EOF'
# Why queuectl does not use a message broker

Most teams reaching for a job queue do not have a throughput problem. They have
an ordering problem, a retry problem, and an on-call problem, and a broker
solves the first while making the other two someone else's job.

queuectl keeps the queue in the database you already back up. You lose
horizontal fan-out past a few thousand jobs a second, and you gain the ability
to debug a stuck job with a SELECT statement at two in the morning.
EOF

cat > docs/at-least-once.md <<'EOF'
# What at-least-once actually costs you

At-least-once delivery means your handler will run twice for the same job, and
the second run has to be harmless. That is not a library feature you can
install, it is a property of the code you write.

The practical version: make the write idempotent on a key the job already
carries, and stop reaching for distributed locks to paper over a handler that
is not safe to repeat.
EOF

git init -q
git config user.email "dev@example.com"
git config user.name "Demo Developer"

mkdir -p src
# Each commit touches a file, so the history is real rather than one squashed
# import — `sources` reads git log, and an empty commit would teach it nothing.
commit() {
  printf '// %s\n' "$1" >> "src/${3:-queue}.go"
  git add -A
  GIT_COMMITTER_DATE="$2" git commit -q --date="$2" -m "$1"
}

commit "feat(queue): at-least-once delivery with transactional ack" "2026-06-02T09:12:00" queue
commit "perf(storage): enable SQLite WAL so reads stop blocking writes" "2026-06-14T11:40:00" storage
commit "feat(worker): per-job visibility timeout" "2026-07-01T10:05:00" worker
commit "fix(worker): stop double-counting retries after a crash" "2026-07-09T16:22:00" worker
commit "feat(cli): queuectl drain for zero-drop deploys" "2026-07-18T14:31:00" cli
commit "feat(worker): backpressure when a worker falls behind" "2026-07-24T09:55:00" worker

GIT_COMMITTER_DATE="2026-07-24T10:00:00" git tag -a v0.6.0 \
  -m "Backpressure, per-job visibility timeouts, and a drain command for deploys."

cat > shiplog.toml <<'EOF'
# shiplog — publish what you ship.

[author]
kind = "member"
member_urn = "urn:li:person:DEMO_PLACEHOLDER"
organization_urn = ""
name = "Demo Developer"
headline = "Backend engineer — queues, storage, boring reliability"

[sources]
changelog = "CHANGELOG.md"
posts = ["docs/**/*.md"]
include_tags = true
include_commits = true
commit_types = ["feat", "fix", "perf"]

[[audience]]
id = "backend-hiring"
label = "Engineering managers hiring backend developers"
reads_for = "evidence someone can ship and explain their work"
tone = "plain, specific, no hype"
hashtags = ["Backend", "DistributedSystems"]

[[audience]]
id = "peer-devs"
label = "Other developers building queues and storage"
reads_for = "the trade-off you actually made"
tone = "practitioner to practitioner"
hashtags = ["DevTools", "OpenSource"]
EOF

echo "demo repository ready: $TARGET"
