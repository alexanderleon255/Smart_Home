# Smart Home — Chat Operating Protocol

**Revision:** 1.0  
**Created:** 2026-03-06  
**Purpose:** Define how AI assistants should operate in ChatGPT threads using the Chat Tier Pack system.

---

## 1. Thread Startup

When Alex starts a new ChatGPT thread in the Smart Home project:

1. **Mount tiers explicitly.** Alex will say something like:  
   > "Use CHAT_T0_BOOT and CHAT_T1_CORE as authoritative. We are working on Phase X."
2. **Confirm invariants.** The assistant must respond with:
   - Confirmed non-negotiables (see §3)
   - Restated phase objective
   - 1–2 short clarifying questions if needed
3. **Do not assume outside the mounted packs.** If information isn't in a mounted tier, ask for it or request a tier escalation.

---

## 2. Tier Escalation

- **Default:** Most threads run on T0 + T1 only (< 4000 tokens of context).
- **Build mode:** Alex says "Mount CHAT_T2_BUILD" → implementation detail becomes available.
- **Deep mode:** Alex says "Mount CHAT_T3_DEEP" → full corpus for research/analysis.
- **Never auto-escalate.** The assistant must not mount deeper tiers unless explicitly told.

---

## 3. Non-Negotiables (Invariants)

These are locked decisions. Do not re-suggest alternatives:

| # | Constraint | Decided |
|---|-----------|---------|
| 1 | FOSS only — no proprietary cloud services for core functionality | 2026-03-02 |
| 2 | Home Assistant is the authoritative automation hub | 2026-03-02 |
| 3 | AirPods audio routes through iPhone (SonoBus → iPhone → AirPods) | 2026-03-04 |
| 4 | LLM scope: Llama 3.1:8b on Mac sidecar, qwen2.5:1.5b on Pi | 2026-03-03 |
| 5 | Claude does code (VS Code); ChatGPT does planning/analysis | 2026-03-02 |
| 6 | Raspberry Pi 5 runs Debian Bookworm (not HAOS) | 2026-03-03 |
| 7 | All secrets stay in env vars — never in code or LLM context | 2026-03-02 |
| 8 | Tool Broker is the only LLM→HA interface (no direct HA API from LLM) | 2026-03-02 |
| 9 | DEC-008 tool call format: `{"text": "...", "tool_calls": [...]}` | 2026-03-05 |
| 10 | ChromaDB for vector storage (DEC-007) | 2026-03-02 |

---

## 4. How to Handle Ambiguity

1. **Ask short clarifying questions** (max 2), then proceed.
2. **Never block on ambiguity** — pick the most reasonable default and state the assumption.
3. **If a decision seems locked already**, check the tier packs before asking.

---

## 5. Output Conventions

- **Downloadable markdown:** When producing specs, plans, or documents > 1 page, output as a downloadable `.md` file.
- **Code:** Offer code in fenced blocks. For multi-file changes, list files affected first.
- **Tables:** Use Markdown tables for structured data (decisions, comparisons, inventories).
- **Commit messages:** Format as `[Smart Home] Pn-XX: Description` when suggesting commits.

---

## 6. Heavy Thread Warning Rule

If a thread exceeds ~20 exchanges or becomes disorganized:
- The assistant should suggest: "This thread is getting heavy. Consider starting a fresh thread and mounting T0+T1."
- Creating a brief handoff summary for the new thread is encouraged.

---

## 7. What Alex Expects

- **Speed over perfection.** Ship working solutions; iterate later.
- **No hedging.** If you're confident, state it directly. If unsure, say so briefly and propose the best option.
- **Track against the roadmap.** All work should reference Pn-XX item IDs.
- **Security first.** Never suggest patterns that expose secrets, allow arbitrary shell access, or bypass the Tool Broker.

---

END OF CHAT OPERATING PROTOCOL
