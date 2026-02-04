---
name: review-publish
description: Review open article changes, validate quality, and publish to GitHub Pages
argument-hint: Optional specific article path or 'all' to review all changed articles
draft: draft
---

# BASH Consultants: Article Review & Publish Workflow

Execute the complete review and publication pipeline for articles in the BASH Consultants Jekyll site. This workflow handles content validation, quality assurance, SEO optimization, and deployment to GitHub Pages.

## Task Overview

Review all open changes to articles (new or modified), apply BASH Consulting's content standards, validate technical accuracy, ensure SEO compliance, and publish to GitHub Pages via git commit and push.

---

## Step 1: Discover Open Changes

1. **Identify Changed Articles**:
   ```bash
   # Check git status for modified/new articles
   git status
   
   # View detailed changes for articles
   git diff pages/_posts/
   git diff --cached pages/_posts/
   
   # List new untracked articles
   git ls-files --others --exclude-standard pages/_posts/
   ```

2. **Categorize Changes**:
   - **New Articles**: Untracked files in `pages/_posts/`
   - **Updated Articles**: Modified tracked files
   - **Draft Articles**: Files with `draft: true` in front matter (skip for publication)

3. **Summarize Findings**:
   ```markdown
   ## Articles to Review
   
   ### New Articles
   - [ ] `2026-01-31-article-title.md` - Brief description
   
   ### Updated Articles
   - [ ] `2025-11-19-existing-article.md` - What changed
   
   ### Drafts (Not Publishing)
   - [ ] `draft-article.md` - Reason for draft status
   ```

---

## Step 2: Front Matter Validation

For each article, validate the YAML front matter against BASH Consulting standards.

### Required Fields

| Field | Requirements | Example |
|-------|--------------|---------|
| `title` | Clear, compelling, < 60 chars for SEO | `"The ERP Independence Playbook"` |
| `description` | SEO-optimized, 150-160 chars | Technical blueprint for eliminating... |
| `date` | ISO 8601 format | `2026-01-31T05:47:55.305Z` |
| `author` | Author name or `BASH Consulting` | `BASH Consulting` |
| `layout` | Must be `posts` | `posts` |
| `categories` | Array, primary category first | `[Technology, Business Strategy]` |
| `tags` | Array, 5-10 relevant tags | `[ERP, AI-development, manufacturing]` |
| `permalink` | Custom URL path | `/posts/erp-independence-abstraction-ai/` |
| `draft` | Boolean (false for publish) | `false` |

### Recommended Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `preview` | Social media preview text | What if your next ERP migration... |
| `excerpt` | Article summary for listings | ERP vendor lock-in isn't inevitable... |
| `snippet` | Short tagline | The real question isn't which ERP... |
| `sub-title` | Secondary headline | A Technical Blueprint for... |
| `keywords.primary` | Main SEO keywords (array) | `[ERP vendor independence, ...]` |
| `keywords.secondary` | Supporting keywords (array) | `[API-first ERP integration, ...]` |
| `lastmod` | Last modification date | `2026-01-31T06:21:05.084Z` |
| `slug` | URL-friendly identifier | `erp-independence-abstraction-ai` |
| `fmContentType` | Content type marker | `posts` |

### Validation Checklist

```markdown
## Front Matter Report: `article-filename.md`

### Required Fields
- [ ] `title`: ✅ Present, SEO-friendly
- [ ] `description`: ✅ Present, 150-160 chars
- [ ] `date`: ✅ Valid ISO 8601
- [ ] `author`: ✅ Present
- [ ] `layout`: ✅ Set to `posts`
- [ ] `categories`: ✅ Array with valid categories
- [ ] `tags`: ✅ Array with relevant tags
- [ ] `permalink`: ✅ Custom URL set
- [ ] `draft`: ✅ Set to `false` for publishing

### Recommended Fields
- [ ] `preview`: ⚠️ Missing - suggest adding
- [ ] `keywords`: ⚠️ Missing - suggest adding for SEO

### Issues Found
- **Critical**: None
- **Warnings**: Missing `preview` field
- **Suggestions**: Add `keywords.primary` for better SEO
```

---

## Step 3: Content Quality Review

### BASH Consulting Voice & Tone

Apply the BASH brand voice to all content:

