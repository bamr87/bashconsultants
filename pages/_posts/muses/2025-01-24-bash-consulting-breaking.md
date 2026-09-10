---
title: "If a press release about ethical capitalism wrote itself"
description: "A press release claims capitalism has been balanced on a napkin, then a straight answer on the sustainability tracking you can actually build in QuickBooks"
author: "Amr Abdel-Motaleb"
layout: article
date: 2025-01-24T10:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
featured: false
categories: [muses]
tags: [esg, accounting, sustainability, compliance, smb, quickbooks]
keywords: [esg accounting smb, esg reporting for small business, sec climate disclosure smb, california sb 253 sb 261, ghg protocol scope 1 2 3, quickbooks esg tracking, supplier esg questionnaire, denver smb sustainability reporting]
preview: /images/previews/if-a-press-release-about-ethical-capitalism-wrote-.png
---

## For immediate release

**[Somewhere on the Front Range]** — A mid-market consultancy announced today that it has, at long last, balanced the ledger of capitalism. Shareholder returns are up. Carbon is down. Karen in Accounts Payable has been freed from her nine-step invoice approval and is reportedly using the time to enjoy hobbies.

The firm's lead partner, speaking from a press conference held in a converted bike-share station, called the result "a double-entry miracle." Asked for the journal entry, he produced a napkin.

The mechanism, per the napkin: spend that used to leak out as overhead is now redirected, line by line, into the communities and ecosystems the business operates in. Renewable energy. Local workforce development. Cleaning up the polluted lot behind the warehouse the previous owner pretended he didn't know about. Every dollar traceable, every transaction auditable, every excuse for inaction *deletable.*

"We're amortizing the damage capitalism has done to the environment," the partner explained, "over a fifty-year useful life. While capitalizing on humanity's potential. It's GAAP-compliant. Mostly."

Industry response has been mixed. One CFO, reached by phone, said his quarterly numbers had never looked better and asked not to be named. A traditionalist in Houston accused the firm of "over-auditing reality." An executive at an unnamed oil company was overheard muttering that his capital expenditures were being quietly turned into community expenditures, "and they look the same on the cash flow statement, which is the worst part."

The firm declined to share its methodology, citing competitive concerns and the fact that it does not, strictly speaking, exist.

---

## The question under the napkin

The fantasy in that press release is the napkin — one journal entry that squares profit with planet, audited and done. The real question underneath it is more modest and far more useful: **how much sustainability tracking can a Denver small or medium business (SMB) actually build on the systems it already owns?**

Environmental, Social, and Governance (ESG) reporting sounds like something only public companies do. But the pressure has moved downstream. Banks ask about it on loan renewals. Insurers ask about it on commercial property and fleet policies. A large customer — a hospital system, a general contractor, a national retailer — increasingly bakes an ESG questionnaire into its request for proposal (RFP). If you supply, build for, or borrow from a bigger organization, the question is coming, even if the term never reaches your inbox.

Honest answer in 2026: you can build more than most owners assume, and far less than the ESG platform vendors will tell you. The trap is treating it as binary — buy the six-figure enterprise platform or do nothing. There's a middle path, and most of it runs on QuickBooks.

## Why it matters now

