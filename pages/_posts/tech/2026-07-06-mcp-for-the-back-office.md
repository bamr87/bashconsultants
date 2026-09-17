---
title: "MCP for the back office"
sub-title: "A standard plug between the assistant your team uses and the systems your business runs on"
description: "Wire an AI assistant into your file share, ticket queue, and accounting exports with the Model Context Protocol, read-only first and every call logged"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-07-06T12:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [tech, ai]
tags: [mcp, ai, integration, automation, guardrails, back-office]
keywords: [model context protocol explained, mcp for small business, connect ai to file share, ai ticketing system integration, ai quickbooks export analysis, ai guardrails smb, denver ai consulting]
preview: /images/previews/mcp-for-the-back-office.png
---

The artificial intelligence (AI) assistant your team uses every day can't see the systems your business actually runs on. So people copy out of the ticketing system, paste into the chat window, copy the answer back out, and reformat it. Copy-paste has quietly become your integration layer — and it's slow, error-prone, and invisible to any audit.

## What MCP is, in plain English

The Model Context Protocol (MCP) is an open standard for connecting AI assistants to outside systems — file shares, databases, business applications. It was originally developed by Anthropic and is now openly published, with the [specification and documentation at modelcontextprotocol.io](https://modelcontextprotocol.io/).

The plainest way to think about it: before the Universal Serial Bus (USB), every device needed its own cable and its own port. MCP does for AI-to-system connections what USB did for peripherals — one standard plug instead of a custom cable per pairing.

There are two halves. The assistant side speaks the protocol. On the system side, a small adapter called an MCP server sits in front of each system and exposes a short menu of named operations — "search the policy folder," "look up ticket status," "read the AR export" — each with defined inputs and outputs. The assistant can only order off that menu. That constraint is the whole point.

## Why this matters for an SMB now

Until recently, wiring an assistant into your file share or ticketing system meant a custom integration — the kind of project that gets quoted in weeks of development time and never gets funded at small and medium business (SMB) scale. A standard changes the economics. Adapters are small and reusable, vendors increasingly ship their own, and the work shifts from building plumbing to deciding permissions — which is where an owner's attention belongs anyway. For the back-office wiring described below, that's typically days of configuration and guardrail design rather than a custom development project.

## What we'd wire up first

The value isn't in exotic new systems. It's in the ones you already run.

- **The policy and procedure folder.** A read-only MCP server over one specific file-share folder — employee handbook, safety procedures, standard operating documents. Staff ask "what's our paid-time-off carryover rule" and get the answer with the source document cited. Nothing is ever written back.
- **The ticketing queue.** The assistant reads tickets and drafts responses. An operations manager at a Denver construction firm asks "what's still open on the Anderson job and who's waiting on us" and gets a grounded summary instead of twenty minutes of clicking. Creating or closing tickets still goes through a person.
- **Accounting exports, not accounting.** Point the assistant at the read-only exports your bookkeeper already pulls — the accounts receivable (AR) aging, the job-cost report — rather than at the ledger itself. It can summarize, flag anomalies, and draft the collections email. It cannot touch the books.

## The deterministic foundation

Here's the framing that keeps these projects safe. A language model is probabilistic: the same question can produce two different answers. Your general ledger, your job-costing system, and your ticket queue are deterministic: the same query returns the same record every time. Good architecture keeps the facts in the deterministic systems and the judgment in the model — the same split we lay out in [[The deterministic-first doctrine]].

MCP enforces that split at the connector. Each tool the server exposes is a defined operation against a system of record — the assistant decides which tool to call and how to phrase the answer, but the number comes from the export and the ticket status comes from the queue. The model can't invent an operation you didn't expose. When a wrong answer would cost money, the thing that prevents it is a permission, not a clever prompt. This is the same trust discipline we laid out in [[Prompts are the new command line]], pushed down into the plumbing.

## Guardrails that make it safe to plug in

- **Read-only first.** Every connection starts as read-only. Write access is a separate, later decision made per operation.
- **Least-privilege service accounts.** The MCP server connects with its own account scoped to exactly the folders and records it serves — never an administrator login.
- **Approval gates on anything that writes.** Draft the ticket reply, propose the categorization — a person commits it.
- **Log every call.** Who asked, which tool ran, with what parameters, and what came back — retained as long as you retain the records it touched. When AI reaches financial workflows, that log needs the same discipline as your books: [[The AI audit trail: log prompts like journal entries]].
- **Treat documents as untrusted input.** A file in the share can contain text that tries to instruct the assistant — the reason gated writes and scoped permissions matter even for "just documents."

## How it plays out

1. **Phase 1 — read-only pilot (2–4 weeks).** One system, usually the document folder. Includes the permissions review and the service-account setup. Your team's job: name the folder, own the access decisions, and check the log weekly.
2. **Phase 2 — drafting workflows (2–4 weeks).** Ticket replies, collections emails, report summaries — assistant drafts, named humans approve.
3. **Phase 3 — narrow writes, if earned.** Only for operations where the log and the approval record from phase 2 proved out, and often never for anything that moves money.

## Watch-outs

- **Vendor MCP servers aren't automatically safe.** Review the tool list an adapter exposes before connecting it, and disable operations you don't need. "Official" doesn't mean "scoped for you."
- **Over-broad access defeats the design.** A service account with admin rights turns a small mistake into a large one. The boring permissions work is the project.
- **Don't start with the ledger.** Start where wrong answers are cheap (documents) and move toward where they're expensive (money) slowly — or not at all.
- **The demo-to-production gap.** A connector that works in a ten-minute demo still needs the account scoping, logging, and approval design. Budget for that part; it's most of the value.

## Next step

If there's a copy-paste ritual in your back office that an assistant with two or three tightly scoped connections would end, that's a well-bounded first project. See how we scope this kind of work in [[AI solutions and intelligent automation]].
