---
title: "ERP Survivor, episode 2: the great chart of accounts debate"
description: "How a chart of accounts debate teaches Denver controllers to design a general ledger that survives an audit, not just a spreadsheet"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-09-03T12:00:00.000Z
lastmod: 2026-09-03T12:00:00.000Z
draft: false
categories: [erp]
tags: [erp-implementation, change-management, chart-of-accounts, segregation-of-duties, denver-smb]
preview: /images/previews/erp-survivor-episode-2-the-great-chart-of-accounts.png
excerpt: "The Alliance of the Spreadsheet People wanted the new system to keep every project code they'd ever created. Episode 2, where the chart of accounts becomes the season's real battlefield."
---

<!-- TODO: add preview image at /images/previews/erp-survivor-episode-2-the-great-chart-of-accounts.png (1200x630) -->

## Previously on ERP Survivor

*Dramatic music. A single spreadsheet tab, still open, glowing in an otherwise dark office.*

**Narrator**: "Last season, the Alliance of the Spreadsheet People formed to resist the new system. The consultants recruited them instead of fighting them. Requirements gathering is done. Now the tribes face the challenge that ends more Enterprise Resource Planning (ERP) projects than any go-live disaster: designing the chart of accounts (COA), the numbered list of every account the general ledger (GL) will ever use."

If you are the controller who has to sign off on that list, this is the episode for you. The lessons are in the commercial breaks, same as always.

## Why this challenge matters now

A chart of accounts looks like plumbing — dull, structural, easy to defer. It is actually the single decision that determines whether your month-end close is fast or painful for the next decade. A bloated COA, with a separate account for every project, customer, or department, turns every financial report into a scavenger hunt and every new hire into a six-month COA archaeologist. A COA that is too thin loses the detail management actually needs.

For a Denver light-manufacturing or distribution shop, this shows up as a very specific pain: finance wants to slice profit by project, operations wants to slice it by product line, and everyone's instinct is "add more accounts." Do that enough times and a chart designed for 200 accounts balloons to 2,000, nobody remembers what half of them are for, and closing the books means reconciling accounts nobody has posted to in three years.

## The immunity challenge: design the chart of accounts

**Host**: "Today's challenge: each tribe proposes a chart of accounts structure. The tribe whose structure survives contact with an actual audit wins immunity."

### Finance tribe's opening bid

**Linda**: "We need one account per project. We track 47 active projects. That's 47 new accounts, times however many expense categories, times two for this year and next."

**Sarah** *(already building the account-numbering spreadsheet)*: "So somewhere around six hundred new posting accounts, conservatively."

**Dave**: "And we keep the old chart too. Just in case."

