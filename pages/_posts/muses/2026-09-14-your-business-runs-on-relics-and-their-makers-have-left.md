---
title: "Your business runs on relics, and their makers have left"
sub-title: "New solutions require ancient wisdom"
description: "Your legacy systems are artifacts of people who have retired, and the cloud, ERP, or AI project you want next depends on recovering what they knew"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-09-14T10:00:00.000Z
lastmod: 2026-09-14T22:30:00.000Z
draft: false
categories: [muses]
tags: [legacy-systems, strategy, systems-thinking, change-management, smb, denver-smb]
keywords: [legacy system modernization small business, knowledge transfer before retirement, key person risk it systems, legacy erp migration, cobol skills shortage, documenting legacy systems, technical debt small business, denver it consulting]
preview: /images/previews/your-business-runs-on-relics-and-their-makers-have.png
featured: false
excerpt: "An information system stops being technology the day it goes live and starts being an artifact — and the people who can read it are retiring."
---

## The oldest thing in the building

The oldest thing in your building is not the boiler, the founder's desk, or the fax machine nobody has unplugged. It is the numbering scheme in your chart of accounts. Somebody designed it — a controller, probably, in a year when the company had one location and no idea it would ever need a second — and it has quietly governed every invoice, every close, and every report since. That controller retired. The numbering scheme did not.

The claim underneath all of it: an information system stops being technology on the day it goes live, and starts being an artifact. Technology is the word for what is coming. Artifact is the word for what was made, by particular people, for particular reasons, and then left behind. The distinction matters because we manage the two differently. Technology gets a roadmap. Artifacts get an archaeologist — or, more often, they get nothing, until the day someone has to change one and discovers that nobody still on payroll can say why it is the way it is.

## Dig anywhere and you hit a decade

Every running system is a site with layers, and the layers are dated. A distributor on the Front Range that has been in business since the nineties is typically running something like this, from the bottom up:

- **The 1990s stratum.** The chart of accounts and the item master, designed by a person who has since retired, encoding decisions ("warehouse is segment three, always") that everyone obeys and nobody can explain.
- **The mid-2000s stratum.** Customizations to the Enterprise Resource Planning (ERP) system, written by a consultant whose firm no longer exists, in a language the vendor has since stopped teaching.
- **The 2010s stratum.** The workarounds: a pricing workbook with a macro in it, a nightly script that moves a file between two systems that were never meant to meet, a report that everyone trusts and nobody has rerun by hand since it was built.
- **The 2020s stratum.** A web front end, a cloud backup, a dashboard, and this year an artificial intelligence (AI) pilot pointed at all of it.

Each layer was rational in its own year. That is what makes the site hard to read: the code records what was done, and the reason went home with whoever did it. An archaeologist can tell you a wall was built; they have to infer why. Your information technology (IT) lead is in the same position with the nightly script that runs at 2 a.m. It runs at 2 a.m. because the tape backup used to finish at 1:30. The tape drive left the building a decade ago. The timing stayed, a ritual whose god has retired.

