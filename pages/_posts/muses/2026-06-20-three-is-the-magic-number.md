---
title: "Three is the magic number for automation that holds"
sub-title: "Triangular loops, chunked goals, and the haiku now running the front of the trade"
description: "Build automation that corrects itself — three-node loops, goals chunked to one slice, and a small fast AI routing the work at the front"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-06-20T11:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [muses, ai]
tags: [automation, workflow-design, bash, shell, ai-engineering, systems-thinking, productivity]
keywords: [automation design rule of three, triangular routing efficiency, chunking tasks and goals, feedback loop three stages, llm router cascade pattern, small model triage automation]
preview: /images/previews/three-is-the-magic-number-for-automation-that-hold.png
featured: false
excerpt: "The triangle is the only rigid shape, the most efficient loops have three nodes, and a small fast AI now sits at the front of the trade, routing the work."
---

> *One long brittle pipe—*
> *a single stage coughs, the whole*
> *morning runs to null.*

## The straight line that always breaks

Here is the automation everyone writes first. It is a straight line. It reads like a sentence and it dies like one.

```bash
$ fetch | clean | enrich | score | route | notify | log | archive
```

Eight stages, seven pipes, one direction. It feels efficient because it *looks* efficient — no branching, no loops, no ceremony, just data falling downhill from left to right. You ship it. It runs beautifully for nine days. On the tenth, `enrich` times out against a third-party application programming interface (API) at 6 a.m., and because a Unix pipeline is only as alive as its narrowest dead stage, everything downstream of `enrich` receives an empty stream and dutifully processes nothing. `score` scores nothing. `route` routes nothing. `notify` notifies no one that nothing happened. By the time you look, the whole morning has run cleanly to `null` and reported success, because exit code 0 is the most dangerous lie in computing.

The straight line is brittle for a reason that has nothing to do with this particular API. It's brittle because it has no way to *correct itself*. Data goes in one end and out the other, and nowhere in that geometry is there a path for the output to inform the input. A line is not a system. A line is a hope with stages.

The fix is not more stages. The fix is a shape. And the shape, it turns out, is almost always a triangle — because three is the magic number, and I mean that structurally, not mystically.

## Three is the magic number

> *Two legs and it tips,*
> *four legs rock on uneven*
> *floors—three sits dead still.*

Bob Dorough sang it in 1973 — *a man and a woman had a little baby, yes they did, there were three in the family, that's a magic number* — and a generation learned multiplication from a cartoon that was, underneath the harmony, making a claim about structure. Three is not magic because it's lucky. Three is magic because it's the first number that holds.

Watch a three-legged stool on a stone floor. It never wobbles. It *cannot* wobble, because three points define exactly one plane, and any three points — however uneven the floor — sit flush against the single plane they define. A four-legged chair on the same floor rocks, because four points over-define the plane and the floor gets a vote. This is why surveyors use tripods, why your camera mount has three legs, why the milking stool has survived ten thousand years of furniture innovation unchanged. Three is the minimum that is also the maximum: the fewest supports that guarantee stability, and one more than that buys you nothing but a rock.

Now look at the triangle itself. In structural engineering the triangle is the only rigid polygon. Push on the corner of a square frame and it collapses into a rhombus — the angles give, the shape folds flat. Push on the corner of a triangle and nothing moves, because to change a triangle's shape you'd have to change the *length* of a side, and the sides are members under tension and compression, not hinges. This is the entire reason bridges, cranes, roof trusses, transmission towers, and geodesic domes are built from triangles and not squares. The triangle distributes load to its corners and refuses to deform. Squares need diagonal bracing to survive — and a diagonal brace is just a confession that you wanted a triangle all along.

So when I tell you to build automation in threes, I am not invoking the rule of comedy or the three acts of a screenplay, though those rhyme. I am telling you that three is the smallest count of things that produces a structure instead of a pile. Two oscillates. Four wobbles. Three holds load.

