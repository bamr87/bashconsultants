---
title: "work & play & dev &: job control for the sleep-deprived"
description: "A field guide to running work, play, and dev as background jobs, and why fork()-ing a toddler rewrites your whole scheduler and your priorities"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-06-20T10:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [muses]
tags: [work-life-balance, bash, shell, parenting, productivity, developer-life]
keywords: [work life balance for developers, job control bash background jobs, context switching cost, running side projects with a toddler, time management for technologists]
preview: /images/previews/work-play-dev-job-control-for-the-sleep-deprived.png
featured: false
excerpt: "You think your life runs work && play && dev. It actually runs work & play & dev &, until a child process forks into the foreground at nice -20."
---

## The fantasy

Every technologist has, at some low point, typed the equivalent of this into the universe and hit Enter:

```bash
$ work & play & dev &
[1] 24601
[2] 24602
[3] 24603
$
```

Three jobs. One ampersand each. All backgrounded, all running at once, prompt returned instantly, hands free. You lean back. You will earn a living, be a whole person, *and* finally ship the side project — concurrently, like a real machine. The dream of every overcommitted human is the same dream Unix sold us in the 1970s: throw an `&` on the end and walk away.

Then `jobs` reports the truth.

```bash
$ jobs
[1]   Running                 work &
[2]-  Stopped                 play
[3]+  Running (eating all memory)  dev &
```

`play` is **Stopped**. It's always Stopped. And somewhere off-screen, a fourth process you did not schedule is about to fork into the foreground and seize the terminal with a priority you are not authorized to override.

Let's talk about job control.

## You are not multi-core

Here is the lie at the center of modern adult life: that you are running these things in parallel. You are not. You have one core. One. A single execution unit doing what single cores have always done — *time-slicing* so fast it produces the convincing illusion of simultaneity. The central processing unit (CPU) you bought in 2019 fakes multitasking by switching between processes thousands of times a second. You fake it by answering a Slack message at a playground.

