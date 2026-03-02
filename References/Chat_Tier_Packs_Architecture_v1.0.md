# Chat Tier Packs Architecture for AI_CONTEXT (Implementation + Usage Spec)

**Revision:** 1.0\
**Generated:** 2026-03-02 13:38\
**Audience:** Claude (implementation), Alex (operator)\
**Scope:** Extend existing AI_CONTEXT system to generate
ChatGPT/Chat-app-focused tier packs for fast, repeatable context
mounting across Project threads.

------------------------------------------------------------------------

## 1. Purpose

Alex has an existing `AI_CONTEXT` system (SOURCES + ROLES + generator +
verifier) that works extremely well in VS Code/Claude workflows. The
goal of this spec is to adapt that system to the ChatGPT "Project +
Threads" environment, where:

-   Chat threads do **not** share conversation history,
-   Project files **do** persist across threads,
-   Manual copy/paste and repeated re-uploading is painful,
-   Token budgets must be controlled aggressively,
-   The assistant must be forced into deterministic behavior quickly.

**Solution:** Generate a small set of precompiled **Chat Tier Packs**
(`CHAT_T0_BOOT.md`, `CHAT_T1_CORE.md`, etc.) and store them as Project
files. Each new thread mounts the needed tier(s) by referencing these
packs.

------------------------------------------------------------------------

## 2. Mental Model

### 2.1 VS Code (Claude) vs Chat App (ChatGPT)

**VS Code workflow** - Repo is mounted - File tree is visible and
navigable - Context can be assembled on demand - The assistant can
"live" inside the repo

**ChatGPT workflow** - Each thread is isolated (no shared chat
history) - A Project can store shared files (persistent) - Best practice
is to upload authoritative packs once, then reference them

So the chat environment needs **"one-file mounts"** that can be invoked
with one sentence.

------------------------------------------------------------------------

## 3. Target Outputs

The system must generate the following files (and only these files are
expected for normal chat use):

-   `CHAT_INDEX.md` (1 page)
-   `CHAT_T0_BOOT.md` (tiny: hard constraints + operating protocol)
-   `CHAT_T1_CORE.md` (small: stable architecture + glossary)
-   `CHAT_T2_BUILD.md` (medium: contracts + implementation-oriented
    spec)
-   `CHAT_T3_DEEP.md` (large: full authoritative corpus for deep work)

These should be placed into ChatGPT Project files so any new thread can
reference them without re-uploading everything.

------------------------------------------------------------------------

## 4. Design Principles

1.  **Tier-first**: Tiers matter more than roles in a chat app.
2.  **Minimize tokens**: Start small; expand only when requested.
3.  **Deterministic behavior**: Packs must include explicit "don't
    assume" constraints.
4.  **Stable invariants**: Boot pack lists non-negotiables and
    eliminates drift.
5.  **Fast mount**: A new thread should align in \<10 seconds.
6.  **Portable**: Works across projects and can be copied between repos.
7.  **Compatible with existing AI_CONTEXT**: Don't rewrite; extend.

------------------------------------------------------------------------

## 5. Repository Structure Changes

### 5.1 Add New Generated Output Folder

Add one folder (choose one; preference below):

Option A (preferred): - `AI_CONTEXT/GENERATED_CHAT/`

Option B: - `AI_CONTEXT/CHAT/`

Rationale: The existing system likely already has
`AI_CONTEXT/GENERATED/`. Keeping chat packs as generated artifacts
maintains the same workflow pattern.

**Expected generated artifacts** -
`AI_CONTEXT/GENERATED_CHAT/CHAT_INDEX.md` -
`AI_CONTEXT/GENERATED_CHAT/CHAT_T0_BOOT.md` -
`AI_CONTEXT/GENERATED_CHAT/CHAT_T1_CORE.md` -
`AI_CONTEXT/GENERATED_CHAT/CHAT_T2_BUILD.md` -
`AI_CONTEXT/GENERATED_CHAT/CHAT_T3_DEEP.md`

