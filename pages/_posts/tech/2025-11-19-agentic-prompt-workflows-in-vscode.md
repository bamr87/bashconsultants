---
title: "From prompts to pipelines: agentic AI in VS Code"
description: "Turn one-off AI prompts into repeatable, reviewable workflows inside VS Code so your small team ships features faster without losing control"
author: "Amr Abdel-Motaleb"
layout: article
date: 2025-11-19T09:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [tech, ai]
tags: [prompt-engineering, ai, vscode, agents, automation]
keywords: [agentic ai workflows, vs code ai extension, prompt files in git, ai code review process, repeatable ai development workflow, small business software development, denver ai consultant]
preview: /images/previews/from-prompts-to-pipelines-agentic-ai-in-vs-code.png
---

If your team already uses an artificial intelligence (AI) assistant to explain code or draft a function, you have seen the ceiling: every task starts from a blank chat box, and the quality depends on whoever happens to be typing that day. The next step is turning those one-off prompts into saved, repeatable workflows that run inside the editor your developers already live in.

A quick vocabulary check before we go further, because two terms get thrown around loosely. **Prompt engineering** is the practice of writing the instructions you give an AI model carefully enough that the output is consistent and trustworthy. **Agentic** means the AI doesn't just answer — it takes actions: reading files, editing them, running tests, opening a pull request. We covered the first idea in [[Prompts are the new command line]]. This post is about the second: what happens when you wire those prompts together into a pipeline.

## Why this matters now

For a small or medium business (SMB), the expensive part of software work has never been writing the code. It is the surrounding effort: turning a vague client request into requirements, sketching a design, writing tests, updating documentation, and keeping it all consistent across a team of two or three people. That overhead is exactly what drives a 40-person Denver firm to either over-pay a contractor or skip the project entirely.

A single AI chat shaves a little off each of those steps. An **agentic workflow** — a saved sequence of prompts that act on your real files — shaves off the handoffs between them, which is where most of the time and most of the errors actually hide. The payoff is not "the AI writes the code." It is that the same request produces the same quality of output whether your senior developer or your newest hire kicks it off.

## From single prompts to designed pipelines

Most AI-in-the-editor features today are still manual, one command at a time:

- Highlight code, ask "explain this"
- Type a comment, ask "generate this function"
- Open a chat panel, ask "refactor this for me"

Useful, but it is the equivalent of typing shell commands by hand instead of saving a script. An agentic workflow lets you define a sequence of prompts that each play a specific role, call specialized tools (git, linters, test runners), and run the same way every time. Prompt engineering stops being about finding the one perfect sentence and becomes about designing a small system of prompts that behaves like a programmable pipeline.

## A VS Code extension as the control surface

This is the idea behind our own internal extension, a prompt orchestrator built for VS Code. It treats prompts as real, versioned files — stored in a `.github/prompts/` folder alongside the code — instead of disposable chat messages. Practically, that means three things:

1. **Prompts become reusable commands.** The extension reads your prompt files and lists them in a sidebar, so "run the requirements analysis" is a click, not a paste.
2. **Each prompt is bound to a role and a tool set.** A requirements prompt reads notes and issue descriptions; a code prompt edits files in the workspace; a test prompt writes and runs tests; a docs prompt updates Markdown.
3. **Workflows chain those prompts together.** A short configuration file (written in YAML, a plain-text format) describes the order: analyze the request, design the approach, implement, test, document — each step feeding the next.

Because the prompts are codified and stored in git, your team's standards travel with the project. Every engagement follows the same path, and you can review and improve the prompts the way you would review any other piece of architecture.

## Worked example: a client note becomes a feature

Here is a concrete run. A client emails a rough note:

> "We need users to export their transaction history as a CSV file so finance can reconcile faster. It has to be secure and handle large datasets."

That CSV (comma-separated values) export is a small but real feature. The manual version means copying the note into your notes, deriving requirements by hand, sketching an interface, writing the endpoint, writing tests, and updating docs — five separate context switches. The workflow version looks like this:

1. Save the note as `notes/client-export-feature.md`.
2. Right-click the file and choose **Run Workflow: idea to production**.
3. The pipeline runs in order:
   - A requirements step turns the note into a structured spec
   - A design step proposes the interface, data flow, and security approach
   - An implementation step drafts or edits the code
   - A test step adds unit and integration tests and runs them
   - A documentation step updates the user and technical docs
4. You review each diff, run the tests, and adjust before anything is committed.

You stay in control at every step — nothing merges itself. The repetitive plumbing between steps is what gets automated.

## What this looks like for your team

A few realistic ways an in-house IT lead at an SMB would put this to work:

- **Onboarding.** A new hire runs the same workflows your senior developer wrote, so their first pull requests already match house style.
- **Consistency across clients.** A construction client and a dental clinic both get the same requirements-to-docs discipline, even on small jobs that never used to justify it.
- **Maintenance, not just new builds.** Scheduled workflows can flag refactoring candidates, check documentation against the current code, and draft release notes from recent commits — the housekeeping that gets skipped when everyone is busy.

The prompt library you build up over time becomes a genuine asset: a written-down playbook for how your team solves problems, which is exactly the kind of institutional knowledge small teams usually lose when someone leaves.

## Watch-outs

Three things go wrong in practice, and they are worth naming before you invest.

- **Review is not optional.** Agentic does not mean unattended. AI-generated code can be confidently wrong, and a pipeline that commits without a human reading the diff will ship bugs faster, not slower. Keep the review gate.
- **Data leaves your building.** Sending source files and client notes to a hosted model is a data-handling decision, not just a productivity one. For a healthcare or finance client, confirm where the model runs and what it retains. Microsoft documents the data and privacy boundaries for [GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/copilot-privacy-and-data) — read the equivalent for whatever model you choose before any regulated data touches it.
- **Prompts need maintenance.** A prompt that worked six months ago can drift as models change. Version them, test them on known inputs, and treat a bad prompt like a bug, not a mystery.

## The takeaway

The shift here is the same one the command line went through decades ago: from typing commands by hand, to saving them as scripts, to running those scripts on a schedule. Prompts are following that arc. The win for a small business is not flashy AI — it is repeatability. The same request produces the same quality of result, every developer follows the same path, and the knowledge lives in files you own rather than in one person's head.

## Next step

If you want to build workflows like these into your own stack — or just want a second opinion on where AI actually saves your team time versus where it adds risk — see our [[AI solutions and intelligent automation]] work.