## Triangular routes are the most efficient loops

> *Wind dead on the bow—*
> *you cannot sail straight; you tack*
> *a triangle home.*

Here is the part that feels wrong until you've lived it: the most efficient route to a goal is often *not* the straight line at it.

A sailboat cannot sail directly into the wind. Point the bow at the thing you want when the thing you want is upwind, and you stop dead, sails luffing, going nowhere with great conviction. The efficient path to a point you cannot approach head-on is a triangle — you *tack*, sailing at an angle off the wind on one leg, then crossing to the opposite angle on the next, and the zigzag, which looks like a detour to anyone who's never held a tiller, gets you there when the straight line gets you nothing. The triangle isn't the scenic route. The triangle is the *only* route, and it is faster than the straight line that doesn't move.

Mathematicians have a name for the deep version of this: the **triangle inequality**. For any three points, the direct side is never longer than the sum of the other two — `d(A,C) ≤ d(A,B) + d(B,C)`. It sounds like a tautology and it is the foundation of every routing optimizer ever written. It's why a logistics planner reaches for a milk-run loop — depot to A to B to C and home — instead of driving out and back, out and back, out and back, three separate round trips from the depot. Each leg of the loop is never longer than the detour back through the depot would be, so the loop that touches three points in sequence beats the star that returns to center between each one. Triangulate the route and you stop paying for the trip home you take three times.

And the same geometry runs the wall you plugged this laptop into. The electrical grid does not deliver power as one wire doing its best. It delivers **three-phase power**: three alternating currents, each offset by 120 degrees — a third of a cycle — so that as one phase troughs, another peaks, and the sum delivers smooth, constant power with no dead spots. One phase pulses. Two phases still leave gaps. Three phases, spaced a third of a circle apart, hand the motor a continuous push and use less copper doing it. Every industrial motor on Earth runs on the discovery that three rotating things, evenly offset, never all rest at once.

That is what a good automation *loop* is. Not a line — a triangle of three nodes, each handing off to the next, the third feeding back to the first. You already know the shapes, because the disciplines that survived all converged on the same three-node loop and gave it different names:

- **Sense → Decide → Act**, then sense again. The control loop. The thermostat. The autopilot.
- **Red → Green → Refactor.** Test-driven development is a triangle: write the failing test, make it pass, clean it up, write the next failing test. Three states, forever.
- **Extract → Transform → Load.** The oldest data pipeline in the building, and it's three stages because three is where it stabilizes.
- **Build → Measure → Learn.** The whole of Lean, drawn as a loop with exactly three vertices.

Notice what each of these has that the straight pipe didn't: the third node points back at the first. `Act` changes the world that `Sense` reads. `Learn` rewrites what you `Build`. The triangle closes. That closure is the difference between a system that corrects itself and a sentence that runs to `null` at 6 a.m. and tells you it succeeded.

```bash
#!/usr/bin/env bash
# Not a pipe. A loop with three vertices and a way home.
while true; do
  state=$(sense)                  # read the world
  action=$(decide "$state")       # choose, given the reading
  apply "$action"                 # change the world
  sleep "$INTERVAL"               # ...and sense the world you just changed
done
```

Two nodes — sense and act, no decide — and you get a relay that slams on and off, oscillating, because nothing mediates. Four nodes and you've added a vertex that someone will eventually have to explain to a new hire, and which will be the one that's subtly out of phase. Three nodes hold load.

## Chunk the goal until it fits in one slice

> *Mind holds three at most—*
> *break the mountain into three*
> *stones you can lift now.*

A loop needs something to loop *over*, and this is where most automation dies a second, quieter death: the chunk is the wrong size.