------------------------------------------------------------------------

## 6. Source Documents (SOURCES) to Support Chat Packs

Alex already maintains a `SOURCES/` library (vision, runbook, dashboard
design, etc.). For chat packs to be low-friction and highly reliable,
add three chat-specific sources:

### 6.1 `SOURCES/chat_operating_protocol.md`

Must include: - "How to work with Alex in ChatGPT" - "When to output
downloadable markdown" - "How to start a new thread using tier packs" -
"How to handle ambiguity: ask short clarifying questions, then
proceed" - "Heavy thread warning rule" (if applicable)

### 6.2 `SOURCES/current_state.md`

Must include: - What is installed vs not installed - Current phase -
Known pain points / blockers - Next 3 actions - Any active experiments

### 6.3 `SOURCES/decisions_log.md`

Must include: - Bullet list of locked decisions with dates - Any
non-negotiables (FOSS, AirPods pairing constraint, HA authoritative,
etc.) - Rejected options (so the assistant doesn't re-suggest them)

These three sources reduce \~90% of chat drift and repeated explanation.

------------------------------------------------------------------------

## 7. Tier Pack Definitions

### 7.1 Tier Objectives and Constraints

#### `CHAT_T0_BOOT.md` (bootloader)

Purpose: **Instant alignment** + "guardrails."\
Target size: **100--300 lines** max.

Must include: - One-paragraph project summary - Non-negotiables (FOSS,
HA authoritative, AirPods via iPhone, Llama scope, Claude does code) -
Hardware constraints (Mac M1 8GB) - Chat operating protocol (short) -
"Do not assume outside these packs" warning - How to request deeper
tiers

#### `CHAT_T1_CORE.md` (default mount)

Purpose: Stable architecture.\
Target size: **1--3 pages**.

Must include: - Executive summary - Layered architecture overview (HA vs
LLM vs voice) - Glossary/terminology - "What exists / what does not
exist" - Links/pointers to deeper packs

#### `CHAT_T2_BUILD.md` (build mode)

Purpose: Implementation-facing specification.\
Target size: **5--15 pages**.

Must include: - Explicit interface contracts (schemas, confirmation
protocol) - Tool broker responsibilities - Error handling + logging -
Resource governance rules (8GB constraints) - Acceptance criteria style
guidance (what "done" means)

#### `CHAT_T3_DEEP.md` (deep work)

Purpose: Full corpus for deep analysis.\
Target size: Large but bounded.

Includes: - Full vision document - Runbook - Dashboard design - Personas
and use cases - Automation catalog - Device inventory - Threat model (if
present)

------------------------------------------------------------------------

## 8. YAML Configuration (ROLES vs TIERS)

### 8.1 Key Requirement

Tiers are not just roles. In chat, tier selection is the primary control
mechanism.

### 8.2 Implementation Options

**Option A (recommended): Add a TIER config file** - Add
`AI_CONTEXT/TIERS/chat_tiers.yml` - This file defines each tier, its
token budget target, and the source files to include.

Example concept: - `t0_boot`: shared + decisions_log +
chat_operating_protocol + current_state (trimmed) - `t1_core`: t0 +
architecture + glossary sections - `t2_build`: t1 + contracts + runbook
excerpts - `t3_deep`: full sources list

**Option B: Encode tiers as "roles"** - Create `ROLES/chat_t0.yml`,
`ROLES/chat_t1.yml`, etc. - Simple to implement but semantically
confusing (tiers ≠ roles)

**Recommendation:** Option A. Keep ROLES for personas, and TIERS for
packaging.

------------------------------------------------------------------------

## 9. Generator Changes (Implementation Spec)

The existing `generate_context_pack.py` concatenates documents based on
ROLES.

Add a new mode:

-   CLI flag: `--chat`
-   Or env var: `AI_CONTEXT_MODE=chat`

### 9.1 Generation Steps (Chat Mode)

1.  Load tier definitions (`AI_CONTEXT/TIERS/chat_tiers.yml`)
2.  For each tier:
    -   Resolve file list (relative paths)
    -   Concatenate in deterministic order
    -   Insert tier header with metadata (generated time, version,
        sources list)
    -   Enforce soft token budget targets (warn if exceeded)
3.  Write outputs into `AI_CONTEXT/GENERATED_CHAT/`

### 9.2 Deterministic Order

Ordering must be stable. Recommend order:

1.  Header + "how to use this pack"
2.  Non-negotiables / invariants
3.  Current state
4.  Architecture
5.  Contracts
6.  Deep sources

### 9.3 Token Budget Enforcement

Use approximate token counting (existing system) but add tier targets:

-   T0: \~500--1500 tokens
-   T1: \~1500--4000 tokens
-   T2: \~4000--12000 tokens
-   T3: allowed large, but still emit warnings

If any tier exceeds target by \>25%: print warning and list top
contributing source files.

------------------------------------------------------------------------

## 10. Verification Changes

Extend `verify_context_pack.py` to validate chat packs:

-   Validate `AI_CONTEXT/GENERATED_CHAT/` exists
-   Validate required pack filenames exist
-   Validate staleness (same STALENESS_DAYS policy)
-   Optional: ensure pack metadata header exists

If missing, return non-zero exit code to fail CI checks.

------------------------------------------------------------------------

## 11. How to Use Tier Packs in ChatGPT Projects

### 11.1 Upload Once

Upload the generated pack files to the ChatGPT Project (sidebar):

-   `CHAT_INDEX.md`
-   `CHAT_T0_BOOT.md`
-   `CHAT_T1_CORE.md`
-   `CHAT_T2_BUILD.md`
-   `CHAT_T3_DEEP.md`

Optional: keep the "full SOURCES.zip" in Project files too, but the
packs should be the default entry point.

### 11.2 New Thread Startup Ritual (Bridge v2)

In a new thread, Alex types:

> Use `CHAT_T0_BOOT` and `CHAT_T1_CORE` as authoritative. We are working
> on Phase X. Don't assume anything outside these packs.

Assistant must respond with: - Confirmed invariants - Restated phase
objective - Ask 1--2 short clarifying questions if needed - Proceed

### 11.3 Escalation Pattern

When deeper context is needed:

-   "Mount CHAT_T2_BUILD" → implementation detail mode
-   "Mount CHAT_T3_DEEP" → deep analysis mode

The assistant should not automatically mount deeper tiers unless asked
(avoid token blowups).

------------------------------------------------------------------------

## 12. Relationship to Old ALCON-D Thread Bridge

Bridge v1 relied on a ritual phrase and integrity manifest.

With tier packs:

-   The "restore" action becomes: mount `CHAT_T0_BOOT` + `CHAT_T1_CORE`
-   Integrity hashing is optional (still can be used for paranoia /
    reproducibility)
-   The mental model becomes: "Project file binder + tiered mounts"

If integrity is desired, extend the generator to output a
`CHAT_PACK_MANIFEST.json` with SHA-256 hashes for each pack.

------------------------------------------------------------------------

## 13. Acceptance Criteria

This feature is complete when:

1.  Running generator in chat mode produces all 5 files.
2.  Verifier confirms packs exist and are fresh.
3.  In ChatGPT, a brand-new thread can align using only `CHAT_T0_BOOT` +
    `CHAT_T1_CORE`.
4.  The assistant stops re-asking already-decided constraints (FOSS,
    AirPods, HA authoritative, etc.).
5.  Token usage is controlled: most threads run on T0/T1 only.
6.  Escalating to T2/T3 is explicit and intentional.

------------------------------------------------------------------------

## 14. Implementation Notes for Claude

-   Keep code changes minimal: add "chat mode" without breaking existing
    roles mode.
-   Prefer data-driven tier definition (YAML) over hardcoding.
-   Preserve deterministic ordering.
-   Emit warnings (not failures) for token budget overruns.
-   Add CI-friendly exit codes for verifier.

------------------------------------------------------------------------

END OF SPEC