If that sounds like a small-business problem, it is worth knowing that the largest organizations on earth have the same problem at a larger scale. In July 2025 the Government Accountability Office (GAO) examined eleven critical federal systems and put them at [about 23 to 60 years old](https://www.gao.gov/products/gao-25-107795). Eight of the eleven still run on legacy languages such as Common Business-Oriented Language (COBOL) and assembly, "programming languages that have a dwindling number of people available with the skills needed to support them." In the spring of 2020, the governor of New Jersey stood at a pandemic briefing and asked for volunteers who could program in COBOL, because the state's unemployment system was more than forty years old and drowning in claims.

And when Voyager 1, launched in 1977, stopped sending readable data in late 2023, the National Aeronautics and Space Administration (NASA) noted that finding solutions to the probes' problems ["often entails consulting original, decades-old documents written by engineers who didn't anticipate the issues that are arising today"](https://science.nasa.gov/blogs/voyager/2023/12/12/engineers-working-to-resolve-issue-with-voyager-1-computer-2/). Engineers [fixed it the following spring by dividing the affected code into sections and storing them elsewhere in the computer's memory](https://www.jpl.nasa.gov/news/nasas-voyager-1-resumes-sending-engineering-updates-to-earth/), around a chip that had failed. The fix was new. The knowledge required to make it safely was older than most of the careers in the room.

Your business is not a space program. The mechanism is the same at every scale; the scale only changes who the elders are. At NASA the elders wrote the documents. At a forty-person machine shop, the elder is the controller who built the pricing workbook, the administrator who wrote the backup script, and the consultant from the Mfg/Pro days who still answers email, for now.

## The artifact survives, the understanding doesn't

A little more than two thousand years ago, someone in the Greek world built a bronze box of interlocking gears that modeled the heavens: it tracked the moon's phases and predicted eclipses, and the researchers who decoded it call it ["technically more complex than any known device for at least a millennium afterwards"](https://www.nature.com/articles/nature05357). It went down with a ship, spent two millennia on the seabed, and came up in 1901 as a corroded lump that took another century to read.

Notice what survived and what did not. The object survived. The understanding — how to design it, why those gear ratios, what the maker knew that let them build it at all — did not survive on land, where there was no shipwreck to blame. Nobody destroyed that knowledge. It lived in a few heads, was never written where the next person could find it, and went when they went.

That is the condition of most business systems. They are fully legible as objects and nearly illegible as intentions. The code runs; the *why* is gone. And there is a particular cruelty in the timing: a system works best right before the last person who understands it leaves, because that person has spent years tuning it. Retirement does not break the system. It breaks the ability to change the system, and change is precisely what the new project requires.

## Why the newest project needs the oldest knowledge

Look at what is actually on the roadmap of a small or medium business (SMB) this year: a move off an unsupported ERP version, a cloud migration, an integration between the shop floor and the ledger, an AI assistant that can answer questions about the company's own data. Every one of those is gated by the oldest knowledge in the company.

You cannot migrate what you cannot read. The ERP move needs someone who knows why the account string has fourteen segments and which nine are dead. The integration needs someone who knows that status code 7 means "shipped but disputed," a decision made in 2006 and recorded nowhere. The AI assistant is the sharpest case, because a model is a reader, and it inherits every undocumented convention in what it reads. It can see the table. It cannot know what the warehouse manager meant. Pointed at an undocumented system, an AI produces confident archaeology: fluent, plausible stories about what each layer means, unchecked against the one person who could check them. The output looks like understanding and is a guess with good grammar.

There is a second, more hopeful sense in which new solutions require ancient wisdom. The techniques underneath your systems are old because they are right, not because nobody got around to replacing them. Double-entry bookkeeping is the oldest business information system still in production; Luca Pacioli described it in print in 1494, and every ERP ever sold is that Venetian ledger with a login screen. The relational model that organizes nearly every database you own was set out in a [1970 paper by Edgar Codd](https://dl.acm.org/doi/10.1145/362384.362685); its author died in 2003 and its ideas have not aged a day. The habits that make cloud infrastructure manageable — small tools that do one thing, plain text, a script instead of a memory — were worked out on machines with less memory than your thermostat. The people are gone. The ideas hold.

So "old" is not the problem. "Unread" is. A modernization that discards the old *idea* along with the old *housing* rebuilds, at cloud prices, the mistakes the old idea already solved. The value of the retiree is not nostalgia. It is that they carry the reasons, and the reasons are what tell you which layers to keep.

## The Rosetta Stone is a reconciliation

Scholars could read Egyptian hieroglyphs only after the Rosetta Stone gave them the same decree in three scripts and two languages — a bilingual artifact that let a known language unlock an unknown one. Systems work has an exact equivalent, and it is less glamorous than a museum piece: the reconciliation.

A trial balance that ties out in both the old system and the new. An accounts receivable (AR) aging that matches to the penny across the cutover. An inventory valuation that agrees between the green screen and the browser. Each is the same decree carved in two scripts, and it is the only proof available that you understood the old system rather than merely copied it. A manufacturer that moved [[From Mfg/Pro to QAD Enterprise Edition without losing data]] rehearsed the migration with reconciliations back to the old system before anyone set a cutover date, and go-live was an anticlimax, which is the entire goal. A parallel run is a translation exercise. A migration without a defined reconciliation is a translation nobody checked.

The test works in reverse, too. If you cannot produce a bilingual artifact for a system — if there is no number the old and the new can both be asked for — you have not finished reading it, and the new system will carry the old one's misreadings forward under a fresh coat of paint.

## What to do before the next retirement party

Archaeology is a practice, not a mood, and the practical version fits a small business. Here are five moves, roughly in order; [[Reviving a legacy system without losing what it knows]] walks each one through in full, with the four questions to put to any vendor who proposes the work.

1. **Map the strata.** One page per system: its age, who built each layer, who can still read it, and what depends on it. The "who can still read it" column is your real risk register. Wherever the answer is one name, and that name is within a few years of retirement or a few months of boredom, that row is a project, whatever the roadmap says. For what the map looks like when it has six interfaces from four decades on it, see [Frankenstein's ERP](/news/erp/frankenstein-erp-legacy-fragmentation/).
2. **Interview the elders while they are still on payroll.** Two or three recorded afternoons with the person who built the thing. Ask for the *why*, not the *how*; the how is in the artifact. What would break if this ran an hour later? Which fields are lies? What did you decide not to build, and why? Write the answers in plain text and store them next to the system's configuration, under version control. This costs days and is irreplaceable the week after they leave. It is also a courtesy: it says their judgment mattered, which it did.
3. **Carve the bilingual artifact before you migrate.** For every system you intend to replace, define the reconciliation up front: which numbers must agree, to what tolerance, on which dates. Then run it in rehearsal, more than once, and treat the first clean tie-out as the real milestone.
4. **Keep the idea, replace the housing.** Interrogate each layer with one question: is this old because it is right, or old because nobody has looked? Double-entry, normalized data, and a nightly reconciliation are the first kind. The 2 a.m. timing and the fourteen-segment account string are the second. Modernize the second on purpose and carry the first forward on purpose; how to stand a new system beside an old one without a big-bang cutover, using application programming interfaces (APIs) and events, is the subject of [[Integration architecture: APIs, events, legacy]].
5. **Write for the archaeologist.** Everything you build this year is a future relic. Leave the *why* where the next reader will dig: a plain-text note beside the code, a changelog, acronyms expanded, decisions recorded with the alternatives you rejected. It is the discipline this practice runs itself on: [[The deterministic-first doctrine]] is a set of files, not a memory. The reason fits in one line — the next reader may be a new hire, a consultant, or a model, and all three can only read what was written down.

## Next step

The knowledge is still in the building. It is walking toward the parking lot one retirement at a time. If you have a system whose only reader is planning a farewell lunch, or a migration whose reconciliation nobody has defined yet, [tell us what is in the oldest layer](/contact/), and we'll help you map the strata and carve the bilingual artifact while the people who can check it are still answering email.
