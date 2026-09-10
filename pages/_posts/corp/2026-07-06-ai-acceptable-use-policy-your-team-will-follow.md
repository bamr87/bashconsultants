---
title: "An AI acceptable-use policy your team will actually follow"
description: "An AI acceptable-use policy a 20-100-person business will follow: what to allow, what to ban, what to log, and a skeleton you can adapt in an afternoon"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-07-06T12:00:00.000Z
lastmod: 2026-09-07T12:00:00.000Z
draft: false
categories: [corp, ai]
tags: [ai-policy, acceptable-use, governance, shadow-it, denver-smb, compliance]
keywords: [ai acceptable use policy template, small business ai policy, employee chatgpt policy, ai governance smb, shadow ai risk, denver it consultant, hipaa ai policy, ai policy for law firms]
preview: /images/previews/an-ai-acceptable-use-policy-your-team-will-actuall.png
---

Your team is already using artificial intelligence (AI) at work. The only open question is whether they're using it under rules you wrote or rules they improvised. At most 20–100-person businesses we see, the honest answer is the second one — and the policy that fixes it doesn't need to be long. It needs to be followable.

## Why the policy you've been putting off matters now

When we inventory software at small and medium businesses (SMBs), we typically find somewhere between a handful and a dozen AI tools in active use that nobody approved — free chatbot accounts, browser extensions, note-takers quietly sitting in on client calls. Each one is a place where company or client information now lives outside your control.

That exposure lands differently by industry. For a Denver law or accounting firm, a paralegal pasting a client matter into a personal chatbot account may have just stretched a confidentiality duty past its limit. For a dental clinic, patient details in a consumer AI tool are a Health Insurance Portability and Accountability Act (HIPAA) problem whether or not anything bad happens next. And on many free consumer tiers, the vendor's terms allow your inputs to be used for model training — which means "just delete it" may not be an option later.

The instinct is to ban everything. That fails quickly: the staff who found these tools useful keep using them on personal devices, and now you carry the same exposure with zero visibility. The policy that works gives people a sanctioned way to do what they were already doing.

## The three lists: allow, ban, log

A workable SMB policy fits on one page and answers three questions.

**What's allowed without asking.** Drafting and editing internal documents and emails. Summarizing meeting notes and public information. Writing or reviewing code in company repositories. Brainstorming and research starting points. All of it on approved tools under company business accounts — business tiers generally offer admin controls and contract terms that exclude your data from training, which free tiers may not.

**What's banned without written approval.** Client-identifying or client-confidential information. Employee, payroll, or health records. Passwords, keys, and security configurations. Personal AI accounts for any company work. And the big one: sending AI output to a client, court, or regulator without a named human reviewing it first.

**What gets logged.** Which tools are approved and who holds the accounts. Who reviewed AI-assisted work before it left the building. And for material decisions — pricing, hiring, anything that touches the books — the tool, the prompt, the output, and the reviewer.

If you want a framework behind those choices, the National Institute of Standards and Technology (NIST) publishes the [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework), and that is the reference we use. In plain terms it asks for four things: govern (someone owns the policy), map (know where AI is actually used), measure (check the outputs), and manage (fix what the checks find). A one-page policy, a tool inventory, and a quarterly review cover all four at SMB scale.

## A skeleton you can copy

Adapt the brackets, delete what doesn't apply, and resist the urge to add legal boilerplate. A policy nobody reads is a policy nobody follows.

```text
AI acceptable-use policy — [Company name]
Effective [date] | Owner: [name, role] | Reviewed: quarterly

1. Approved tools
   - [Tool A] under the company business account only
   - [Tool B] under the company business account only
   - Anything else requires written approval from [owner/role]

2. Allowed without asking
   - Drafting and editing internal documents, emails, and marketing copy
   - Summarizing meeting notes and publicly available information
   - Writing or reviewing code in company repositories
   - Brainstorming, research starting points, and format conversion

3. Prohibited without written approval
   - Entering client-identifying or client-confidential information
   - Entering employee records, payroll data, or health information
   - Entering passwords, keys, or security configurations
   - Using personal AI accounts for any company work
   - Sending AI output to a client, court, or regulator without a
     named human reviewing and approving it first

4. Review and logging
   - AI-assisted work that leaves the company gets a human review;
     the reviewer is accountable for the content
   - [Owner/role] maintains the list of approved tools and accounts
   - Material decisions supported by AI (pricing, hiring, financial
     reporting) are logged: tool, prompt, output, reviewer, date

5. When in doubt
   - Ask [owner/role] before pasting. Asking is never a violation.
```

## How the rollout plays out

1. **Week 1 — inventory.** Ask, don't audit. A short survey ("what AI tools do you use, for what?") with amnesty attached gets honest answers. This list is the real scope of your policy.
2. **Week 2 — draft with the users.** Write the three lists with the two or three heaviest users in the room. They'll tell you which bans will be ignored and what approved alternative would make compliance the easy path.
3. **Week 3 — roll out.** Set up business accounts for the approved tools, walk the team through the one-pager in a single meeting, and name the owner people ask when unsure.
4. **Quarterly — review.** New tools appear, models change, and someone will request an exception. Fifteen minutes a quarter keeps the policy real.

For most firms this size, the whole cycle is 2–4 weeks of part-time effort, and most of it is conversation rather than paperwork. The wider version of the same work — inventory, guardrails, and where AI actually pays — is laid out in [[Adopting AI in your business without losing control]].

## Watch-outs

- **A ban without an alternative creates shadow use.** If the policy says no and offers nothing, usage doesn't stop — it goes underground, which is strictly worse.
- **A policy without logging can't be enforced.** If you can't say which tools are approved and who reviewed what, the document is decoration.
- **Legal language kills adoption.** Save the dense version for the employee handbook appendix if you must; the working copy is the one page people actually read.
- **Tools change faster than policies.** The approved-tools list should be a living attachment the owner can update without re-ratifying the whole document.

## Next step

The policy is the paper half; the working half is the tool inventory, the business-account setup, and the guardrails that make the rules stick. That's the first working session in [[AI solutions and intelligent automation]] — and it usually surfaces the riskiest paste before the policy is even final.
