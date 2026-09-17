---
title: "The AI audit trail: log prompts like journal entries"
sub-title: "Who, what, when, source document, approval — the discipline your books already have, applied to the model"
description: "If AI touches your financial workflows, its actions need the same evidence a journal entry carries: who, what, when, source, and approval"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-07-06T12:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [erp, ai]
tags: [audit-trail, internal-controls, ai, financial-close, compliance, segregation-of-duties]
keywords: [ai audit trail financial systems, ai internal controls, logging ai in accounting, coso framework ai controls, audit evidence for ai tools, ai month-end close, segregation of duties ai, denver accounting systems consultant]
preview: /images/previews/the-ai-audit-trail-log-prompts-like-journal-entrie.png
---

No controller would post a journal entry with no date, no preparer, no source document, and no approval. Yet that's exactly what an unlogged artificial intelligence (AI) step in a financial workflow is — an action inside your accounting process that nobody signed for.

## Why this is a 2026 problem

AI is moving into the finance function at small and medium businesses (SMBs) through the side door: proposing general ledger (GL) codes for bank-feed transactions, drafting reconciliations, estimating accruals, writing collections emails. All useful. But finance has a century-old discipline for actions that touch the books — every journal entry carries who, what, when, a source document, and an approval — and AI actions in those same workflows carry none of that by default.

A vendor's chat history is not an audit trail. It lives on the vendor's retention schedule, in an account you may not control, in a format you can't hand to an auditor. Meanwhile, financial records are typically retained for around seven years. If an AI-proposed categorization flows into an entry your auditor questions in year three, "the conversation expired" is not a working answer.

The control frameworks don't carve out software, either. The Committee of Sponsoring Organizations of the Treadway Commission's [Internal Control — Integrated Framework](https://www.coso.org/guidance-on-ic) expects control activities and reliable information regardless of which actor performs a step. An AI proposing entries is a preparer. Preparers generate evidence.

## The five fields, mapped

Treat every AI touch of a financial workflow like a journal entry. The mapping is direct:

| Evidence on a journal entry | Equivalent for an AI action |
|---|---|
| Preparer | Staff member who ran it, plus the model and version used |
| Date | Timestamp of the run |
| Amounts and accounts | The output, verbatim — proposed codes, numbers, or draft text |
| Source document | The exact input snapshot: the bank-feed export, the invoice batch |
| Approval | Named reviewer, their decision, and the date |

If you can produce those five fields for any AI-assisted step, you have a control. If you can't, you have a very fast, very confident preparer working off the books.

## Practical logging patterns

- **Keep an AI register.** One row per AI-assisted action, five fields per row. For a small finance team, a structured spreadsheet in a permission-controlled folder is a legitimate starting point; an append-only log table is better. Reference the row ID in the journal entry memo field ("prepared with AI, ref 2026-041") so the trail runs in both directions — from the entry to the evidence and back.
- **Log at the workflow, not the chat.** Capture the step where output enters the books — the bank-feed import, the journal entry batch — rather than the whole conversation. And always pair the output with its input snapshot; a prompt without its data can't reproduce anything.
- **Match retention to the records.** If the entry lives seven years, its evidence lives seven years. Export the register and snapshots to storage you control, on your schedule, not the vendor's.
- **Separate the prompter from the approver.** The person who runs the prompt isn't the person who approves the posting — the same segregation of duties you already apply to manual entries, and the same gap a one-person override opens in [[ERP Survivor, episode 2: the great chart of accounts debate]]. In a one-person finance function, use the same compensating control you would anywhere else: the owner reviews an exception report on a set cadence.
- **Version the prompts.** A reusable categorization prompt is a control. Editing it mid-period is a control change: date it, note who approved it, and keep the prior version. Your auditor will care whether the logic changed between Q1 and Q3.

## What the auditor will actually ask

None of these questions are exotic — they're the standard questions asked about any preparer. The only new part is that the preparer is software.

- Show me every entry this period where AI was involved. (A register answers this in minutes; email archaeology takes weeks.)
- Who approved this output, and what did they compare it against?
- Can you reproduce this result — what data did the model see?
- What's the exception process when the output is wrong, and can you show me one that was caught?
- Did the prompt change during the period? Who approved the change?

Walking into fieldwork with a register that answers all five is the difference between AI reading as a well-controlled efficiency and AI reading as a scope expansion.

## How it plays out

For a typical SMB finance team, standing this up takes 2–4 weeks of part-time effort. Week one is scoping: list every place AI currently touches a financial workflow — the inventory is usually longer than the controller expects. Week two, define the register and the preparer/approver split for the highest-volume touchpoint, which is almost always bank-feed categorization. Weeks three and four, run it live, tune the exception process, and reconcile the register's scope with [[An AI acceptable-use policy your team will actually follow]] so both documents agree on what counts as touching the books.

## Watch-outs

- **Vendor chat history isn't your evidence.** Retention, export, and format are on the vendor's terms. Assume it's gone when you need it and log on your side.
- **Prompts without inputs are half a record.** If you didn't snapshot the data the model saw, you can't reproduce the output — and a control you can't demonstrate reads as a control you don't have.
- **Never give the model posting rights.** Outputs enter the books only through a human approval, and the register proves it. An AI that posts directly is an unreviewed preparer working at unlimited speed.
- **A partial register is worse than it looks.** An AI action outside the register is this decade's version of the side spreadsheet — invisible until it surfaces in fieldwork.

## Next step

This is the finance-literate side of AI adoption, and it's where a dual accounting-and-systems background earns its keep. If AI is already drafting entries somewhere in your close, see our [[Finance tech]] — accounting systems and controls that hold up under audit.