The regulatory floor is shifting under the whole topic, which is exactly why guessing is expensive. The U.S. Securities and Exchange Commission [adopted a climate-related disclosure rule for public companies in 2024](https://www.sec.gov/newsroom/press-releases/2024-31), then in 2025 [voted to end its defense of the rule](https://www.sec.gov/newsroom/press-releases/2025-58) — so federal mandates are in flux. Meanwhile [California's climate-disclosure laws (SB 253 and SB 261)](https://ww2.arb.ca.gov/our-work/programs/california-corporate-greenhouse-gas-reporting-and-climate-related-financial-risk) reach large private companies above revenue thresholds, and the supply-chain emissions those companies have to account for tend to arrive at their suppliers as contract language. The reporting framework most of these regimes lean on is the [Greenhouse Gas (GHG) Protocol](https://ghgprotocol.org/corporate-standard), which defines emissions in three scopes — your direct fuel burn (Scope 1), your purchased electricity (Scope 2), and everything up and down your supply chain (Scope 3).

You do not need to memorize that. You need to know that the people who finance, insure, and buy from you increasingly do — and that "we don't track any of that" is becoming an answer that costs money. A loan covenant, an insurance premium, a spot on a preferred-vendor list: these now occasionally hinge on whether you can produce a credible page of numbers.

## What we'd actually do

Three things are within reach on QuickBooks Online (QBO) or a typical mid-market Enterprise Resource Planning (ERP) system, with no platform purchase. We've set these up the same way for a Front Range distributor and a 30-person professional-services firm.

**1. Tag the chart of accounts.** Spend tied to energy, fuel, waste, business travel, and local sourcing becomes queryable when you attach a *class* or *location* dimension in QBO (or a department/segment in NetSuite or Acumatica). Once your diesel, your Xcel bill, and your hauler invoices each carry a tag, "what did we spend on energy last quarter" is a saved report, not a scavenger hunt. Budget the setup at a weekend in QBO, a short sprint in an ERP.

**2. Pull utility and fuel data in.** Xcel Energy, most fleet-card programs, and the major waste haulers expose monthly usage as a CSV download or an Application Programming Interface (API) feed. Land that usage data in a side table next to the general ledger — a spreadsheet tab or a small database — so kilowatt-hours and gallons sit alongside the dollars. Nobody should be keying meter readings by hand.

**3. Publish one page, every quarter.** Revenue, gross margin, and the three or four sustainability numbers a bank or large customer is most likely to ask for: total electricity use, fuel/fleet emissions, waste diverted, and — if it's relevant to your buyers — workforce or local-spend figures. Build it once in Power BI, Looker Studio, or a Google Sheet that one named person owns — the same path [[From spreadsheets to dashboards]] walks through. It does not need to be beautiful. It needs to be repeatable and dated.

## How it plays out

A realistic rollout for a 20-to-150-person business runs over a single quarter, in parallel with normal close:

- **Weeks 1–2 — scope and tag.** Decide which two or three metrics your stakeholders actually ask about (don't measure everything), then add the chart-of-accounts dimensions. Your controller or bookkeeper does most of this.
- **Weeks 3–5 — connect the feeds.** Wire up the utility, fleet, and waste data sources and reconcile one historical month against a paper bill so you trust the numbers.
- **Weeks 6–9 — build the page and write the method.** Stand up the quarterly report and document, in one plain paragraph per metric, where each number comes from and what it excludes. That methodology note is what turns a spreadsheet into something a lender or auditor will respect.
- **Ongoing — refresh at close.** The report updates as part of month-end and quarter-end. The whole point is that it stops being a project.

What your team has to bring: someone in finance who owns the numbers, and one decision-maker who can say "these are the metrics that matter to us" so the scope doesn't balloon.

## Watch-outs

- **Scope 3 is the cliff.** Audited supplier-level lifecycle emissions, Scope 3 across your supply chain, or anything resembling Corporate Sustainability Reporting Directive (CSRD)-grade disclosure is genuinely not buildable for a small business without real budget and outside assurance. If a vendor pitches you that for a few thousand dollars a year, the math is hiding somewhere — ask exactly which emissions factors and data sources they use, and watch them get vague.
- **Don't overstate what you measure.** Publishing a number you can't defend is worse than publishing none. Greenwashing claims invite the same scrutiny as a bad financial disclosure. Label estimates as estimates and state what's excluded.
- **Don't let the tool pick the metrics.** Buy a platform first and you'll spend the year feeding it data nobody asked for. Start from the questions your bank, insurer, and biggest customers actually put in writing, then build only those.

The honest version of that press release is unglamorous: tag the ledger, pull the feeds, publish one defensible page, and tell lenders and customers exactly what you do and don't measure. It's real, it's cheap relative to scrambling later, and it does not require a sorcerer.

## Where to go from here

The test is simple. In the last twelve months, has a lender, insurer, large customer, or RFP asked anything about emissions, diversity, or governance? If yes, building the basics quietly over a quarter costs a fraction of scrambling when the next one asks — and graduating to a real system later is far easier from a tagged, documented baseline than from scratch.

If that conversation is overdue, see how we approach [[Finance tech]].
