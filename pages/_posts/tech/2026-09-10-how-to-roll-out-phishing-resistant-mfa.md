---
title: "How to roll out phishing-resistant MFA"
description: "A phased plan for moving Microsoft 365 and Google Workspace logins from push-based MFA to phishing-resistant passkeys and security keys"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-09-10T12:00:00.000Z
lastmod: 2026-09-10T12:00:00.000Z
draft: false
categories: [tech]
tags: [mfa, phishing, security, identity, smb]
keywords: [phishing-resistant mfa, mfa push bombing, passkeys for business, fido2 security key rollout, mfa fatigue attack, number matching mfa, denver it consulting, microsoft 365 mfa]
preview: /images/previews/how-to-roll-out-phishing-resistant-mfa.png
---

<!-- TODO: add preview image at /images/previews/how-to-roll-out-phishing-resistant-mfa.png (1200×630) -->

Your team enabled multi-factor authentication (MFA) last year, checked the box on the cyber-insurance form, and moved on. Then an employee's phone lit up with twenty login approval prompts at 11 p.m. — not because anyone was trying to log in from home, but because an attacker already had the password and was betting someone would tap "approve" just to make the notifications stop.

## Why it matters now

That attack has a name — push bombing, or MFA fatigue — and it works often enough that it's now a standard step in commodity phishing kits, not a nation-state trick. A second, quieter attack does the same thing without the noise: an adversary-in-the-middle phishing page that proxies your real login page in real time, captures the password, and relays the MFA code the instant the victim types it. Both attacks beat the exact control we told everyone to "just turn on" in [[The security baseline every small business needs]]. Push notifications and one-time codes are real MFA and still stop plain password-stuffing, but they no longer count as the finish line — carriers and the U.S. Cybersecurity and Infrastructure Security Agency (CISA) now distinguish basic MFA from [phishing-resistant MFA](https://www.cisa.gov/resources-tools/resources/multi-factor-authentication-mfa), which uses cryptographic keys that a fake login page cannot relay.

## What we'd actually do

Phishing-resistant MFA means the second factor is a hardware security key or a device-bound passkey built on the FIDO2/WebAuthn standard, instead of a code or a tap. The credential is tied to the real website's domain, so it simply doesn't work on a look-alike phishing page — there's nothing for the attacker to steal or relay. Both Microsoft 365 (via Conditional Access authentication strengths) and Google Workspace (via 2-Step Verification security keys and passkeys) support this today, on hardware most staff already carry — a laptop's built-in fingerprint reader or a $25–$50 Universal Serial Bus (USB) security key.

The honest scope: this is a configuration and change-management project, not a development project. For a business without on-premises legacy applications, expect days of admin work plus a few weeks of staff rollout, not months.

## How it plays out

1. **Audit current methods (week 1).** Pull the MFA method report from your Microsoft 365 or Google Workspace admin console. You're looking for how many users are still on SMS or voice-call codes — both are phishable and increasingly unreliable against SIM-swap fraud — versus app-based push.
2. **Protect the accounts that matter most first (weeks 1–2).** Enroll finance staff, anyone with administrator rights, and owners with a hardware security key or platform passkey. These are the accounts a targeted attacker goes after by name, so they move first regardless of company size.
3. **Turn on number matching everywhere else (week 2).** For staff not yet on a security key, enable number matching on push approvals — the app shows a number the user must type back, which kills the "just tap approve" version of push bombing even before hardware keys arrive.
4. **Extend security keys or passkeys to everyone (weeks 3–6).** Roll out by department. A professional-services firm can usually do this in one sitting per team; a construction company with field crews sharing tablets needs a slower pass and a clear policy on who owns which key.
5. **Retire SMS and voice codes (after rollout).** Once adoption is confirmed, disable phone-based MFA as a fallback option, not just as a default — a fallback an attacker can still request is a fallback that still gets used.

## Watch-outs

- **Lost keys need a real process, not a shrug.** Decide in advance how a lost security key gets revoked and replaced same-day, with a second, backed-up key or passkey as the recovery path — never a phone call to the help desk as the only fallback.
- **Shared and field devices break the "one passkey per person" model.** Construction and light-manufacturing shops with shared shop-floor terminals should default those accounts to hardware security keys staff carry with them, not device-bound passkeys tied to a machine nobody owns.
- **Legacy line-of-business software is often the real blocker.** An on-premises application that only accepts a password, or a VPN client that hasn't been updated in years, can't enforce modern MFA at all — that gap usually needs a compensating control or a [[Managed IT services]] engagement to close properly, not a policy memo.

## Next step

If your MFA rollout stalled at "enabled" and you're not sure which accounts are still one convincing phishing page away from a breach, an audit of your current authentication methods is a same-week engagement under [[Managed IT services]].
