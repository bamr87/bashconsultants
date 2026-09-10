---
title: "Your best programmer thinks they're just good at Excel"
sub-title: "The load-bearing workbook, the person who maintains it, and the day it outgrows the grid"
description: "The spreadsheet your month-end close runs on is software, and the person who built it is a programmer — treat both like the systems they are"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-08-15T09:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [muses]
tags: [smb, legacy-systems, software-development, accounting, strategy, productivity]
keywords: [spreadsheet risk small business, excel to database migration, when to replace excel with a database, power query sql skills, business intelligence for smb, month-end close spreadsheet errors, key person risk finance]
preview: /images/previews/your-best-programmer-thinks-they-re-just-good-at-e.png
featured: false
excerpt: "The most fluent programmer in your company may have never opened a terminal — they maintain a workbook with eleven tabs and a formula your quarter depends on."
---

Somewhere in your company there is a workbook. It has eleven tabs, one of which is named `Sheet1 (final)(v3)(USE THIS ONE)`, and a formula in cell `M14` that the entire month-end close depends on. The person who maintains it does not call themselves a programmer. They call themselves someone who is good at Excel.

They are wrong about the first part. Advanced spreadsheet work is programming with the syntax filed off — not "like" programming, not "a stepping stone toward" programming, but the thing itself, done in a cell instead of a code file. And once you accept that, two conclusions follow that most small and medium businesses (SMBs) haven't acted on: you employ a programmer you aren't using as one, and you run production software you aren't managing as software.

## The formula bar doesn't lie

Open a formula written by someone who actually lives in Excel — not the `=A1+A2` crowd, but the person who builds the pricing model or the commission calc. You'll find something like this:

```text
=IFERROR(INDEX(Rates,MATCH(1,(Region=$B5)*(Tier=$C5),0)),"check inputs")
```

Ignore the spreadsheet costume and read what's happening. There's a lookup against a named range. There's a compound condition — region *and* tier both have to match — built by multiplying two arrays of true/false values, because the author worked out that `TRUE * TRUE = 1` and constructed an AND out of arithmetic. And there's error handling: when the lookup fails, it doesn't spit out a cryptic `#N/A`, it returns a message a human can act on.

Written in Structured Query Language (SQL), the language your accounting system's database already speaks, the same logic is a two-condition `WHERE` clause. Written in Python, it's a five-line function. The logic, the data structures, and the defensive habits are identical — only the vocabulary and the job title change.

## What "good at Excel" actually is

Strip the branding off the things your best Excel person does every day and the list reads like a junior developer's job description:

- **Nested `IF`, `INDEX/MATCH`, `SUMPRODUCT`** — conditional logic and lookups. Control flow and data structures, expressed in a grid.
- **Visual Basic for Applications (VBA) macros** — scripts, outright: loops, conditionals, and event-driven triggers.
- **Pivot tables and Power Query** — `GROUP BY`, `JOIN`, and `WHERE` wearing a drag-and-drop interface. Someone who builds a pivot off three source tables already understands relational data; they're missing the word "SQL," not the concept.
- **Named ranges, input validation, a tab per scenario** — data modeling and separation of concerns. Rough, usually. So is most code.

These aren't skills *adjacent* to programming. They're the same skills, learned in the one environment that ships on every corporate laptop and never asks anyone to install anything.

## The part that should worry you

Here's where this stops being a compliment and becomes a line item on your risk register.

If the argument above is right, then the model your quarter runs on is production software — and you are maintaining it with no version history, no testing, no review, and exactly one person who understands it. A formula buried in `M14` can't be code-reviewed. It silently changes meaning the day someone inserts a column. There is no audit trail for a workbook on a shared drive; there is only "who touched the model," asked in an accusatory tone during close week.

Calling it "just a spreadsheet" doesn't make the risk smaller. It only makes the risk invisible. The exposure comes in three familiar flavors: key-person risk (the author resigns and takes the only working mental map with them), silent-error risk (a broken formula that still produces a number), and audit risk (a material figure whose lineage nobody can reconstruct). None of these shows up on a budget until the week it costs you the close.

## Where the grid runs out

The honest version of this argument also names the walls, because Excel's limits are published, not mysterious. A worksheet tops out at 1,048,576 rows — [Microsoft's own specifications page](https://support.microsoft.com/en-us/office/excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3) lists the ceilings — and a model gets miserable long before that, when every recalculation takes a coffee break. Repeatability fails next: a workbook can't be meaningfully tested or diffed. Integration fails last: Excel can be bullied into calling an application programming interface (API) or scheduling a nightly job, but at that point someone is writing a program inside a spreadsheet to avoid admitting they should write a program.

None of those walls proves your Excel person isn't a programmer. The opposite: the person who looks at a wheezing 400,000-row workbook and says "this wants to be a database" has just made a senior engineering judgment. They only need someone to confirm they were right and hand them the tools — usually a small reporting database and a business intelligence (BI) layer like Power BI, which is the route [[From spreadsheets to dashboards]] walks through step by step.

## What to do with this

Three moves, in order of urgency:

1. **Inventory the load-bearing workbooks.** Ask one question of your finance and operations leads: "Which spreadsheets, if their author left tomorrow, would hurt the close?" That list is your shadow software portfolio. In the shops we walk into it usually runs three to six files.
2. **Treat the top of the list like software.** A second person who can maintain each model. Input validation on the cells humans touch. Dated, versioned copies instead of `(final)(v3)`. A one-page note on what the model assumes. This costs days, not months, and removes the scariest single point of failure in your reporting.
3. **Graduate the ones past the wall.** The models that are too big, too shared, or too integration-hungry belong in a small database with a BI front end — and your Excel person belongs at the front of that project, because they already own the logic. Teach them SQL first; it lands in weeks, not years, because pivot tables were SQL all along.

The most fluent programmer in your office may be the one who never opened a terminal. Check the formula bar before you decide who's technical — and if you'd like a second set of eyes on your shadow software portfolio, [tell us what's in cell M14](/contact/).
