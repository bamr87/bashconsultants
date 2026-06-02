# Change Log

All notable changes to the BASH Consultants repository will be documented in this file.

Check [Keep a Changelog](http://keepachangelog.com/) for recommendations on how to structure this file.

## [Unreleased]

### Added
- **BASH OS Phase 0 — AI engine & governance foundation:**
  - **`tools/bashos/`** — Node/TypeScript CLI (the AI engine). `bashos prompts` lists the prompt library, `bashos classify` reports the blast-radius autonomy verdict for the working tree, `bashos run <prompt> <file>` runs a prompt against a file with Claude (prompt-cached instruction context, opus/sonnet/haiku tiers). `run` never commits; committing is policy-gated.
  - **`tools/bashos/policy/blast-radius.yml`** + **`docs/ai-framework/AUTONOMY-POLICY.md`** — The semi-autonomous governance model: Green (auto-commit) / Yellow (open PR) / Red (human-only), most-restrictive-wins, draft condition, and a secret-pattern backstop.
  - **`tools/bashos/evals/validate-prompts.mjs`** + **`.github/workflows/ai-prompt-evals.yml`** — Dependency-free structural eval that validates every `.prompt.md`/`.instructions.md` against the canonical frontmatter schema and body-style rules; runs in CI to catch prompt drift.
  - **`CLAUDE.md`** — Symlink to `AGENTS.md` (single source of truth for agent guidance).
  - **`.claude/skills/`** — Claude-native skills (`content-article`, `content-review`) that thinly wrap the existing prompts without duplicating them.
- **`docs/ai-framework/PLAN.md`** + **`docs/ai-framework/README.md`** — Comprehensive plan for "BASH OS", an AI-augmented consulting operating system layered on the static site (Claude overlay on a deterministic git/Jekyll foundation). Covers the layered architecture, five capability modules (Content Studio, Idea Vault, Marketing Engine, Comms Hub, Site Ops), a semi-autonomous governance/blast-radius model, a reusable distribution model for other consultants, and a phased roadmap (Phase 1 = Content Studio).
- **`pages/_posts/muses/2025-01-24-bash-consulting-breaking.md`** — New satirical press-release post ("If a press release about ethical capitalism wrote itself") covering ESG accounting for Denver SMBs; includes a straight practical section on what's buildable on QuickBooks today.
- **`.github/prompts/article-write.prompt.md`** — New `/article-write` agent prompt for drafting new bashconsultants.com posts end-to-end.

### Changed
- **`pages/_posts/muses/2025-08-12-innovation-paradox.md`** — Frontmatter updated (author, description, keywords, lastmod, tags normalized); content rewritten for voice and SMB focus.
- **`pages/_posts/tech/2025-08-12-ai-integration-reality.md`** — Frontmatter updated; content rewritten with honest SMB-first framing on AI implementation.
- **`pages/_posts/tech/2025-11-19-prompts-are-the-new-command-line.md`** — Frontmatter normalized (author, lastmod, categories/tags as YAML lists); content already updated to SMB voice.

### Removed
- **`pages/_posts/tech/2025-01-24-bash-consulting-breaking.md`** — Deleted from `tech/`; replaced by the muses rewrite above.

---

### Added
- **`.github/instructions/`** — Six file-scoped instruction files for AI agents:
  - `content-style.instructions.md` (applyTo `pages/**`, `index.md`, `about.md`, `contact.md`) — shared editorial voice, audience profile (Denver SMBs 5–200 employees), target-industry table, banned phrases, SEO + accessibility rules
  - `posts.instructions.md` (applyTo `pages/_posts/**/*.md`) — blog post structure + subfolder routing (corp/erp/muses/tech)
  - `services.instructions.md` (applyTo `pages/_services/**/*.md`) — service-page conversion structure + industry-fit naming
  - `jekyll-theme.instructions.md` (applyTo theme override paths) — local override rules for the remote theme
  - `extension.instructions.md` (applyTo `extension/**`) — VS Code Prompt Orchestrator dev rules
  - `prompts.instructions.md` (applyTo `.github/{prompts,instructions}/**`) — schema + slash-hard body style
- **AGENTS.md** — Cross-tool entry point for AI coding agents (Copilot, Codex, Cursor, Aider, Claude Code). Points to canonical guidance.
- **`.github/prompts/commit-publish.prompt.md`** — Standard commit + push + deploy workflow for the direct-to-main publishing model.
- **Canonical frontmatter reference** — `.github/FRONTMATTER.md` documents the required schema for `.prompt.md` and `.instructions.md` files.

### Changed
- **`.github/copilot-instructions.md`** — Rewritten to reflect the actual dual-purpose repo (Jekyll site + `extension/` sub-project). Previous content described only the extension and was stale.
- **`.github/prompts/` frontmatter normalized** — All `.prompt.md` files updated to canonical `mode: agent` + `description` + `date` + `lastmod` schema. Body content already concise (≤100 lines per file); no further compression needed.

### Removed
- **`.github/prompts/docs.prompt.md`** — superseded by `documentation.prompt.md`.

## [1.4.0] - 2026-04-06

### Changed
- **Theme Upgrade**: Updated zer0-mistakes theme from v0.21.6 to v0.22.10
  - `Gemfile.azure`: Updated `jekyll-theme-zer0` from `~> 0.21.2` to `~> 0.22.10`
  - `pages/_about/site/_config.yml`: Updated `remote_theme` pin from `v0.21.6` to `v0.22.10`
  - `_data/README.md` and `_data/navigation/README.md`: Updated version references to v0.22+
  - Notable theme changes since v0.21.6:
    - Admin layout and configuration dashboards (v0.22.10)
    - Cross-platform installation compatibility fixes (v0.22.8)
    - Hero layout and scroll animation stabilization (v0.22.3)
    - Various documentation and CI improvements

## [1.3.0] - 2026-03-31

### Changed
- **Theme Upgrade**: Updated zer0-mistakes theme from v0.18.0 to v0.21.6
  - `Gemfile`: Updated `jekyll-theme-zer0` from `~> 0.18.0` to `~> 0.21.2` (latest on RubyGems)
  - `Gemfile.azure`: Added version pin `~> 0.21.2`
  - `_config.yml`: Pinned `remote_theme` to `bamr87/zer0-mistakes@v0.21.6`

- **Layout Standardization**: Aligned post and section layouts with theme v0.20.3+ conventions
  - Changed default post layout from `journals` to `article` in `_config.yml` defaults
  - Updated 9 posts with explicit `layout: journals` or `layout: blog` to `layout: article`
  - Updated 6 category/index pages to use `layout: default` (theme's `section` layout uses `/news/` URLs)
  - Renamed category pages with date prefixes for proper Jekyll `_posts` processing

- **New Features Enabled**:
  - Added `search.json` for GitHub Pages compatible search (theme v0.20.2 feature)
  - Added `mermaid` diagram configuration for client-side rendering
  - Added `jekyll-include-cache` plugin for improved build performance
  - Updated vendor exclusion paths to support `assets/vendor/` publishing

- **Configuration Updates**:
  - Updated Bootstrap version reference from 5.2.0 to 5.3.3 in `powered_by`
  - Updated version references in `_data/README.md` and `_data/navigation/README.md` to v0.21+
  - Synced `pages/_about/site/_config.yml` remote_theme pin and post layout default

### Fixed
- **404 Page**: Fixed broken `/blog` navigation link to use correct `/posts` path
- **Navigation**: Removed broken links to non-existent pages (`/docs/`, `/about/org/`, `/about/portfolio/`)
- **Navigation**: Fixed `/home/` links to `/` across navigation data files
- **Blog Index**: Fixed hardcoded post URLs using slug format to use date-based format
- **Category Pages**: Added missing `permalink` to muses category page

## [1.2.0] - 2026-01-24

### Changed
- **Development Port Standardization**: Updated all development ports from 4002 to 4042 for consistency
  - `Dockerfile`: Changed EXPOSE and CMD to use port 4042
  - `docker-compose.yml`: Updated port mapping to 4042:4042
  - `.vscode/tasks.json`: Updated Jekyll local serve port to 4042
  - `.vscode/launch.json`: Updated all debug configuration URLs to localhost:4042

- **VS Code Development Environment**: Complete overhaul of development configurations
  - `.vscode/launch.json`: Added 6 new debug configurations:
    - 🐳 Debug BASH Consultants (Docker) - Primary Docker debugging
    - 🔗 Attach to Running Jekyll (Docker) - Attach to running container
    - 🔄 Docker Rebuild & Debug - Force rebuild with debugging
    - 🖥️ Debug BASH Consultants (Local) - Local development debugging
    - 📱 Mobile Debug (Docker) - Mobile responsive testing
    - 🎯 Performance Debug (Docker) - Performance profiling
  - `.vscode/tasks.json`: Added 12 comprehensive tasks:
    - Docker operations (up, stop, down, rebuild, logs)
    - Jekyll serve/build (Docker and Local)
    - Maintenance tasks (clean up, update dependencies)

- **Theme Version**: Updated jekyll-theme-zer0 to v0.18.0
  - `Gemfile`: Updated gem version constraint to `~> 0.18.0`
  - `_config.yml`: Simplified remote_theme to `bamr87/zer0-mistakes` (uses latest)

- **Gemfile Cleanup**: Simplified dependencies
  - Removed redundant jekyll_plugins group (already included in github-pages gem)
  - Removed pinned versions for ffi and webrick (use latest compatible)
  - Removed commonmarker pin (resolved upstream)

### Added
- **`.gitignore`**: Added `logs/` directory for debug trace logs

### Fixed
- **Dockerfile**: Added newline at end of file

## [1.1.0] - 2026-01-24

### Changed
- **Navigation Data Structure** (`_data/navigation/`): Updated to zer0-mistakes theme v0.17+ format
  - Migrated from `sublinks` to `children` property for nested navigation items
  - Added Bootstrap Icons (`bi-*` prefix) to all navigation items
  - Added consistent Home links to sidebar navigation files
  - Added trailing slashes to all URLs for consistency

### Added
- **New Navigation Files** (`_data/navigation/`)
  - `home.yml` - Homepage quick navigation with icons
  - `services.yml` - Services sidebar navigation
  - `README.md` - Navigation schema documentation with migration guide

### Fixed
- Fixed HTML entity `&amp;` in about.yml to proper `&` character
- Fixed inconsistent URL trailing slashes across navigation files

## [1.0.0] - 2026-01-24

### Added
- **Prompt Orchestrator VS Code Extension** (`extension/`): New VS Code extension for orchestrating AI agent workflows using structured prompts
  - Discovers and loads prompt templates from `.github/prompts/` directory
  - Execute prompts via Command Palette or sidebar tree view
  - Integration with VS Code Chat API and Language Model API
  - Commands: refreshPrompts, executePrompt, review, refactor, test, docs, debug
  - Configuration settings for prompts directory and auto-refresh
  
- **Prompt Engineering Toolkit** (`.github/prompts/`)
  - `docs.prompt.md` - Technical documentation generation
  - Additional prompts for requirements analysis, system design, code implementation, test generation, code refactoring, and debugging

- **Automation Scripts** (`scripts/`)
  - `routine-maintenance.sh` - Prepare prompt workflows for VS Code Chat
  - `demo-docs-generation.js` - Demonstrate documentation prompt generation
  - `test-docs-prompt.js` - Standalone test script for prompt loading
  - `vscode-integration.sh` - VS Code CLI integration helper

- **Blog Posts** (`pages/_posts/`)
  - "Prompts: The New Command Line" - Exploring the paradigm shift in development
  - "From Prompts to Pipelines: Agentic Workflows in VS Code" - Extension design and agentic workflows

### Changed
- **Repository Structure**: Reorganized to separate Jekyll website from VS Code extension
  - Jekyll site configs remain at root level
  - Extension code moved to dedicated `extension/` directory
  - Updated `.gitignore` for new structure
  
- **VS Code Workspace Configuration** (`.vscode/`)
  - Updated `launch.json` for Jekyll-focused development
  - Updated `tasks.json` for Jekyll build tasks
  - Updated `settings.json` for Liquid/Jekyll file associations
  - Updated `extensions.json` with Jekyll-relevant recommendations

- **Root `package.json`**: Clean Jekyll-only build configuration for Azure Static Web Apps

- **README.md**: Added Tools and Resources section documenting prompt engineering toolkit

### Removed
- Extension files from root directory (moved to `extension/`)
  - `tsconfig.json`, `esbuild.js`, `eslint.config.mjs` (now in `extension/`)
  - `src/`, `out/`, `dist/` directories (now in `extension/`)
  - `.vscode-test.mjs`, `.vscodeignore`, `vsc-extension-quickstart.md`, `EXTENSION-README.md`