Human working memory holds about three to four items at once — the number has shrunk in the literature since George Miller's famous ["seven, plus or minus two,"](https://psychclassics.yorku.ca/Miller/) and the honest modern figure is closer to four, often three under load. You do not overcome that ceiling by trying harder. You overcome it by *chunking*: grouping the raw material into a handful of units each small enough to hold whole. A phone number is ten digits you can't retain and three chunks you can. A goal is the same. "Migrate the platform" is a mountain you cannot lift and cannot even see the top of. "Stand up the new database, dual-write to both for a week, cut reads over" is three stones, and you can pick up the first one today.

Machines have the same constraint wearing different clothes. In [[work & play & dev &: job control for the sleep-deprived]], the lesson was that `dev` — the deep-work process — only makes progress in long uninterrupted blocks because it needs its whole working set resident and the cache hot; starve it of a contiguous slice and it produces nothing but guilt. Chunking is how you size work to the slice you can actually give it. Too big a chunk and the job can't fit in one focused block, so it never completes and never checkpoints — it just thrashes, paging your attention to disk. Too small a chunk and you drown in overhead: the cost isn't the work, it's the context switch between the pieces, and a thousand tiny pieces means a thousand switches, each taxed.

The right chunk is the one you can carry through the loop exactly once — sense it, decide on it, act on it — before you have to set it down. And the elegant part, the part that closes the loop back to the triangle, is that the best chunking is *also* in threes. Break the goal into three. Break each of those into three. You descend a tree where every node has three children, and a tree of depth three already has twenty-seven leaves — enough granularity to schedule real work, shallow enough that you can still see the root from the leaf. Divide and conquer is the oldest algorithm we have, and it does not divide into eleven. It halves, or it thirds, and the thirds tend to map better onto the way a goal actually has a beginning, a middle, and a done.

```bash
# A goal you can't hold:
deploy_the_whole_thing

# Chunked into a loop you can run, three at a time:
for stone in stand_up_db dual_write cut_over; do
  result=$(run_chunk "$stone") || { rollback "$stone"; break; }
  checkpoint "$stone" "$result"     # set it down before you pick up the next
done
```

Three stones. Each one small enough to lift, run through the loop once, and set down with a checkpoint — so that when `enrich` times out at 6 a.m., you lose one stone, not the morning.

## The haiku of trade

> *Five, seven, then five—*
> *the small fast core reads the work,*
> *routes it, steps aside.*

A haiku is three lines: five syllables, seven, five. It is the smallest poem that still completes a thought — short enough to hold whole in working memory, structured enough to have a shape, and built, of course, on three. The form survived a thousand years for the same reason the milking stool did: it is the minimum that holds. Every epigraph above this paragraph has been one, and you read each of them in a single slice without strain. That is not decoration. That is the chunk size of the human mind, set to verse.

There is a haiku of *trade*, too — the smallest complete transaction, the three-beat loop at the bottom of all commerce. A request comes in. A decision is made. A response goes out. Read the order, decide the fulfillment, ship the thing. Five-seven-five. Sense, decide, act. It is the same triangle wearing an apron, and for the whole history of business it had a human at the front of it: someone who read what came in, judged what it was, and routed it onward — the clerk, the dispatcher, the desk that triaged the morning's mail into piles.

That front seat is now an artificial intelligence (AI) core. And here is the actual news: it is not the *biggest* model that takes the front. It's the *smallest fast one*.

The pattern has a name in the trade now — the **router**, or the **cascade** — and the economics are the triangle inequality applied to compute. You do not send every request to the most powerful, most expensive model you own, any more than you'd drive a separate round trip from the depot for every single package. You put a small, fast, cheap model at the front — call it a [Haiku](https://docs.anthropic.com/en/docs/about-claude/models/overview), because that is precisely the role and, as it happens, the name of the model class built for it — and its whole job is the first beat of the loop: read the work, decide what it *is*, and route it. Most requests are simple, and the fast front-line core handles them whole and ships the answer in one slice. The genuinely hard ones — the cases where the triangle inequality says the detour through heavier compute actually pays — it escalates: hands them up to the heavyweight, the deep reasoner, or out to the human who's the right one of the three to lift this particular stone. The fast core reads the work, routes it, and steps aside.

