# Smart Home — Chat Tier Pack Index

## Available Packs

| Pack | Purpose | Size | Mount Command |
|------|---------|------|---------------|
| `CHAT_T0_BOOT` | Instant alignment + guardrails | ~1000 tokens | Default (always active) |
| `CHAT_T1_CORE` | Stable architecture overview | ~3000 tokens | "Mount CHAT_T1_CORE" |
| `CHAT_T2_BUILD` | Implementation specs + contracts | ~8000 tokens | "Mount CHAT_T2_BUILD" |
| `CHAT_T3_DEEP` | Full corpus for deep analysis | ~30000 tokens | "Mount CHAT_T3_DEEP" |

## Quick Start

In a new ChatGPT thread:
> "Use CHAT_T0_BOOT and CHAT_T1_CORE as authoritative. We are working on [topic]."

## Regeneration

```bash
python generate_context_pack.py --chat
python verify_context_pack.py --chat
```

---

## Pack Manifest

| Pack | Tokens | SHA-256 (first 12) | Generated |
|------|--------|--------------------|-----------|
| `CHAT_T0_BOOT` | ~2951 | `b298a794ec17` | 2026-03-06 13:33 UTC |
| `CHAT_T1_CORE` | ~4567 | `df17ded93325` | 2026-03-06 13:33 UTC |
| `CHAT_T2_BUILD` | ~11789 | `f242956dca5e` | 2026-03-06 13:33 UTC |
| `CHAT_T3_DEEP` | ~39825 | `faf169adcc40` | 2026-03-06 13:33 UTC |


*Generated: 2026-03-06 13:33 UTC*