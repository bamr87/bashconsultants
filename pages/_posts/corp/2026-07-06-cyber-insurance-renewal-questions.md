---
title: "What your cyber insurance renewal will ask about this year"
description: "The security questions on this year's cyber insurance application, how each answer moves your premium, and a 30-minute self-audit for Denver SMBs"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-07-06T12:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [corp]
tags: [cyber-insurance, security, mfa, edr, backups, offboarding, denver-smb]
keywords: [cyber insurance renewal checklist, cyber insurance mfa requirement, edr requirement cyber insurance, small business cyber insurance premium, backup requirements cyber insurance, employee offboarding security, denver managed it services]
preview: /images/previews/what-your-cyber-insurance-renewal-will-ask-about-t.png
---

The cyber insurance renewal application that lands in your inbox this year is longer than the one you signed last year, and the difference isn't paperwork inflation. Carriers have learned exactly which missing controls turn a phishing email into a six-figure ransomware claim, and they now ask about each one directly.

## Why the application got serious

A few years ago, a small and medium business (SMB) cyber application was a page of yes/no questions. Today it's a multi-page attestation, and your answers do three jobs at once: they set your premium, they set your exclusions, and they become evidence if you ever file a claim. An answer you guessed at — "sure, we have multi-factor on everything" — can void coverage at the exact moment you need it, because carriers investigate the attestation after an incident, not before.

Four controls carry most of the weight: multi-factor authentication, endpoint detection, backups, and offboarding. They also track closely with the [Cyber Essentials guidance](https://www.cisa.gov/cyber-essentials) the U.S. Cybersecurity and Infrastructure Security Agency (CISA) publishes, which is a useful free reference whether or not an insurer is asking.

## The four questions that move the number

### Multi-factor authentication, everywhere that matters

Multi-factor authentication (MFA) means a second proof of identity beyond the password. The application will ask about it on email, on remote access, on administrator accounts, and increasingly on the backup console itself — because attackers who get in like to delete the backups first.

How it moves the number: for many carriers, "no" here isn't a surcharge, it's a declination or a ransomware exclusion. The good news is that MFA is usually the cheapest control on the list — on Microsoft 365 or Google Workspace it's configuration work, not new spending.

### Endpoint detection and response, not just antivirus

Endpoint detection and response (EDR) watches behavior on laptops and servers — a process encrypting files at 2 a.m., a login from nowhere — and can isolate a machine automatically. That's different from legacy antivirus, which checks files against a list of known bad ones. Applications now ask for the product by name and what percentage of devices it covers.

How it moves the number: weak answers here tend to show up less in the base premium and more in the fine print — higher retentions (your deductible) and lower ransomware sub-limits.

### Backups an attacker can't reach

The application asks three things: do you back up the systems that matter, is at least one copy offline or immutable (meaning the same attacker who encrypted your network can't encrypt it too), and have you actually tested a restore. A backup that lives on the same network with the same credentials as everything else counts as no. So does a backup that has never been restored — until it's tested, it's a hope, not a control.

How it moves the number: tested, separated backups shorten downtime, and downtime is most of what the insurer is pricing.

### Offboarding, the sleeper question

How quickly are accounts disabled when someone leaves? Are there shared logins? Do former employees or contractors still have live credentials to email, remote access, or the accounting system? Stale accounts are one of the cheapest ways into a network, and carriers know it. For a multi-location retailer or a construction firm with seasonal field staff, this question deserves more attention than it usually gets.

## What this does to your premium

Ranges, because that's what's honest: SMB cyber premiums commonly run from the low four figures to the low five figures per year depending on revenue, industry, and limits. The four controls above largely decide which market you shop in. A documented yes on all four puts you in the standard market with competitive quotes. A no — or a "partially," which carriers read as no — typically means some combination of higher retention, a ransomware sub-limit, an exclusion, or a push into surplus-market pricing that can run a multiple of standard. The premium is the visible cost; the exclusions are the expensive one.

## The 30-minute self-audit

Do this before the broker's deadline, not the night of.

- **Minutes 0–5:** Open your email admin console. Is MFA *enforced* for every user, or merely available? "Enabled but optional" is a no.
- **Minutes 5–10:** Pick three computers, including one field or remote laptop. Confirm the EDR agent is installed, running, and reporting to a console someone actually watches.
- **Minutes 10–15:** Find the most recent successful backup of the systems that would stop the business — accounting, job files, patient records. Note the date and where that copy lives.
- **Minutes 15–20:** Find the date of the last *tested* restore. If the answer is never, that's the answer.
- **Minutes 20–25:** List the last three people who left the company. Check whether their accounts are disabled in email, remote access, and the accounting system.
- **Minutes 25–30:** Write down every "partially" you just found. That list, in that order, is your pre-renewal to-do list.

## Watch-outs

- **Never guess yes.** An inaccurate attestation is grounds for a denied claim. If you're not sure, the application is telling you what to go verify.
- **"Mostly deployed" is a no.** Finish the rollout before you sign, not after.
- **Start 60–90 days out.** Remediation takes weeks, and a quote requested the day before renewal locks in whatever your answers are that day.
- **Treat the application as a free assessment.** It's a carrier-funded list of the controls that most often decide whether an incident is an inconvenience or a catastrophe. The remote-access half of the list overlaps heavily with [[Remote work three years later: what actually worked]].

## Next step

If the self-audit produced more "partially" than you'd like, closing exactly these four gaps — and producing the documentation that lets you answer the application honestly — is standard scope for [[Managed IT services]]. Bring the application; it makes a very good project plan.