- **Pragmatic, not ideological** — Focus on practical business outcomes
- **SMB-focused** — Acknowledge resource constraints; show achievable solutions
- **Confident expertise** — Speak from experience, not theory
- **Subtle vendor skepticism** — Question vendor narratives constructively
- **Actionable** — Every section should give readers something they can do

### Content Structure Validation

```markdown
## Content Review: `article-filename.md`

### Structure
- [ ] **Executive Summary**: Present and compelling
- [ ] **Clear H2/H3 hierarchy**: Logical heading structure
- [ ] **Code blocks**: Properly formatted with language tags
- [ ] **Tables**: Used appropriately for comparisons
- [ ] **Call to Action**: BASH contact info included
- [ ] **Conclusion**: Strong closing with next steps

### Quality Metrics
- [ ] **Depth**: Sections are substantive, not superficial
- [ ] **Clarity**: Technical jargon explained when used
- [ ] **Accuracy**: Technical claims are correct
- [ ] **Completeness**: All promised content delivered
- [ ] **Tone**: Matches BASH professional voice

### SEO Optimization
- [ ] **Primary keyword** in title: ✅
- [ ] **Primary keyword** in first paragraph: ✅
- [ ] **Internal links**: Links to other BASH content
- [ ] **External links**: Authoritative references included
- [ ] **Image alt text**: All images have descriptive alt text
```

### Content Enhancement Checklist

For articles that need improvement:

1. **Thin Sections**: Identify paragraphs < 3 sentences and expand
2. **Missing Examples**: Add real-world applications or code samples
3. **Jargon**: Add brief explanations for technical terms
4. **Flow**: Ensure logical transitions between sections
5. **CTA**: Verify BASH contact information is present

---

## Step 4: Apply BASH ERP Independence Framework (If Applicable)

For ERP-related content, ensure alignment with BASH's Three Pillars:

### Pillar Integration Check

- [ ] **Business Logic Abstraction**: Article addresses extracting unique processes from vendor-specific implementations
- [ ] **Canonical Data Layer**: Mentions vendor-neutral data models and organization data ownership
- [ ] **Headless UI / Custom Platform**: Discusses decoupling user experience from ERP backend

### Messaging Alignment

- [ ] Frames ERP lock-in as a **design choice**, not inevitability
- [ ] Emphasizes **AI acceleration** for development timelines
- [ ] Includes **financial analysis** (TCO comparisons, leverage gains)
- [ ] Provides **actionable roadmaps** (phased implementation)

---

## Step 5: Build and Test Locally

1. **Start Jekyll Server**:
   ```bash
   # With Docker (recommended)
   docker-compose up
   
   # Or locally
   bundle exec jekyll serve --config "_config.yml,_config_dev.yml" --port 4002
   ```

2. **Verify Build Success**:
   ```bash
   # Check for build errors
   docker-compose exec jekyll bundle exec jekyll build
   
   # Or locally
   bundle exec jekyll build
   ```

3. **Visual Review**:
   - Navigate to `http://localhost:4002/posts/[article-slug]/`
   - Verify rendering, images, code blocks, tables
   - Check mobile responsiveness
   - Validate internal/external links

4. **Test Checklist**:
   ```markdown
   ## Build Verification: `article-filename.md`
   
   - [ ] Jekyll build: SUCCESS
   - [ ] Article renders correctly
   - [ ] Images load properly
   - [ ] Code blocks syntax highlighted
   - [ ] Tables display correctly
   - [ ] Links functional
   - [ ] Mobile responsive
   ```

---

## Step 6: Commit and Publish

### Prepare Commit

1. **Stage Article Changes**:
   ```bash
   # Stage specific articles
   git add pages/_posts/2026-01-31-article-title.md
   
   # Or stage all post changes
   git add pages/_posts/
   
   # Stage any related assets
   git add assets/images/posts/
   ```

2. **Review Staged Changes**:
   ```bash
   git diff --cached --stat
   ```

### Commit Message Format

Use semantic commit messages following BASH conventions:

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types for Articles**:
- `content`: New article or major content addition
- `update`: Article update or revision
- `fix`: Typo/error correction
- `docs`: Documentation or README changes

**Example Commits**:

```bash
# New article
git commit -m "content(posts): add ERP Independence Playbook white paper

Comprehensive guide to eliminating ERP vendor lock-in through:
- Business logic abstraction patterns
- Canonical data layer architecture  
- Headless UI development with AI acceleration

Keywords: ERP independence, vendor lock-in, AI-enabled development"

# Article update
git commit -m "update(posts): enhance Frankenstein ERP satire with staffing analysis

Added new sections:
- IT staffing requirements for legacy ERP support
- Vendor irony analysis
- Expanded conclusion with three strategic options"

# Multiple articles
git commit -m "content(posts): publish January 2026 ERP article series

New articles:
- ERP Independence Playbook (white paper)
- Frankenstein's ERP (satire)

Both articles support BASH's vendor independence messaging."
```

### Push to GitHub

```bash
# Push to main branch
git push origin main
```

### Verify Deployment

1. **GitHub Actions**: Check for successful build at `https://github.com/amr-bash/bashconsultants/actions`
2. **Live Site**: Verify article appears at `https://bashconsultants.com/posts/[article-slug]/`

---

## Step 7: Post-Publication Checklist

### Verification

```markdown
## Publication Verification

**Date**: YYYY-MM-DD
**Articles Published**:

### Article 1: `title`
- [ ] Live URL: https://bashconsultants.com/posts/slug/
- [ ] Renders correctly in production
- [ ] Social preview (og:image) displays properly
- [ ] Listed in posts index
- [ ] Internal links functional

### Article 2: `title`
- [ ] Live URL: https://bashconsultants.com/posts/slug/
- [ ] Renders correctly in production
- [ ] etc.

### Overall
- [ ] No 404 errors on site
- [ ] Build succeeded in GitHub Actions
- [ ] CNAME still configured correctly
```

### Update CHANGELOG (If Applicable)

```markdown
## [Unreleased]

### Added
- **New Post: `ERP Independence Playbook`** - White paper on vendor-agnostic architecture
- **New Post: `Frankenstein's ERP`** - Satirical take on legacy ERP fragmentation

### Changed
- Updated front matter standards for improved SEO
```

---

## Output Format

Provide a comprehensive summary after completing the workflow:

```markdown
# Article Review & Publish Summary

**Date**: YYYY-MM-DD
**Reviewer**: AI Agent

## Articles Reviewed

### ✅ Published
| Article | Status | URL |
|---------|--------|-----|
| ERP Independence Playbook | Published | /posts/erp-independence-abstraction-ai/ |
| Frankenstein's ERP | Published | /posts/frankenstein-erp-legacy-fragmentation-satire/ |

### ⏸️ Drafts (Not Published)
| Article | Reason |
|---------|--------|
| draft-article.md | `draft: true` in front matter |

### ❌ Issues Found
| Article | Issue | Resolution |
|---------|-------|------------|
| None | — | — |

## Quality Metrics

- **Front Matter Compliance**: 100%
- **Content Quality Score**: 95%
- **SEO Optimization**: 90%
- **BASH Voice Alignment**: 95%

## Commit Details

- **Hash**: `abc1234`
- **Message**: `content(posts): publish January 2026 ERP article series`
- **Files Changed**: 2 articles, 1 image

## Deployment Status

- **GitHub Actions**: ✅ Build successful
- **Live Site**: ✅ Articles accessible
- **SSL/HTTPS**: ✅ Secure

## Next Steps

- [ ] Share articles on LinkedIn
- [ ] Schedule social media posts
- [ ] Monitor analytics for engagement
```

---

## Quick Reference Commands

```bash
# Discovery
git status
git diff pages/_posts/

# Local testing
docker-compose up
# OR: bundle exec jekyll serve --port 4002

# Staging
git add pages/_posts/
git add assets/images/posts/

# Commit
git commit -m "content(posts): <description>"

# Publish
git push origin main

# Verify
# Check: https://github.com/amr-bash/bashconsultants/actions
# Live:  https://bashconsultants.com/posts/
```

---

## Related Prompts

- **article-review.prompt.md** — Detailed content editing and SEO optimization
- **bashing-erps.prompt.md** — Transform content with BASH's ERP independence philosophy

---

**Note**: Always review articles for alignment with BASH Consulting's brand positioning as the authority on ERP independence through abstraction and AI-enabled platform development. Contact: info@bashconsultants.com | bashconsultants.com | Denver, Colorado