> **Commercial break — the lesson:** This is the classic mistake, and it comes from a real need: Linda's team needs to report profit by project. The wrong fix is a GL account per project. The right fix is a **dimension** — a tag you attach to a transaction (project, department, location) that lets you slice reports without multiplying the chart itself. Microsoft's own guidance on [designing a chart of accounts for Dynamics 365 Business Central](https://learn.microsoft.com/en-us/dynamics365/business-central/finance-chart-of-accounts) puts it plainly: "start simple with fewer G/L accounts" and "use dimensions to simplify your chart of accounts — don't have specific G/L accounts for each product or department." One clean expense account with a project dimension answers Linda's question and every other cut she will ever ask for, including the ones she has not thought of yet.

### Operations tribe counters

**Bob**: "We don't need 47 project accounts. We need our own inventory adjustment account, our own scrap account, and a way to fix mistakes without waiting for anyone's approval."

**Carol**: "What do you mean, 'waiting for approval'? Bob just posts the correction himself. He's been doing it since the Reagan administration."

**Mike**: "It's called the emergency override procedure. Bob has the login. Bob makes the fix. Bob moves on."

**Bob** *(proudly)*: "Twenty minutes, start to finish. No meetings."

> **Commercial break — the lesson:** Bob's "emergency override" is a segregation-of-duties gap, not a shortcut — the same person who identifies an error, approves the correction, and posts it, with nobody else reviewing it. It survives in a legacy system because nobody's looked in years. It will not survive a lender's or insurer's first real audit, and it is exactly the kind of finding that turns a clean review into a management-letter comment. The fix is not to accuse Bob of anything; his corrections are probably right. The fix is a second set of eyes: a same-day review queue, or a threshold above which someone else approves before the entry posts. That takes Bob from twenty minutes to maybe forty-five, and it takes segregation of duties from "trust Bob" to "provable."

### IT tribe tries to referee

**Jennifer**: "What if we just gave both tribes everything they asked for? More accounts, more overrides, more flexibility."

**Tom** *(flipping through his binder)*: "The methodology recommends a standard chart of accounts with minimal customization, but it also has a whole appendix on flexibility, so—"

**Alex**: "I could build a report that hides the accounts nobody uses. Problem solved."

> **Commercial break — the lesson:** "Give everyone what they asked for" is not a design decision, it is the absence of one, and it is how a 200-account chart becomes a 2,000-account chart within eighteen months. Someone has to own the chart of accounts as a single artifact — usually the controller, with the implementation partner as a sounding board — and say no to additions that a dimension, a report filter, or a saved view can handle instead.

## The plot twist: the guest judge draws two lists

**Guest Judge**: "Every account request goes on one of two lists today. List one: things that change the actual financial structure of the business — a new legal entity, a new revenue stream, a new tax jurisdiction. Those get new accounts. List two: things you want to slice, filter, or report on — a project, a customer, a sales rep, a department. Those get dimensions."

**Linda** *(reading the lists)*: "...my 47 projects are all on list two."

**Guest Judge**: "Every one. You'll get project-level profitability without a single new account."

**Bob** *(quieter now)*: "And the override procedure?"

**Guest Judge**: "Stays, with one change: a second approver on anything over a threshold you set. You keep the speed. The business gets the proof."

> **Commercial break — the lesson:** Most chart-of-accounts fights are really reporting fights wearing a structural costume. Separating "this changes what the business is" from "this changes how I want to view what the business already does" resolves the majority of them before a single account number gets assigned.

## How a real chart of accounts design plays out

1. **Inventory the current chart and every report built on it (1-2 weeks).** Include the accounts nobody remembers the purpose of — those are usually the first to retire.
2. **Adopt a standard structure, then customize only where a real business rule demands it (1-2 weeks).** Most mid-market ERP platforms ship a sensible default chart for your industry; start there instead of rebuilding from scratch.
3. **Map every "I need to slice by X" request to a dimension, not an account (1-2 weeks).** Project, department, location, and sales channel almost always belong here.
4. **Design the control matrix alongside the chart, not after go-live (1-2 weeks).** Decide who can post, who approves exceptions, and at what dollar threshold — including Bob's overrides.
5. **Pilot the close with the new chart for one full cycle before retiring the old one.** A chart that looks right on paper still has to survive an actual month-end.

## Watch-outs that eliminate contestants

- **Account-per-project sprawl.** If a request can be answered with a dimension, it is not a new account. Every exception you allow becomes the precedent for the next one.
- **Unreviewed override authority.** Anyone who can identify, approve, and post a correction alone is a finding waiting for an auditor to notice it. Fix the workflow before it fixes your quarter.
- **A chart designed by committee with no owner.** Someone has to have the authority to say no to a new account. Without that, the chart grows until nobody trusts it.

## Next step

Redesigning your chart of accounts as part of a bigger system change? See our [[ERP consulting]], including the financial and control design work that keeps Linda's reporting and Bob's speed both intact.

<a href="/contact/" class="btn btn-primary btn-lg px-4">Book a free consultation</a>

---

*Based on patterns observed across dozens of ERP implementations. The characters are fictional. The chart of accounts disputes are not. No project codes were harmed in the making of this episode — 46 of them were, mercifully, retired in favor of a dimension.*

*Next episode: "User acceptance testing tribal council," where Mike discovers what thirty years of undocumented data actually converts into, and the alliance faces its first vote.*