The catch is the context switch. When a real CPU switches processes it has to dump the registers, flush part of the cache, load the next process's state, and warm everything back up. It's cheap in silicon and ruinous in wetware. When *you* switch from `dev` to `work` to "why is the toddler quiet," you pay a context-switch tax measured not in nanoseconds but in the time it takes to remember what the function you were writing was supposed to return. The often-cited figure from Gloria Mark's University of California, Irvine interruption research is about 23 minutes to get back to an interrupted task; her [study on the cost of interrupted work](https://ics.uci.edu/~gmark/chi08-mark.pdf) found people finish interrupted tasks faster and pay for it in stress and effort. Your scheduler is running at maybe forty productive minutes an hour, and that's on a good day with no SIGCHLD storm. (We'll get to SIGCHLD.)

So the goal was never true parallelism. It was a tolerable time-slicing policy. Most of us are running the worst one available: switch on every interrupt, prioritize whatever screamed loudest, and let the lowest-priority job starve.

## `jobs -l`: meet the processes

Before you can schedule three jobs you should know their resource profiles, because they do not behave alike.

**`work`** is the daemon that pays for the electricity. It launches at boot whether you want it to or not, it has a habit of quietly raising its own priority — it starts the day at a polite `nice 0` and by 4 p.m. it's somehow renice'd itself to `-5` and is preempting everything — and it *refuses to die on logout*. You close the laptop; `work` keeps running, because some prior version of you ran it with `nohup`:

```bash
$ nohup work &
work: ignoring input and appending output to 'nohup.out'
```

`nohup` means "no hangup" — the process survives the terminal closing. That's the technical name for the email that finds you at 9:47 p.m. It is immune to the hangup signal by design. You did this to yourself.

**`dev`** is the fun one and the dangerous one. It's your daemon, the thing you actually chose — the side project, the homelab, the repo nobody asked for. It is also a memory hog that only makes progress in long uninterrupted blocks. `dev` does not time-slice gracefully. You cannot give it ninety seconds between other tasks and expect output; it needs the cache hot and the whole working set resident, which is exactly the condition your life is least able to provide. When `dev` gets starved, it doesn't crash — it just sits there as a process you keep meaning to bring back to the foreground, accruing guilt instead of commits.

**`play`** is the process with the highest `nice` value in the system — `nice 19`, maximum niceness, which in the wonderful inversion of Unix means *lowest priority*. The nicer the process, the more readily it yields the CPU to everything else. `play` is so polite it never demands anything, which is precisely why it never runs. It is Stopped in your `jobs` list right now. Hold that thought, because the kernel has plans for it.

## fork()

Now the part nobody benchmarks for.

At some point you run `fork()`. The child process spins up. And every assumption your scheduler made goes out the window, because this is not a job you can background.

A forked child *inherits the parent's environment*. This is true in Unix and it is true in the kitchen — the child gets a copy of your environment variables, your habits, your exported defaults, the way you say the word you wish you didn't say. `export PATIENCE=thin` and watch it propagate.

But the real engineering problem is signals. In Unix, when a child process stops or terminates, the kernel sends the parent a signal called — and I want to be clear that I am not making this up — **`SIGCHLD`**. The child literally signals the parent. A toddler is a process that fires `SIGCHLD` at unpredictable intervals, demanding the parent immediately stop what it's doing and handle it, and if the parent ignores the signal the child does not get cleaned up and the situation only gets worse. You end up writing a signal handler:

```bash
trap 'handle_snack_request' SIGCHLD
```

And here is where job control breaks down completely:

- You cannot run the child in the background. There is no `child &`. It runs in the foreground by divine right and holds the terminal.
- You cannot `nohup` it. It does not survive you leaving the room; it follows you, signaling.
- You cannot `renice` it. It runs at `nice -20`, the maximum *negative* niceness, the highest priority the system allows — and on a real Unix box, setting a priority that aggressive requires root. You are not root. You filed the request and were denied. The toddler is root.
- And you absolutely cannot `kill -9` it. `kill -9` sends `SIGKILL`, the one signal a process cannot catch, block, or ignore — the nuclear option that always works. It does not work here. It is the one place in all of computing where `kill -9` is off the table, and thank goodness, but operationally: your hardest preemption tool has been removed from the rack.

So now your `jobs` list looks like this:

```bash
$ jobs
[1]   Running                 work &
[2]-  Stopped                 play
[3]   Stopped                 dev
[4]+  Running (foreground)    child   # nice -20, uninterruptible, owns the terminal
```

`dev` got bumped to Stopped to make room. Of course it did.

## Thrashing

The naive response is to oversubscribe — keep all four "running," background everything you can, and push harder. This is where you meet the two failure modes every overloaded system shares with every overloaded parent.

The first is **swap**. When a machine runs out of random-access memory (RAM) it starts paging memory out to disk, and if it's doing that constantly it enters a state called *thrashing*: it spends so much effort moving pages back and forth that it does almost no actual work. The load average climbs, every process slows, and the box is technically up but accomplishing nothing. The human version is a Tuesday where you were busy for fourteen hours and shipped not one thing. You were thrashing. You were paging your attention to disk.

The second is the **zombie**. In Unix a zombie is a child process that has finished executing but whose parent never called `wait()` to read its exit status — so it lingers in the process table, done but un-reaped. Your life is full of zombies: the laundry that is technically washed but will never be folded, the pull request (PR) that's approved but un-merged, the email you've read and mentally answered and not actually sent. Each one holds a slot. Enough un-reaped tasks and you run out of entries in the table, and the strange thing about zombies is you can't `kill` them — they're already dead. You have to reap them. The only fix is to finish the thing you already finished.

Meanwhile the parent, having not slept, has become a different kind of zombie entirely. The metaphor, like the laundry, does not fold cleanly.

## The out-of-memory (OOM) killer always comes for `play`

When memory pressure gets bad enough that swap can't save it, the Linux kernel deploys its last resort: the **OOM killer**. It walks the process list, scores each one on a heuristic of how much it'd reclaim and how expendable it looks, and it *kills* the loser to keep the system alive. (If you want the gory scoring details, the kernel documents the [`oom_score_adj` tunable](https://docs.kernel.org/filesystems/proc.html) in `/proc`.)

You already know which process it picks. It is never `work` — `work` pays for the RAM. It is never `child` — `child` is `nice -20` and untouchable. It is `dev`, and when `dev` is already Stopped, it is `play`. The OOM killer comes for `play` first, every single time, because `play` is the most expendable-looking thing in the table. It made itself maximally nice. It never demanded a slice. And so the system, doing exactly what it was configured to do, reaps the one process whose entire purpose was to make running the others bearable.

This is the actual bug. Not that there are too many jobs. That the scheduler is configured to starve the one job you cannot articulate a business case for.

## A scheduler that actually works

The fix is not a productivity system. It's a scheduling policy, and the good ones share a few properties.

**Stop pretending you're parallel.** `work & play & dev &` is a lie your prompt tells you. You time-slice; the only question is whether you do it on purpose. Run one job in the foreground at a time and let it actually own the core. A focused hour on `dev` beats four hours of `dev` getting `SIGCHLD`'d every nine minutes — because of the context-switch tax, those are not the same four hours.

**`cron` the non-negotiables.** The recurring, load-bearing events should not depend on you having spare attention to schedule them. Bedtime, the standing date, the gym, daycare pickup — these go in `crontab`, they fire on a timer, and they are not subject to renegotiation by whichever process is loudest at 5 p.m. A `cron` job doesn't ask permission. That's the feature.

```bash
# m  h  dom mon dow   command
  0 18   *   *  1-5   run play --no-laptop   # weekdays, 6pm, non-negotiable
  0 21   *   *   *    reap_zombies           # fold the laundry you already washed
```

**Batch your context switches.** The cost isn't the work, it's the switch. Answer `work` in two or three deliberate windows, not continuously. Every time you `fg` and `bg` between jobs on a whim you pay the tax twice.

**Give `play` a guaranteed slice and protect it from the OOM killer.** This is the whole point. The process with no business case is the one keeping the box alive; reserve CPU for it explicitly, the way you'd pin a critical service so the kernel can't reap it. If `play` only runs on the scraps left after `work` and `dev` and `child`, it runs never, and then the other three degrade too, because they were always running on `play`'s output without admitting it.

**Let `dev` detach.** This is what `tmux` and `screen` are *for* — a session that keeps running after you disconnect and is sitting exactly where you left it when you reattach. `dev` cannot demand a four-hour block from a life that contains a `nice -20` child. But it can survive interruption if you stop expecting to hold its whole state in your head and start letting the session hold it for you. Write the failing test before you stand up. Leave a `// TODO: you were here` at the cursor. Reattach, don't restart.

**And handle the one interrupt that's worth it synchronously.** Here's the turn. Everything above is about defending your jobs from interruption — except one. The `child` process is the single workload in the whole system where stopping the foreground task to handle the signal *is the task*. You will spend a number of years being interrupted by it, and the cruel math is that the interruptions feel like the thing keeping you from your real work, right up until the window closes and you understand they were the workload the entire time. `work` will fork new instances of itself forever. `dev` will still compile in a decade. The `nice -20` child downgrades to `nice 5`, then `nice 10`, then forks a process of its own and stops sending you `SIGCHLD` at all, and you would give a kidney to get one more.

So: protect `play`. Detach `dev`. `cron` the rest. And when the small process signals, handle it in the foreground, on purpose, without resentment. That's not a failure of your scheduler. On a good day, that *is* the scheduler.

## The same bug runs your business

Strip the parenting jokes and this is the scheduler running most small businesses we walk into. There's a `work` daemon that renice's itself to `-5` and eats every interrupt — the loudest customer, the squeakiest invoice, the integration that broke this morning. There's a `dev` job that never gets a focused block, so the migration off QuickBooks or the reporting cleanup sits Stopped for two years. And there's a `play` process — the strategic project with no screaming deadline and no obvious business case — that the OOM killer reaps first every quarter, because nobody pinned it.

The teams that ship the strategic work are not working more hours. They've just stopped letting the loudest process and the kernel's lazy default decide the schedule. They give the load-bearing project a guaranteed slice, batch the interrupts into windows, chunk it to a size one slice can carry — the argument in [[Three is the magic number for automation that holds]] — and detach the long-running work so a single interruption doesn't cost a full restart. The fix is a policy, not a person grinding harder.

## exit 0

You will not run `work & play & dev &` in true parallel. No one does; the people who look like they do are just running a better time-slicing policy and not telling you about the swap. You have one core. You always did. The skill was never doing all of it at once — it was choosing, slice by slice, which process gets the core right now, and refusing to let the loudest one or the kernel's lazy default decide for you.

Now if you'll excuse me, job `[4]` is signaling, and this one I take in the foreground.

```bash
$ fg %4
```

---

*At BASH Consulting we spend our days untangling systems that are technically running but quietly thrashing — the strategic project that's been Stopped for two years because the loud daemons eat every slice. If your team's scheduler keeps reaping the wrong process, see [[Software development]].*
