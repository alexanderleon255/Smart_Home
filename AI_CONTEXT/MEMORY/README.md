# Smart Home Memory System

**Version:** 1.0  
**Updated:** 2026-03-02

---

## Overview

This directory contains the persistent memory system for the Smart Home LLM. It enables the assistant to:

- Remember user preferences across sessions
- Recall past research and conversations
- Learn device-specific quirks
- Detect and adapt to routines

---

## Architecture

```
MEMORY/
├── INDEX/
│   └── dossier_index.json      # Keyword → dossier lookup (RAG-lite)
│
├── DOSSIERS/                    # Persistent knowledge store
│   ├── PREFERENCES/             # User preferences (permanent)
│   ├── RESEARCH/                # Web search results (expires 30-90 days)
│   ├── DEVICES/                 # Device quirks and calibrations
│   └── ROUTINES/                # Detected behavioral patterns
│
├── CONVERSATION_LOG/            # Session archives
│   └── YYYY-MM/
│       └── YYYY-MM-DD_session.json
│
└── AUDIT_LOG/                   # Security-sensitive operations
    └── YYYY-MM-DD_audit.json
```

---

## Memory Types

### Dossiers (Structured Knowledge)

| Type | Location | Retention | Content |
|------|----------|-----------|---------|
| **Preference** | `DOSSIERS/PREFERENCES/` | Permanent | User likes/dislikes, corrections |
| **Research** | `DOSSIERS/RESEARCH/` | 30-90 days | Web search summaries |
| **Device** | `DOSSIERS/DEVICES/` | Permanent | Device quirks, calibrations |
| **Routine** | `DOSSIERS/ROUTINES/` | Updated weekly | Detected patterns |

### Conversation Log (Raw Archive)

- Full conversation transcripts
- 30-day retention (configurable)
- Used for: dossier generation, debugging, compliance

### Audit Log (Security)

- All lock/unlock operations
- Security arm/disarm
- Unusual patterns
- 90-day retention

---

## Dossier Format

Each dossier follows this structure:

```markdown
# Dossier: [Title]

**ID:** DXXX
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**Type:** preference | research | device | routine
**User:** alex | partner | shared
**Expires:** YYYY-MM-DD | null (permanent)

## Summary
[One paragraph summary]

## Details
[Structured content]

## Keywords
keyword1, keyword2, keyword3

## Related Entities
- entity_id_1
- entity_id_2
```

---

## Retrieval Flow

```python
def retrieve_dossiers(query: str, user_id: str) -> list[str]:
    """
    1. Tokenize query
    2. Match keywords against dossier_index.json
    3. Filter by user (include user-specific + shared)
    4. Filter out expired dossiers
    5. Return top matches within token budget
    """
```

---

## Dossier Lifecycle

### Creation Triggers

| Trigger | Example | Dossier Type |
|---------|---------|--------------|
| Explicit statement | "I prefer lights at 40%" | Preference |
| Correction | "No, warmer, not cooler" | Preference |
| Research + satisfaction | "Thanks, that's helpful" | Research |
| Troubleshooting success | "That fixed it!" | Device |
| Pattern detection | Same command 5+ times | Routine |

### Updates

- **Preferences:** Overwrite on contradiction, add on new info
- **Research:** Replace if re-searched, expire otherwise
- **Devices:** Append new findings
- **Routines:** Recalculate weekly

### Deletion

- **Research:** Auto-expire after TTL
- **Manual:** User can say "Forget that I..."
- **Compliance:** Audit logs retained per policy

---

## Privacy Considerations

1. **All data stays local** - No cloud sync
2. **User can request deletion** - "Forget everything about X"
3. **Audit logs are separate** - Security events can't be deleted by voice
4. **Encryption at rest** - Future enhancement

---

## Integration Points

### Tool Broker

```python
# memory_manager.py
retrieve_relevant_dossiers(query, user_id, max_tokens=4000)
create_dossier(type, content, user, keywords)
delete_dossier(dossier_id)
update_dossier_index()
```

### Context Builder

```python
# context_builder.py
def build_context():
    ...
    # Tier 3: Retrieved dossiers
    dossiers = retrieve_relevant_dossiers(user_query, user_id)
    context += "\n\n## Relevant Memories\n" + "\n\n".join(dossiers)
```

---

## Maintenance

### Daily
- Archive old conversation logs
- Update routine dossiers

### Weekly
- Recalculate routine patterns
- Clean expired research dossiers
- Rebuild dossier index

### Monthly
- Archive audit logs > 90 days
- Review memory usage
- Optimize index

---

## Token Budget

| Component | Typical Tokens |
|-----------|----------------|
| Single preference dossier | 100-200 |
| Research dossier | 150-300 |
| Device dossier | 100-200 |
| Routine dossier | 80-150 |
| **Max retrieved per query** | ~4000 |

With 4K token budget, typically 10-20 dossiers can be retrieved.