```bash
# The haiku of trade, with an AI core at the front.
classify=$(haiku "triage: $request")   # the fast front-line read — line one
case "$classify" in
  simple)  haiku  "resolve: $request" ;;   # ...handles it whole, ships it
  hard)    opus   "resolve: $request" ;;   # ...escalates to the heavyweight
  human)   queue_for_human "$request" ;;   # ...or routes to the right person
esac
# Front core fronts. All else follows what it sends.
```

This is the inversion worth sitting with. The instinct is to put your most capable thing at the front of the operation — the senior engineer reads every ticket, the biggest model sees every prompt, the partner takes every call. It's backwards, and it's backwards for a reason you now have the geometry to see. The front of a loop is the *sensing* node, and sensing wants to be fast, cheap, and constant — three offset phases handing off a smooth signal, not one enormous pulse with dead spots between. You want the heavy capability held in reserve for the chunk that genuinely earns it, the way you hold `dev`'s deep block for the work that needs the whole cache hot. Put the fast core in front to triage and route, and the expensive capability stops being a bottleneck and becomes an escalation path. The Haiku takes the front. All else follows what it sends.

Which means the entire performance of the system now rides on a thing it never used to: the quality of the *routing*. When a small fast core sits at the front of the trade and everything downstream follows its read, a bad triage doesn't fail loudly — it succeeds, confidently, at the wrong thing, and runs your morning to `null` while reporting exit 0. The clerk who mis-sorts the mail mis-sorts it fast and at scale. So the discipline shifts from *doing the work* to *checking the front* — auditing what the router escalates and what it doesn't, watching the cases it waves through, keeping the human in the loop precisely at the vertex where the fast core decides who lifts the stone. The automation didn't remove the judgment. It moved it to the front and made it the only thing that matters.

## exit 0

> *Haiku takes the front;*
> *all else follows what it sends—*
> *earn what comes behind.*

You will keep wanting to build the straight line. It reads so cleanly left to right, and the shape of a sentence is the shape of how we think a task should go: this, then this, then this, then done. But a line has no way home. It cannot correct what it got wrong because nothing in its geometry points backward, and so the first dead stage runs the rest of it to `null` and tells you it worked.

Three is the magic number, and the magic is structural. So, three things to take with you — because of course there are three:

**Build the loop, not the line.** Three nodes, the third pointing back at the first. Sense, decide, act, and sense the world you just changed. The triangle is the only shape that holds load, and a loop that closes is the only automation that corrects itself.

**Chunk the goal until it fits in one slice.** Three stones, each small enough to carry through the loop once and set down with a checkpoint. The right chunk size is the one that survives an interruption without losing the morning. When in doubt, third it.

**Put the fast core at the front.** The haiku of trade now has an AI core reading the first line — small, fast, constant — routing most of the work whole and escalating only the chunk that earns the heavyweight or the human. That's the efficient shape. But the front is now the whole game: all else follows what it sends, so audit the read, watch what it waves through, and make sure what comes behind is worth the follow.

The trade has a new clerk at the front desk, and it works in fives and sevens and fives, sorting the morning's mail faster than any human ever could. For a Denver small or medium business (SMB), that is the difference between two analysts hand-triaging support tickets all morning and a small model routing most of them in seconds, freeing your people for the harder fraction that actually needs a human. That's not the end of your job. That's the start of a better one — minding the vertex where the fast core decides, because everything downstream is now following a haiku, and a haiku is only as good as its first line.

```bash
$ exit 0   # this time, on purpose.
```

---

*At BASH Consulting we build the automation that holds — loops that correct themselves, goals chunked to a size your team can actually carry, and AI cores placed where they make the system faster instead of where they make the demo flashier. If your pipeline is a straight line quietly running to `null` at 6 a.m., see how our [[Software development]] work puts the right shape — and the right model — at the front.*
