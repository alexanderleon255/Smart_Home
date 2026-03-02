# Conversation Log Retention Policy

**Version:** 1.0  
**Effective:** 2026-03-02

---

## Purpose

Raw conversation logs serve as:
1. Source material for dossier generation
2. Debugging resource for assistant behavior
3. Compliance record for security events

---

## Retention Periods

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Raw conversations | 30 days | Balance between utility and storage |
| Security events | 90 days | Compliance and incident investigation |
| Dossiers (preference) | Permanent | Core user knowledge |
| Dossiers (research) | 30-90 days | Time-sensitive information |
| Dossiers (device) | Permanent | Device-specific learnings |
| Dossiers (routine) | Rolling | Continuously updated |

---

## Storage Format

### Conversation Logs

```
CONVERSATION_LOG/
└── 2026-03/
    ├── 2026-03-01_session_001.json
    ├── 2026-03-01_session_002.json
    └── ...
```

Each session file:
```json
{
  "session_id": "2026-03-01_001",
  "start_time": "2026-03-01T07:30:00",
  "end_time": "2026-03-01T07:35:00",
  "user_id": "alex",
  "turns": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "dossiers_created": [],
  "tools_called": []
}
```

---

## Deletion Schedule

### Automated (Cron Job)

```bash
# Daily at 3 AM
# Delete conversation logs older than 30 days
find CONVERSATION_LOG -name "*.json" -mtime +30 -delete

# Delete expired research dossiers
python scripts/cleanup_expired_dossiers.py
```

### Manual Deletion

Users can request deletion via voice:
- "Forget our conversation from [date]"
- "Delete my search history about [topic]"
- "Forget everything about [X]"

**Note:** Security audit logs cannot be deleted via voice command.

---

## Privacy Guarantees

1. **Local only** - No conversation data leaves the local network
2. **User-deletable** - Most data can be deleted on request
3. **Transparent** - Users can ask "What do you remember about me?"
4. **Minimal** - Only store what's useful for future assistance

---

## Compliance Notes

- GDPR: Right to erasure supported (except security logs)
- CCPA: Consumer deletion requests honored
- Local law: Adjust retention periods as required

---

## Implementation

```python
# scripts/cleanup_expired_dossiers.py

def cleanup_expired():
    index = load_json("MEMORY/INDEX/dossier_index.json")
    today = datetime.now().date()
    
    for dossier in index["dossiers"]:
        if dossier["expires"]:
            expiry = datetime.fromisoformat(dossier["expires"]).date()
            if expiry < today:
                delete_file(dossier["path"])
                remove_from_index(dossier["id"])
    
    save_json("MEMORY/INDEX/dossier_index.json", index)
```
