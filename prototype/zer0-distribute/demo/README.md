# The zer0-distribute demo and screen recording

What LinkedIn asks for with a Community Management API application is a screen recording of the app. This directory reproduces the one we submit, from scratch, on any machine.

## The recording

`recording/zer0-distribute-review-gate.mp4` — 33 seconds, 1280×800, H.264. A capture of the review dashboard served by `zer0-distribute serve`, ending with a person clicking **Approve** on a draft.

`recording/still-approval-gate.png` — a frame from it, for anywhere a video will not go.

**What it shows, in order:** the queue as a developer opens it · a draft composed from the repository's own release tag, with the marker showing where LinkedIn truncates the post · the exact `POST /rest/posts` payload that draft becomes · the developer's accumulated track record · the audience profiles the copy was written for · a human clicking Approve, and the counter dropping to zero.

**What it does not show, deliberately:** a post reaching LinkedIn. The app has not been granted API access — that is what the application is for — so `publish` is dry-run only and the recording shows the payload it *would* send. Faking a successful call would misrepresent the app to the reviewer evaluating it.

Everything on screen is live. The dashboard is served from real files, the drafts were composed by `zer0-distribute` from the demo repository's real git history, and the Approve click really does rewrite the draft on disk — you can verify it with `queue` before and after.

## Reproducing it

```bash
cd prototype/zer0-distribute/demo
./setup_demo.sh   /tmp/zer0-distribute-demo     # a normal developer's project: git history, tags, changelog, docs
./seed_state.sh   /tmp/zer0-distribute-demo     # publish history + drafts waiting for approval

python3 ../../zer0-distribute --root /tmp/zer0-distribute-demo serve &   # dashboard on :8765

npm i playwright                                          # once
node record.mjs --url http://127.0.0.1:8765 --out ./recording
```

That writes a `.webm`. To get the `.mp4` LinkedIn wants:

```bash
ffmpeg -i recording/page@*.webm -c:v libx264 -preset slow -crf 21 \
       -pix_fmt yuv420p -movflags +faststart recording/zer0-distribute-review-gate.mp4
```

`seed_state.sh` resets the queue every run, so the Approve click is always a real state change rather than a replay.

### If Chromium is not the build Playwright pins

Set `CHROMIUM_PATH` to a local full Chromium and skip the download. The headless *shell* cannot record video, so it has to be the full browser:

```bash
CHROMIUM_PATH=/path/to/chrome node record.mjs
```

## The narration, if you record a voice-over

Timed to the capture. Say less than this rather than more; the screen is doing the work.

| At | Say |
| --- | --- |
| 0:00 | "This is zer0-distribute. It reads what a developer already wrote in their repository — commits, tags, changelog entries, docs — and turns it into LinkedIn posts." |
| 0:05 | "Here is a draft it composed from this project's v0.6.0 release tag. The dashed line is where LinkedIn truncates, so you can see what a reader sees before they click." |
| 0:12 | "This is the exact request that draft becomes. A developer can read the payload before authorising anything — one post, to their own profile, `w_member_social`." |
| 0:19 | "The point of using it more than once: a track record. Four posts, tied to real shipped work, over three months." |
| 0:24 | "The audiences are declared in a config file. The tool never reads your connections or anyone's profile to guess who you write for." |
| 0:28 | "And this is the gate. Nothing publishes until a person clicks approve. There is no scheduler and no unattended mode." |

## Why a dashboard at all, for a command-line tool

Because approving copy is reading, and reading is what a browser is good at. Everything the dashboard does is available from the command line (`queue`, `preview`, `approve`), and the dashboard holds no state of its own — it reads and writes the same files. It exists so the moment that matters, a person deciding whether this should go out under their name, has somewhere legible to happen.
